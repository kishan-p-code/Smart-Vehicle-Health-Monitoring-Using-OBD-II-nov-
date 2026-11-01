import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-obd2-vehicle-health-monitor-key-2026")
    DATABASE_PATH = os.path.join(BASE_DIR, "vehicle_health.db")
    MODEL_DIR = os.path.join(BASE_DIR, "ml_models")
    MODEL_PATH = os.path.join(MODEL_DIR, "isolation_forest_model.joblib")
    
    # Telemetry Normal Operating Thresholds
    THRESHOLDS = {
        "engine_temp": {"normal_max": 98.0, "warning_max": 108.0, "unit": "°C"},
        "battery_voltage": {"normal_min": 13.2, "normal_max": 14.8, "warning_min": 11.9, "unit": "V"},
        "rpm": {"idle": 750, "normal_max": 4200, "warning_max": 5800, "redline": 6800, "unit": "RPM"},
        "fuel_level": {"warning_min": 18.0, "critical_min": 8.0, "unit": "%"},
        "speed": {"normal_max": 120, "warning_max": 150, "unit": "km/h"},
        "engine_load": {"normal_max": 75.0, "warning_max": 90.0, "unit": "%"},
        "throttle_pos": {"normal_max": 85.0, "warning_max": 95.0, "unit": "%"},
        "intake_temp": {"normal_max": 60.0, "warning_max": 75.0, "unit": "°C"},
        "fuel_pressure": {"normal_min": 250.0, "normal_max": 420.0, "unit": "kPa"}
    }
    
    # Machine Learning Isolation Forest Parameters
    ML_SETTINGS = {
        "n_estimators": 100,
        "contamination": 0.05,  # Expected 5% anomalous operating conditions
        "random_state": 42,
        "features": [
            "speed",
            "rpm",
            "engine_temp",
            "battery_voltage",
            "fuel_level",
            "engine_load",
            "throttle_pos",
            "fuel_pressure",
            "intake_temp"
        ]
    }
    
    # Simulation Settings
    SIMULATION_INTERVAL = 1.0  # seconds between sensor readings
