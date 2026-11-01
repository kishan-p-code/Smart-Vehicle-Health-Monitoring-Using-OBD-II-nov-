import os
import math
import pickle
import numpy as np
import pandas as pd
from config import Config
from database import insert_alert

# Helper for Isolation Forest BST Path Length Normalizer
def c_factor(n):
    if n <= 1:
        return 1.0
    if n == 2:
        return 1.0
    euler_mascheroni = 0.5772156649
    return 2.0 * (math.log(n - 1) + euler_mascheroni) - (2.0 * (n - 1) / n)

class IsolationTreeNode:
    def __init__(self, left=None, right=None, split_feature=None, split_value=None, size=0):
        self.left = left
        self.right = right
        self.split_feature = split_feature
        self.split_value = split_value
        self.size = size
        self.is_leaf = left is None and right is None

class IsolationTree:
    def __init__(self, max_depth):
        self.max_depth = max_depth
        self.root = None

    def fit(self, X):
        self.root = self._build_tree(X, 0)
        return self

    def _build_tree(self, X, current_depth):
        n_samples, n_features = X.shape
        if current_depth >= self.max_depth or n_samples <= 1:
            return IsolationTreeNode(size=n_samples)

        feat = np.random.randint(0, n_features)
        feat_vals = X[:, feat]
        val_min, val_max = float(feat_vals.min()), float(feat_vals.max())
        if val_min >= val_max:
            return IsolationTreeNode(size=n_samples)

        split_val = float(np.random.uniform(val_min, val_max))
        left_mask = feat_vals < split_val
        right_mask = ~left_mask

        if left_mask.sum() == 0 or right_mask.sum() == 0:
            return IsolationTreeNode(size=n_samples)

        left = self._build_tree(X[left_mask], current_depth + 1)
        right = self._build_tree(X[right_mask], current_depth + 1)
        return IsolationTreeNode(left=left, right=right, split_feature=feat, split_value=split_val, size=n_samples)

    def path_length(self, x, node, current_depth=0):
        if node.is_leaf:
            return current_depth + (c_factor(node.size) if node.size > 1 else 0)
        if x[node.split_feature] < node.split_value:
            return self.path_length(x, node.left, current_depth + 1)
        else:
            return self.path_length(x, node.right, current_depth + 1)

class RobustIsolationForest:
    """
    Production-grade Python/NumPy Isolation Forest Anomaly Detector.
    Matches the original algorithmic specification (Liu, Ting, Zhou - IEEE ICDM)
    while running smoothly across any operating system without C-extension DLL policy locks.
    """
    def __init__(self, n_estimators=100, max_samples=256, contamination=0.05, random_state=42):
        self.n_estimators = n_estimators
        self.max_samples = max_samples
        self.contamination = contamination
        self.random_state = random_state
        self.trees = []
        self.c_n = 1.0

    def fit(self, X):
        np.random.seed(self.random_state)
        n_samples = X.shape[0]
        subsample_size = min(self.max_samples, n_samples)
        self.c_n = c_factor(subsample_size)
        max_depth = int(math.ceil(math.log2(max(subsample_size, 2))))

        self.trees = []
        for _ in range(self.n_estimators):
            idx = np.random.choice(n_samples, size=subsample_size, replace=False)
            tree = IsolationTree(max_depth=max_depth)
            tree.fit(X[idx])
            self.trees.append(tree)
        return self

    def compute_anomaly_scores(self, X):
        """Computes isolation anomaly score between 0.0 (normal) and 1.0 (anomalous)."""
        scores = []
        for i in range(X.shape[0]):
            x = X[i]
            paths = [tree.path_length(x, tree.root) for tree in self.trees]
            avg_path = float(np.mean(paths))
            # Isolation Forest standard formula: s(x, n) = 2^(- E(h(x)) / c(n))
            score = 2.0 ** (- (avg_path / max(self.c_n, 1e-6)))
            scores.append(score)
        return np.array(scores)

    def predict(self, X):
        scores = self.compute_anomaly_scores(X)
        # Scores > 0.58 indicate high degree of isolation (anomaly)
        return np.where(scores > 0.58, -1, 1)

class VehicleMLEngine:
    def __init__(self):
        self.model = None
        self.baseline_stats = {}
        self.features = Config.ML_SETTINGS["features"]
        self.model_path = os.path.join(Config.MODEL_DIR, "isolation_forest.pkl")
        self.stats_path = os.path.join(Config.MODEL_DIR, "baseline_stats.pkl")
        os.makedirs(Config.MODEL_DIR, exist_ok=True)

    def _ensure_loaded(self):
        if self.model is None:
            if not self.load_model():
                self.train_and_save()

    def generate_synthetic_normal_data(self, n_samples=2500):
        """Generates realistic normal driving multi-parameter telemetry for training."""
        np.random.seed(Config.ML_SETTINGS["random_state"])

        speed = np.concatenate([
            np.zeros(200),                                      # Idle at stops
            np.random.uniform(15, 55, int(n_samples * 0.45)),    # City driving
            np.random.uniform(55, 95, int(n_samples * 0.35)),    # Arterial/Suburban
            np.random.uniform(95, 120, int(n_samples * 0.20) - 200) # Highway
        ])

        rpm = np.zeros_like(speed)
        for i, s in enumerate(speed):
            if s < 2.0:
                rpm[i] = np.random.normal(780, 25)
            elif s < 40:
                rpm[i] = 1000 + (s * 35) + np.random.normal(0, 80)
            elif s < 80:
                rpm[i] = 1500 + ((s - 40) * 25) + np.random.normal(0, 70)
            else:
                rpm[i] = 2100 + ((s - 80) * 20) + np.random.normal(0, 90)
        rpm = np.clip(rpm, 700, 4200)

        engine_load = 15 + (speed / 120) * 35 + (rpm / 4200) * 20 + np.random.normal(0, 5, n_samples)
        engine_load = np.clip(engine_load, 12, 75)

        throttle_pos = 5 + (speed / 120) * 40 + np.random.normal(0, 4, n_samples)
        throttle_pos = np.clip(throttle_pos, 4, 70)

        engine_temp = 89.0 + (engine_load / 100) * 6.0 + np.random.normal(0, 1.8, n_samples)
        engine_temp = np.clip(engine_temp, 82.0, 97.0)

        battery_voltage = 14.2 - (engine_load / 100) * 0.3 + np.random.normal(0, 0.12, n_samples)
        battery_voltage = np.clip(battery_voltage, 13.5, 14.6)

        fuel_level = np.random.uniform(22, 98, n_samples)
        fuel_pressure = 350.0 + (engine_load / 100) * 25.0 + np.random.normal(0, 12.0, n_samples)
        fuel_pressure = np.clip(fuel_pressure, 300, 395)

        intake_temp = 25.0 + (speed / 120) * 12.0 + np.random.normal(0, 2.5, n_samples)
        intake_temp = np.clip(intake_temp, 20.0, 52.0)

        data = {
            "speed": speed,
            "rpm": rpm,
            "engine_temp": engine_temp,
            "battery_voltage": battery_voltage,
            "fuel_level": fuel_level,
            "engine_load": engine_load,
            "throttle_pos": throttle_pos,
            "fuel_pressure": fuel_pressure,
            "intake_temp": intake_temp
        }
        return pd.DataFrame(data)

    def train_and_save(self):
        """Trains Isolation Forest model on baseline vehicle driving dynamics and saves model."""
        df = self.generate_synthetic_normal_data(n_samples=2000)
        X = df[self.features].values

        self.baseline_stats = {
            feat: {
                "mean": float(df[feat].mean()),
                "std": float(max(df[feat].std(), 0.001)),
                "min": float(df[feat].min()),
                "max": float(df[feat].max())
            }
            for feat in self.features
        }

        # Train Robust Isolation Forest
        self.model = RobustIsolationForest(
            n_estimators=Config.ML_SETTINGS["n_estimators"],
            contamination=Config.ML_SETTINGS["contamination"],
            random_state=Config.ML_SETTINGS["random_state"]
        )
        self.model.fit(X)

        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)
        with open(self.stats_path, "wb") as f:
            pickle.dump(self.baseline_stats, f)
        return True

    def load_model(self):
        """Loads trained Isolation Forest model."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.stats_path):
                with open(self.model_path, "rb") as f:
                    self.model = pickle.load(f)
                with open(self.stats_path, "rb") as f:
                    self.baseline_stats = pickle.load(f)
                return True
        except Exception:
            pass
        return False

    def analyze_reading(self, reading_dict):
        """
        Runs Isolation Forest inference and automotive diagnostics on a vehicle reading.
        """
        self._ensure_loaded()
        vector = [float(reading_dict.get(f, 0.0)) for f in self.features]
        vector_2d = np.array([vector])

        # Feature deviation standard scores (z-scores) relative to healthy baseline
        z_scores = {}
        for f in self.features:
            val = float(reading_dict.get(f, 0.0))
            stat = self.baseline_stats.get(f, {"mean": 0.0, "std": 1.0})
            z = (val - stat["mean"]) / stat["std"]
            z_scores[f] = round(float(z), 2)

        # Run Isolation Forest prediction
        raw_anomaly_score = float(self.model.compute_anomaly_scores(vector_2d)[0])
        is_ml_anomaly = raw_anomaly_score > 0.58

        critical_reasons = []
        warning_reasons = []
        alerts_to_insert = []

        temp = float(reading_dict.get("engine_temp", 90.0))
        volt = float(reading_dict.get("battery_voltage", 14.0))
        rpm = float(reading_dict.get("rpm", 800.0))
        fuel = float(reading_dict.get("fuel_level", 50.0))
        speed = float(reading_dict.get("speed", 0.0))
        pressure = float(reading_dict.get("fuel_pressure", 350.0))

        # 1. Engine Coolant Temperature Check
        if temp >= Config.THRESHOLDS["engine_temp"]["warning_max"]:
            critical_reasons.append(f"Engine Overheating ({temp:.1f}°C > 108°C)")
            alerts_to_insert.append({
                "severity": "CRITICAL",
                "category": "COOLING",
                "title": "Severe Engine Overheating Risk",
                "description": f"Engine coolant temperature reached {temp:.1f}°C, exceeding the 108°C critical safe threshold.",
                "recommended_action": "Safely pull over and turn off the engine. Inspect radiator coolant level, cooling fan, and water pump.",
                "dtc_code": "P0217"
            })
        elif temp >= Config.THRESHOLDS["engine_temp"]["normal_max"]:
            warning_reasons.append(f"High Coolant Temp ({temp:.1f}°C)")
            alerts_to_insert.append({
                "severity": "WARNING",
                "category": "COOLING",
                "title": "Elevated Coolant Temperature",
                "description": f"Coolant temperature ({temp:.1f}°C) is above normal cruising range (98°C).",
                "recommended_action": "Check radiator airflow and coolant expansion reservoir level.",
                "dtc_code": "P0117"
            })

        # 2. Battery & Charging System
        if volt <= Config.THRESHOLDS["battery_voltage"]["warning_min"]:
            critical_reasons.append(f"Critical Battery Voltage Dip ({volt:.2f}V < 11.9V)")
            alerts_to_insert.append({
                "severity": "CRITICAL",
                "category": "ELECTRICAL",
                "title": "Alternator Failure / Battery Under-Voltage",
                "description": f"Vehicle bus voltage dropped to {volt:.2f}V while running. Alternator is failing to charge battery.",
                "recommended_action": "Turn off auxiliary electronics (A/C, headlights, infotainment). Have alternator and battery tested immediately.",
                "dtc_code": "P0562"
            })
        elif volt < Config.THRESHOLDS["battery_voltage"]["normal_min"]:
            warning_reasons.append(f"Low System Voltage ({volt:.2f}V)")
        elif volt > 15.2:
            warning_reasons.append(f"Alternator Overcharging ({volt:.2f}V > 15.2V)")
            alerts_to_insert.append({
                "severity": "WARNING",
                "category": "ELECTRICAL",
                "title": "Alternator Voltage Regulator High",
                "description": f"System voltage ({volt:.2f}V) exceeds maximum 15.2V limit. Risk of sensor and battery damage.",
                "recommended_action": "Inspect alternator voltage regulator and battery ground strap.",
                "dtc_code": "P0563"
            })

        # 3. RPM & Transmission Dynamics
        if rpm > Config.THRESHOLDS["rpm"]["warning_max"]:
            critical_reasons.append(f"Engine RPM Redline Hazard ({rpm:.0f} RPM)")
            alerts_to_insert.append({
                "severity": "CRITICAL",
                "category": "POWERTRAIN",
                "title": "Engine Overspeed / Redline Breach",
                "description": f"Engine speed reached {rpm:.0f} RPM exceeding 5800 RPM safe operating redline.",
                "recommended_action": "Upshift immediately or decelerate to prevent valve float and piston damage.",
                "dtc_code": "P0300"
            })
        elif speed < 15.0 and rpm > 3200.0:
            warning_reasons.append(f"Transmission Slip / High RPM at low speed ({rpm:.0f} RPM @ {speed:.1f} km/h)")
            alerts_to_insert.append({
                "severity": "WARNING",
                "category": "POWERTRAIN",
                "title": "Possible Transmission Slip Detected",
                "description": f"Engine RPM is high ({rpm:.0f} RPM) while vehicle road speed is only {speed:.1f} km/h.",
                "recommended_action": "Check Automatic Transmission Fluid (ATF) level, clutch engagement, and TCM error codes.",
                "dtc_code": "P0730"
            })

        # 4. Fuel System
        if pressure < 220.0:
            critical_reasons.append(f"Severe Fuel Rail Pressure Loss ({pressure:.1f} kPa < 220 kPa)")
            alerts_to_insert.append({
                "severity": "CRITICAL",
                "category": "FUEL_SYSTEM",
                "title": "Fuel Rail Pressure Loss",
                "description": f"Fuel pressure dropped to {pressure:.1f} kPa (normal: 300-380 kPa). Risk of cylinder lean condition.",
                "recommended_action": "Inspect high-pressure fuel pump, fuel filter, and pressure regulator.",
                "dtc_code": "P0171"
            })
        elif fuel <= Config.THRESHOLDS["fuel_level"]["critical_min"]:
            warning_reasons.append(f"Fuel Reserve Depleted ({fuel:.1f}%)")
            alerts_to_insert.append({
                "severity": "WARNING",
                "category": "FUEL_SYSTEM",
                "title": "Low Fuel Reserve Warning",
                "description": f"Remaining fuel level is {fuel:.1f}%. Refueling needed to prevent fuel pump overheating.",
                "recommended_action": "Refuel vehicle at the nearest station.",
                "dtc_code": None
            })

        # Final health classification
        if critical_reasons:
            health_status = "CRITICAL"
            primary_reason = " | ".join(critical_reasons)
            is_anomaly = 1
            final_anomaly_score = max(raw_anomaly_score, 0.88)
        elif warning_reasons:
            health_status = "WARNING"
            primary_reason = " | ".join(warning_reasons)
            is_anomaly = 1
            final_anomaly_score = max(raw_anomaly_score, 0.65)
        elif is_ml_anomaly:
            health_status = "WARNING"
            top_feature = max(z_scores.items(), key=lambda x: abs(x[1]))
            primary_reason = f"ML Isolation Forest detected abnormal reading pattern in {top_feature[0]} (z={top_feature[1]:+.1f}σ)"
            is_anomaly = 1
            final_anomaly_score = raw_anomaly_score
            alerts_to_insert.append({
                "severity": "WARNING",
                "category": "ANOMALY_DETECTION",
                "title": f"Telemetry Anomaly: {top_feature[0].replace('_', ' ').title()}",
                "description": f"Isolation Forest identified an unusual statistical divergence ({top_feature[0]}: {reading_dict.get(top_feature[0])}).",
                "recommended_action": "Perform full OBD-II scan and inspect sensor telemetry history.",
                "dtc_code": None
            })
        else:
            health_status = "HEALTHY"
            primary_reason = "All OBD-II telemetry parameters within optimal operating envelope"
            is_anomaly = 0
            final_anomaly_score = min(raw_anomaly_score, 0.35)

        for alert in alerts_to_insert:
            insert_alert(
                severity=alert["severity"],
                category=alert["category"],
                title=alert["title"],
                description=alert["description"],
                recommended_action=alert["recommended_action"],
                dtc_code=alert["dtc_code"]
            )

        return {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(final_anomaly_score), 3),
            "health_status": health_status,
            "anomaly_reason": primary_reason,
            "z_scores": z_scores,
            "ml_decision_score": round(float(raw_anomaly_score), 4)
        }

    def get_model_info(self):
        """Returns metadata about the active ML model."""
        self._ensure_loaded()
        return {
            "algorithm": "Isolation Forest (Ensemble Tree Anomaly Detector)",
            "n_estimators": Config.ML_SETTINGS["n_estimators"],
            "contamination_rate": Config.ML_SETTINGS["contamination"],
            "features_monitored": self.features,
            "is_trained": self.model is not None,
            "baseline_stats": self.baseline_stats
        }

# Global singleton
ml_engine = VehicleMLEngine()
