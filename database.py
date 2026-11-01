import sqlite3
import os
import io
import csv
from datetime import datetime, timedelta
import random
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema with tables for telemetry, alerts, vehicle profile, and DTC codes."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Telemetry logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS telemetry_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        speed REAL NOT NULL,
        rpm REAL NOT NULL,
        engine_temp REAL NOT NULL,
        battery_voltage REAL NOT NULL,
        fuel_level REAL NOT NULL,
        engine_load REAL NOT NULL,
        throttle_pos REAL NOT NULL,
        fuel_pressure REAL NOT NULL,
        intake_temp REAL NOT NULL,
        anomaly_score REAL DEFAULT 0.0,
        is_anomaly INTEGER DEFAULT 0,
        health_status TEXT DEFAULT 'HEALTHY',
        anomaly_reason TEXT DEFAULT '',
        data_source TEXT DEFAULT 'SIMULATED'
    )
    ''')

    # 2. Maintenance Alerts table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maintenance_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        severity TEXT NOT NULL,  -- 'INFO', 'WARNING', 'CRITICAL'
        category TEXT NOT NULL,  -- 'COOLING', 'ELECTRICAL', 'POWERTRAIN', 'FUEL_SYSTEM'
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        recommended_action TEXT NOT NULL,
        dtc_code TEXT DEFAULT NULL,
        is_resolved INTEGER DEFAULT 0,
        resolved_at DATETIME DEFAULT NULL
    )
    ''')

    # 3. Vehicle Profile table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vehicle_profile (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        vin TEXT UNIQUE NOT NULL,
        make TEXT NOT NULL,
        model TEXT NOT NULL,
        year INTEGER NOT NULL,
        engine TEXT NOT NULL,
        odometer_km REAL NOT NULL,
        protocol TEXT NOT NULL,
        connection_type TEXT NOT NULL,
        status TEXT NOT NULL
    )
    ''')

    # 4. Standard OBD-II Diagnostic Trouble Codes (DTC) reference
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS dtc_reference (
        code TEXT PRIMARY KEY,
        system TEXT NOT NULL,
        description TEXT NOT NULL,
        severity TEXT NOT NULL,
        possible_causes TEXT NOT NULL,
        recommended_fix TEXT NOT NULL
    )
    ''')

    # Insert default vehicle profile if not exists
    cursor.execute('SELECT COUNT(*) FROM vehicle_profile')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO vehicle_profile (vin, make, model, year, engine, odometer_km, protocol, connection_type, status)
        VALUES ('1HGCR2F83HA029412', 'Apex Motors', 'CyberSentinel GT', 2024, '2.0L Turbocharged I4 DOHC', 34820.5, 'ISO 15765-4 (CAN 11-bit 500k)', 'OBD-II (ELM327 Virtual Stream)', 'ACTIVE')
        ''')

    # Insert standard DTC definitions
    cursor.execute('SELECT COUNT(*) FROM dtc_reference')
    if cursor.fetchone()[0] == 0:
        standard_dtcs = [
            ("P0117", "Engine Cooling", "Engine Coolant Temperature Sensor 1 Circuit Low", "CRITICAL", "Faulty ECT sensor, cooling system leak, stuck thermostat, wiring short.", "Inspect coolant level, test ECT sensor resistance, check for thermostat failure."),
            ("P0217", "Engine Cooling", "Engine Overtemperature Condition", "CRITICAL", "Low coolant, failing water pump, blocked radiator, stuck closed thermostat.", "Shut off engine immediately to prevent head gasket warp. Inspect coolant and radiator fans."),
            ("P0562", "Electrical System", "System Voltage Low", "WARNING", "Weak battery, failing alternator, loose serpentine belt, parasitic electrical draw.", "Test alternator charging output under load, test battery state of health, inspect belt tension."),
            ("P0563", "Electrical System", "System Voltage High", "WARNING", "Faulty voltage regulator on alternator, bad battery ground, sensor calibration error.", "Inspect alternator voltage regulator immediately to avoid frying ECUs."),
            ("P0300", "Powertrain / Ignition", "Random / Multiple Cylinder Misfire Detected", "CRITICAL", "Worn spark plugs, faulty ignition coils, low fuel pressure, vacuum leak.", "Replace spark plugs and ignition coils, test fuel pressure and intake manifold gasket."),
            ("P0171", "Fuel / Air Metering", "System Too Lean (Bank 1)", "WARNING", "Dirty Mass Air Flow (MAF) sensor, vacuum leak, weak fuel pump, clogged fuel injector.", "Clean MAF sensor with approved spray, inspect vacuum lines for dry rot, check fuel rail pressure."),
            ("P0420", "Emissions", "Catalyst System Efficiency Below Threshold (Bank 1)", "WARNING", "Degraded catalytic converter, faulty upstream/downstream O2 sensor, exhaust leak.", "Check upstream vs downstream O2 sensor waveforms, verify no exhaust leak before cat."),
            ("P0730", "Transmission", "Incorrect Gear Ratio / Transmission Slip", "CRITICAL", "Low transmission fluid, burnt transmission oil, failing shift solenoid, worn clutch pack.", "Inspect ATF fluid level and color, scan TCM codes, avoid high load driving.")
        ]
        cursor.executemany('''
        INSERT INTO dtc_reference (code, system, description, severity, possible_causes, recommended_fix)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', standard_dtcs)

    # Seed initial telemetry data if table is empty (to populate initial historical charts)
    cursor.execute('SELECT COUNT(*) FROM telemetry_logs')
    if cursor.fetchone()[0] == 0:
        seed_initial_telemetry(cursor)

    # Seed initial alerts if empty
    cursor.execute('SELECT COUNT(*) FROM maintenance_alerts')
    if cursor.fetchone()[0] == 0:
        initial_alerts = [
            ("WARNING", "COOLING", "Coolant Temperature Approaching Limit", "Engine coolant reached 97.5°C during high engine load. Operating within high-normal margin.", "Monitor cooling fan activation and radiator airflow.", "P0117", 0),
            ("INFO", "ELECTRICAL", "Battery State of Charge Optimal", "Battery alternator charging stable at 14.2V under auxiliary load.", "Routine check scheduled for next oil change.", None, 1)
        ]
        cursor.executemany('''
        INSERT INTO maintenance_alerts (severity, category, title, description, recommended_action, dtc_code, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', initial_alerts)

    conn.commit()
    conn.close()

def seed_initial_telemetry(cursor):
    """Creates a realistic 60-minute driving profile of healthy baseline data."""
    now = datetime.now()
    records = []
    
    speed = 0.0
    rpm = 800.0
    engine_temp = 72.0
    battery_voltage = 14.2
    fuel_level = 88.0
    engine_load = 22.0
    throttle_pos = 12.0
    fuel_pressure = 350.0
    intake_temp = 28.0

    # 60 sample points going back 60 minutes
    for i in range(60, 0, -1):
        ts = (now - timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S")
        
        # Simulate realistic driving pattern
        phase = (60 - i) % 20
        if phase < 5:  # Idling/stoplight
            speed = max(0.0, speed * 0.4)
            rpm = 750.0 + random.uniform(-30, 40)
            engine_load = 18.0 + random.uniform(-2, 3)
            throttle_pos = 5.0
        elif phase < 12:  # Cruising
            speed = min(95.0, max(50.0, speed + random.uniform(-3, 6)))
            rpm = 1800.0 + (speed * 18.0) + random.uniform(-60, 60)
            engine_load = 38.0 + random.uniform(-5, 8)
            throttle_pos = 28.0 + random.uniform(-3, 5)
        else:  # Acceleration / Highway
            speed = min(115.0, max(70.0, speed + random.uniform(-4, 5)))
            rpm = 2300.0 + (speed * 16.0) + random.uniform(-80, 80)
            engine_load = 52.0 + random.uniform(-6, 10)
            throttle_pos = 35.0 + random.uniform(-4, 6)

        if engine_temp < 89.0:
            engine_temp += random.uniform(0.2, 0.6)
        else:
            engine_temp = 89.5 + random.uniform(-1.5, 1.8)

        battery_voltage = 14.15 + random.uniform(-0.15, 0.25)
        fuel_level = max(10.0, fuel_level - 0.08)
        fuel_pressure = 350.0 + random.uniform(-15.0, 18.0)
        intake_temp = 30.0 + (speed * 0.05) + random.uniform(-1.0, 1.5)

        records.append((
            ts, round(speed, 1), round(rpm, 0), round(engine_temp, 1),
            round(battery_voltage, 2), round(fuel_level, 1), round(engine_load, 1),
            round(throttle_pos, 1), round(fuel_pressure, 1), round(intake_temp, 1),
            0.02, 0, 'HEALTHY', 'Normal telemetry baseline', 'SIMULATED'
        ))

    cursor.executemany('''
    INSERT INTO telemetry_logs (
        timestamp, speed, rpm, engine_temp, battery_voltage, fuel_level,
        engine_load, throttle_pos, fuel_pressure, intake_temp,
        anomaly_score, is_anomaly, health_status, anomaly_reason, data_source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)

def insert_telemetry(record):
    """Inserts a new vehicle telemetry point into database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO telemetry_logs (
        speed, rpm, engine_temp, battery_voltage, fuel_level,
        engine_load, throttle_pos, fuel_pressure, intake_temp,
        anomaly_score, is_anomaly, health_status, anomaly_reason, data_source
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        record.get("speed", 0.0),
        record.get("rpm", 0.0),
        record.get("engine_temp", 0.0),
        record.get("battery_voltage", 0.0),
        record.get("fuel_level", 0.0),
        record.get("engine_load", 0.0),
        record.get("throttle_pos", 0.0),
        record.get("fuel_pressure", 0.0),
        record.get("intake_temp", 0.0),
        record.get("anomaly_score", 0.0),
        record.get("is_anomaly", 0),
        record.get("health_status", "HEALTHY"),
        record.get("anomaly_reason", ""),
        record.get("data_source", "SIMULATED")
    ))
    record_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return record_id

def get_latest_telemetry():
    """Retrieves the single most recent telemetry log."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM telemetry_logs ORDER BY id DESC LIMIT 1
    ''')
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_recent_telemetry(limit=30):
    """Retrieves the recent N telemetry logs ordered chronologically for real-time charts."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM (
        SELECT * FROM telemetry_logs ORDER BY id DESC LIMIT ?
    ) ORDER BY id ASC
    ''', (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_telemetry_history(page=1, per_page=20, status_filter=None, anomaly_only=False):
    """Retrieves paginated telemetry records with optional status filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM telemetry_logs WHERE 1=1"
    params = []

    if status_filter and status_filter.upper() != 'ALL':
        query += " AND health_status = ?"
        params.append(status_filter.upper())
        
    if anomaly_only:
        query += " AND is_anomaly = 1"

    count_cursor = conn.cursor()
    count_query = query.replace("SELECT *", "SELECT COUNT(*)")
    count_cursor.execute(count_query, params)
    total_count = count_cursor.fetchone()[0]

    query += " ORDER BY id DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return {
        "records": [dict(r) for r in rows],
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": max(1, (total_count + per_page - 1) // per_page)
    }

def insert_alert(severity, category, title, description, recommended_action, dtc_code=None):
    """Inserts a predictive maintenance alert if an identical active alert is not already open."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Avoid duplicate active alerts within the last 15 minutes
    cursor.execute('''
    SELECT id FROM maintenance_alerts 
    WHERE title = ? AND is_resolved = 0
    ''', (title,))
    existing = cursor.fetchone()
    
    if not existing:
        cursor.execute('''
        INSERT INTO maintenance_alerts (severity, category, title, description, recommended_action, dtc_code, is_resolved)
        VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (severity, category, title, description, recommended_action, dtc_code))
        alert_id = cursor.lastrowid
        conn.commit()
    else:
        alert_id = existing[0]
        
    conn.close()
    return alert_id

def get_alerts(resolved=None, limit=50):
    """Returns alerts ordered by most recent."""
    conn = get_db_connection()
    cursor = conn.cursor()
    if resolved is None:
        cursor.execute('SELECT * FROM maintenance_alerts ORDER BY id DESC LIMIT ?', (limit,))
    else:
        cursor.execute('SELECT * FROM maintenance_alerts WHERE is_resolved = ? ORDER BY id DESC LIMIT ?', (1 if resolved else 0, limit))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def resolve_alert(alert_id):
    """Marks an alert as resolved."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('UPDATE maintenance_alerts SET is_resolved = 1, resolved_at = ? WHERE id = ?', (now_str, alert_id))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0

def get_vehicle_profile():
    """Returns vehicle profile info."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM vehicle_profile LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {}

def lookup_dtc(code):
    """Looks up a specific Diagnostic Trouble Code."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dtc_reference WHERE code = ?', (code.upper().strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_all_dtcs():
    """Returns all DTC definitions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM dtc_reference ORDER BY code ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def export_telemetry_csv():
    """Generates a CSV string containing all telemetry records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT id, timestamp, speed, rpm, engine_temp, battery_voltage, fuel_level,
           engine_load, throttle_pos, fuel_pressure, intake_temp,
           anomaly_score, is_anomaly, health_status, anomaly_reason, data_source
    FROM telemetry_logs ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Record ID", "Timestamp", "Speed (km/h)", "Engine RPM", "Coolant Temp (°C)",
        "Battery Voltage (V)", "Fuel Level (%)", "Engine Load (%)", "Throttle Position (%)",
        "Fuel Pressure (kPa)", "Intake Air Temp (°C)", "ML Anomaly Score", "Is Anomaly (0/1)",
        "Health Status", "Anomaly Diagnostic Reason", "Data Source"
    ])
    for r in rows:
        writer.writerow(list(r))
    return output.getvalue()
