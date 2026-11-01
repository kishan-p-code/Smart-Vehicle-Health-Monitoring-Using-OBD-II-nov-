import math
import random
import os
import csv
import time
from datetime import datetime

class OBDSimulator:
    def __init__(self):
        # Initial normal state
        self.speed = 0.0
        self.rpm = 780.0
        self.engine_temp = 88.5
        self.battery_voltage = 14.22
        self.fuel_level = 76.4
        self.engine_load = 22.0
        self.throttle_pos = 12.0
        self.fuel_pressure = 350.0
        self.intake_temp = 32.0
        
        # Drive cycle state machine
        self.mode = "CRUISE"  # "IDLE", "ACCEL", "CRUISE", "DECEL"
        self.step_count = 0
        self.target_speed = 65.0
        
        # Real dataset replay cache
        self.dataset_records = self._load_dataset_telematics()
        self.dataset_index = 0
        
        # Fault injection state
        self.active_fault = None
        self.fault_duration_remaining = 0
        self.is_running = True

    def _load_dataset_telematics(self):
        """Loads recorded real-vehicle OBD-II drive cycle from Dataset/Vehicle_Telematics.csv if present."""
        records = []
        path = os.path.join(os.path.dirname(__file__), "Dataset", "Vehicle_Telematics.csv")
        if os.path.exists(path):
            try:
                with open(path, mode="r", encoding="utf-8", errors="ignore") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        def parse_num(v, default):
                            if not v or v.strip() == "":
                                return default
                            return float(v.replace(",", ".").strip())

                        speed_val = parse_num(row.get("SPEED"), None)
                        rpm_val = parse_num(row.get("ENGINE_RPM"), None)
                        if speed_val is not None and rpm_val is not None and rpm_val > 0:
                            temp_val = parse_num(row.get("ENGINE_COOLANT_TEMP"), 89.0)
                            fuel_val = parse_num(row.get("FUEL_LEVEL"), 75.0)
                            load_val = parse_num(row.get("ENGINE_LOAD"), 25.0)
                            throttle_val = parse_num(row.get("THROTTLE_POS"), 15.0)
                            intake_val = parse_num(row.get("AIR_INTAKE_TEMP"), 32.0)
                            records.append({
                                "speed": speed_val,
                                "rpm": rpm_val,
                                "engine_temp": temp_val,
                                "fuel_level": fuel_val,
                                "engine_load": load_val,
                                "throttle_pos": throttle_val,
                                "intake_temp": intake_val,
                                "battery_voltage": round(14.22 - (load_val / 100.0) * 0.25, 2),
                                "fuel_pressure": round(350.0 + (load_val / 100.0) * 20.0, 1)
                            })
            except Exception:
                pass
        return records


    def set_fault(self, fault_type, duration_seconds=60):
        """
        Injects a synthetic fault for testing predictive maintenance alerts and ML anomaly detection.
        Supported faults: 'OVERHEAT', 'BATTERY_FAIL', 'MISFIRE', 'LOW_FUEL', 'FUEL_PRESSURE_DROP', 'TRANSMISSION_SLIP'
        """
        self.active_fault = fault_type.upper()
        self.fault_duration_remaining = duration_seconds
        return {
            "status": "success",
            "message": f"Fault '{self.active_fault}' injected successfully for {duration_seconds} seconds.",
            "active_fault": self.active_fault
        }

    def clear_fault(self):
        """Clears active fault and returns telemetry to normal envelope."""
        fault_cleared = self.active_fault
        self.active_fault = None
        self.fault_duration_remaining = 0
        
        # Smoothly reset abnormal readings
        self.engine_temp = 89.0
        self.battery_voltage = 14.2
        self.fuel_pressure = 350.0
        self.rpm = 800.0 if self.speed < 5.0 else 2200.0
        
        return {
            "status": "success",
            "message": f"Fault '{fault_cleared}' cleared. Resumed normal driving profile.",
            "active_fault": None
        }

    def step(self):
        """Advances the simulation state by 1 step (1 second) and returns all sensor values."""
        self.step_count += 1
        
        # Count down fault duration if active
        if self.active_fault:
            if self.fault_duration_remaining > 0:
                self.fault_duration_remaining -= 1
            else:
                self.active_fault = None

        # 1. Drive cycle telemetry
        if not self.active_fault:
            if self.dataset_records and len(self.dataset_records) > 0:
                rec = self.dataset_records[self.dataset_index % len(self.dataset_records)]
                self.dataset_index += 1
                self.speed = rec["speed"]
                self.rpm = rec["rpm"]
                self.engine_temp = rec["engine_temp"]
                self.battery_voltage = rec["battery_voltage"]
                self.fuel_level = rec["fuel_level"]
                self.engine_load = rec["engine_load"]
                self.throttle_pos = rec["throttle_pos"]
                self.fuel_pressure = rec["fuel_pressure"]
                self.intake_temp = rec["intake_temp"]
            else:
                if self.step_count % 35 == 0:
                    # Transition drive mode
                    modes = ["IDLE", "ACCEL", "CRUISE", "DECEL"]
                    self.mode = random.choice(modes)
                    if self.mode == "CRUISE":
                        self.target_speed = random.uniform(50.0, 95.0)
                    elif self.mode == "ACCEL":
                        self.target_speed = random.uniform(80.0, 115.0)
                    elif self.mode == "DECEL":
                        self.target_speed = random.uniform(15.0, 40.0)
                    elif self.mode == "IDLE":
                        self.target_speed = 0.0

                # Drive cycle velocity adjustment
                if self.speed < self.target_speed:
                    self.speed = min(self.target_speed, self.speed + random.uniform(1.5, 3.5))
                    self.engine_load = min(75.0, 35.0 + (self.speed / 120.0) * 35.0 + random.uniform(-2, 4))
                    self.throttle_pos = min(70.0, 20.0 + (self.speed / 120.0) * 45.0 + random.uniform(-2, 3))
                elif self.speed > self.target_speed:
                    self.speed = max(self.target_speed, self.speed - random.uniform(1.8, 3.8))
                    self.engine_load = max(14.0, 20.0 + random.uniform(-3, 2))
                    self.throttle_pos = max(5.0, 8.0 + random.uniform(-2, 2))
                else:
                    self.speed += random.uniform(-0.8, 0.8)
                    self.speed = max(0.0, min(130.0, self.speed))
                    self.engine_load = 28.0 + (self.speed / 120.0) * 20.0 + random.uniform(-2, 2)
                    self.throttle_pos = 15.0 + (self.speed / 120.0) * 25.0 + random.uniform(-1, 2)

                # RPM calculation based on speed and simulated transmission gear ratios
                if self.speed < 2.0:
                    self.rpm = 780.0 + random.uniform(-20, 25)
                elif self.speed < 30.0:
                    self.rpm = 1000.0 + (self.speed * 45.0) + random.uniform(-40, 40)
                elif self.speed < 65.0:
                    self.rpm = 1400.0 + ((self.speed - 30.0) * 28.0) + random.uniform(-30, 30)
                else:
                    self.rpm = 1900.0 + ((self.speed - 65.0) * 22.0) + random.uniform(-25, 25)

                target_temp = 90.0 + (self.engine_load / 100.0) * 3.5
                self.engine_temp += (target_temp - self.engine_temp) * 0.08 + random.uniform(-0.15, 0.15)
                self.engine_temp = max(80.0, min(96.0, self.engine_temp))

                self.battery_voltage = 14.22 - (self.engine_load / 100.0) * 0.25 + random.uniform(-0.06, 0.06)
                self.fuel_pressure = 350.0 + (self.engine_load / 100.0) * 20.0 + random.uniform(-5, 5)
                self.intake_temp = 28.0 + (self.speed / 120.0) * 10.0 + random.uniform(-0.5, 0.5)


        # 2. Inject Fault Override (if active)
        if self.active_fault == "OVERHEAT":
            # Ramp temperature to critical levels (109°C - 116°C)
            self.engine_temp = min(116.5, self.engine_temp + random.uniform(0.8, 1.8))
            self.engine_load = min(92.0, self.engine_load + 5.0)

        elif self.active_fault == "BATTERY_FAIL":
            # Alternator failure - voltage drops below 11.8V
            self.battery_voltage = max(11.1, self.battery_voltage - random.uniform(0.18, 0.42))

        elif self.active_fault == "MISFIRE":
            # Erratic RPM spikes and drops, load jitter
            self.rpm = 3400.0 + math.sin(self.step_count * 1.5) * 1600.0 + random.uniform(-350, 450)
            self.rpm = max(800.0, min(6200.0, self.rpm))
            self.engine_load = 65.0 + random.uniform(-20, 25)

        elif self.active_fault == "LOW_FUEL":
            # Low fuel reserve condition
            self.fuel_level = max(4.5, self.fuel_level - 0.2)

        elif self.active_fault == "FUEL_PRESSURE_DROP":
            # Fuel pump cavitation / pressure loss
            self.fuel_pressure = max(165.0, self.fuel_pressure - random.uniform(8.0, 16.0))
            self.engine_load = min(88.0, self.engine_load + random.uniform(4, 9))

        elif self.active_fault == "TRANSMISSION_SLIP":
            # High engine RPM while vehicle road speed drops
            self.speed = max(8.0, self.speed * 0.94)
            self.rpm = min(5400.0, self.rpm + random.uniform(150, 350))
            self.engine_load = min(85.0, self.engine_load + 4.0)

        # Standard fuel consumption (tiny fraction per step)
        self.fuel_level = max(0.0, self.fuel_level - (self.rpm / 6000.0) * 0.003)

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "speed": round(float(self.speed), 1),
            "rpm": round(float(self.rpm), 0),
            "engine_temp": round(float(self.engine_temp), 1),
            "battery_voltage": round(float(self.battery_voltage), 2),
            "fuel_level": round(float(self.fuel_level), 1),
            "engine_load": round(float(self.engine_load), 1),
            "throttle_pos": round(float(self.throttle_pos), 1),
            "fuel_pressure": round(float(self.fuel_pressure), 1),
            "intake_temp": round(float(self.intake_temp), 1),
            "active_fault": self.active_fault,
            "data_source": "SIMULATED"
        }

# Global simulator instance
simulator = OBDSimulator()
