import logging
from obd_simulator import simulator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("OBDHardware")

class BaseOBDAdapter:
    def connect(self):
        raise NotImplementedError
    def disconnect(self):
        raise NotImplementedError
    def get_telemetry(self):
        raise NotImplementedError
    def get_status(self):
        raise NotImplementedError

class SimulatedOBDAdapter(BaseOBDAdapter):
    """Adapter that reads high-fidelity vehicle telemetry from the software simulator."""
    def __init__(self):
        self.connected = True
        self.name = "ELM327 Virtual CAN Bus (Simulator)"

    def connect(self):
        self.connected = True
        return True

    def disconnect(self):
        self.connected = False
        return True

    def get_telemetry(self):
        return simulator.step()

    def get_status(self):
        return {
            "is_connected": True,
            "mode": "SIMULATED",
            "adapter_type": "High-Fidelity Virtual OBD-II Engine",
            "protocol": "ISO 15765-4 (CAN 11-bit 500k Virtual)",
            "port": "Virtual-CAN-0",
            "active_fault": simulator.active_fault,
            "description": "Simulated realistic telemetry stream for demo, testing, and ML evaluation."
        }

class HardwareOBDAdapter(BaseOBDAdapter):
    """
    Adapter designed to interface directly with real physical ELM327 OBD-II hardware
    via USB, Bluetooth COM port, or WiFi socket.
    """
    def __init__(self, port=None, baudrate=38400):
        self.port = port
        self.baudrate = baudrate
        self.connection = None
        self.connected = False
        self.name = "Physical ELM327 OBD-II Adapter"

    def connect(self):
        """Attempts connection to real OBD-II hardware using python-obd if available."""
        try:
            import obd
            if self.port:
                self.connection = obd.OBD(self.port, baudrate=self.baudrate)
            else:
                self.connection = obd.OBD()  # Auto-scan serial/bluetooth ports

            if self.connection.is_connected():
                self.connected = True
                logger.info(f"Connected to physical OBD-II vehicle on port {self.connection.port_name()}")
                return True
            else:
                self.connected = False
                logger.warning("No physical OBD-II dongle detected on scanning ports.")
                return False
        except ImportError:
            logger.info("python-obd library not installed. Ready for installation when hardware is plugged.")
            self.connected = False
            return False
        except Exception as e:
            logger.error(f"Error connecting to OBD hardware: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.connection:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connected = False
        return True

    def get_telemetry(self):
        """Queries physical vehicle PIDs via ELM327."""
        if not self.connected or not self.connection:
            return None

        import obd
        try:
            cmd_speed = self.connection.query(obd.commands.SPEED)
            cmd_rpm = self.connection.query(obd.commands.RPM)
            cmd_temp = self.connection.query(obd.commands.COOLANT_TEMP)
            cmd_volt = self.connection.query(obd.commands.CONTROL_MODULE_VOLTAGE)
            cmd_fuel = self.connection.query(obd.commands.FUEL_LEVEL)
            cmd_load = self.connection.query(obd.commands.ENGINE_LOAD)
            cmd_throttle = self.connection.query(obd.commands.THROTTLE_POS)
            cmd_pressure = self.connection.query(obd.commands.FUEL_PRESSURE)
            cmd_intake = self.connection.query(obd.commands.INTAKE_TEMP)

            return {
                "speed": float(cmd_speed.value.magnitude) if cmd_speed.value else 0.0,
                "rpm": float(cmd_rpm.value.magnitude) if cmd_rpm.value else 0.0,
                "engine_temp": float(cmd_temp.value.magnitude) if cmd_temp.value else 85.0,
                "battery_voltage": float(cmd_volt.value.magnitude) if cmd_volt.value else 13.8,
                "fuel_level": float(cmd_fuel.value.magnitude) if cmd_fuel.value else 50.0,
                "engine_load": float(cmd_load.value.magnitude) if cmd_load.value else 25.0,
                "throttle_pos": float(cmd_throttle.value.magnitude) if cmd_throttle.value else 15.0,
                "fuel_pressure": float(cmd_pressure.value.magnitude) if cmd_pressure.value else 350.0,
                "intake_temp": float(cmd_intake.value.magnitude) if cmd_intake.value else 30.0,
                "data_source": "HARDWARE_OBD"
            }
        except Exception as e:
            logger.error(f"Failed to query OBD PIDs: {e}")
            return None

    def get_status(self):
        return {
            "is_connected": self.connected,
            "mode": "HARDWARE" if self.connected else "HARDWARE_UNAVAILABLE",
            "adapter_type": "ELM327 Physical OBD-II Dongle",
            "protocol": self.connection.protocol_name() if self.connected and self.connection else "N/A",
            "port": self.connection.port_name() if self.connected and self.connection else "COM Port Disconnected",
            "description": "Physical vehicle connection via ELM327 interface."
        }

class OBDManager:
    """Central gateway routing queries to either physical hardware or high-fidelity simulation."""
    def __init__(self):
        self.simulated_adapter = SimulatedOBDAdapter()
        self.hardware_adapter = HardwareOBDAdapter()
        self.mode = "SIMULATED"  # Default to SIMULATED

    def set_mode(self, mode):
        if mode == "HARDWARE":
            if self.hardware_adapter.connect():
                self.mode = "HARDWARE"
                return {"success": True, "mode": "HARDWARE", "message": "Connected to physical OBD-II hardware."}
            else:
                self.mode = "SIMULATED"
                return {
                    "success": False,
                    "mode": "SIMULATED",
                    "message": "Physical OBD-II dongle not found. Reverted to Simulated Stream."
                }
        else:
            self.mode = "SIMULATED"
            return {"success": True, "mode": "SIMULATED", "message": "Active data source: Simulated OBD-II stream."}

    def read_telemetry(self):
        if self.mode == "HARDWARE":
            reading = self.hardware_adapter.get_telemetry()
            if reading is not None:
                return reading
        # Fallback / default to simulation
        return self.simulated_adapter.get_telemetry()

    def get_system_status(self):
        adapter = self.hardware_adapter if self.mode == "HARDWARE" else self.simulated_adapter
        status = adapter.get_status()
        status["active_mode"] = self.mode
        return status

obd_manager = OBDManager()
