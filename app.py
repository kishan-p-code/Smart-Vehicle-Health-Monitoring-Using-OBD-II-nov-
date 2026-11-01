import threading
import time
from flask import Flask, render_template, jsonify, request, Response
from config import Config
from database import (
    init_db, insert_telemetry, get_latest_telemetry,
    get_recent_telemetry, get_telemetry_history,
    get_alerts, resolve_alert, get_vehicle_profile,
    lookup_dtc, get_all_dtcs, export_telemetry_csv
)
from ml_engine import ml_engine
from obd_hardware import obd_manager
from obd_simulator import simulator

app = Flask(__name__)
app.config.from_object(Config)

# Telemetry background polling thread
_telemetry_thread = None
_thread_running = False
_latest_reading_cache = None

def telemetry_worker():
    """Background daemon thread continuously polling OBD-II source, running ML, and saving to SQLite."""
    global _latest_reading_cache, _thread_running
    while _thread_running:
        try:
            # 1. Read raw telemetry from OBD manager (hardware or simulation)
            raw = obd_manager.read_telemetry()
            
            # 2. Run Isolation Forest ML inference & automotive diagnostics in Python
            ml_result = ml_engine.analyze_reading(raw)
            
            # 3. Combine raw telemetry with ML assessment
            combined = {
                **raw,
                "anomaly_score": ml_result["anomaly_score"],
                "is_anomaly": ml_result["is_anomaly"],
                "health_status": ml_result["health_status"],
                "anomaly_reason": ml_result["anomaly_reason"],
                "z_scores": ml_result.get("z_scores", {}),
                "ml_decision_score": ml_result.get("ml_decision_score", 0.0)
            }
            
            # 4. Save to SQLite database
            record_id = insert_telemetry(combined)
            combined["id"] = record_id
            
            # 5. Update in-memory cache for ultra-fast API response
            _latest_reading_cache = combined
            
        except Exception as e:
            app.logger.error(f"Error in telemetry worker: {e}")
            
        time.sleep(Config.SIMULATION_INTERVAL)

def start_background_telemetry():
    global _telemetry_thread, _thread_running
    if _telemetry_thread is None or not _telemetry_thread.is_alive():
        _thread_running = True
        _telemetry_thread = threading.Thread(target=telemetry_worker, daemon=True)
        _telemetry_thread.start()

# --- Page Routes ---

@app.route("/")
def index():
    vehicle = get_vehicle_profile()
    return render_template("index.html", vehicle=vehicle, active_page="home")

@app.route("/dashboard")
def dashboard():
    vehicle = get_vehicle_profile()
    return render_template("dashboard.html", vehicle=vehicle, active_page="dashboard")

@app.route("/live-charts")
def live_charts():
    vehicle = get_vehicle_profile()
    return render_template("live_charts.html", vehicle=vehicle, active_page="charts")

@app.route("/predictive-maintenance")
def predictive_maintenance():
    vehicle = get_vehicle_profile()
    return render_template("ml_anomalies.html", vehicle=vehicle, active_page="maintenance")

@app.route("/reports")
def reports():
    vehicle = get_vehicle_profile()
    return render_template("reports.html", vehicle=vehicle, active_page="reports")

# --- REST APIs ---

@app.route("/api/telemetry/current", methods=["GET"])
def api_current_telemetry():
    """Returns the most up-to-date vehicle telemetry with ML anomaly analysis and health status."""
    global _latest_reading_cache
    if _latest_reading_cache is None:
        db_latest = get_latest_telemetry()
        if db_latest:
            return jsonify({"status": "success", "data": db_latest})
        # If DB is empty, run a single step
        raw = obd_manager.read_telemetry()
        ml_result = ml_engine.analyze_reading(raw)
        combined = {**raw, **ml_result}
        return jsonify({"status": "success", "data": combined})
    
    return jsonify({"status": "success", "data": _latest_reading_cache})

@app.route("/api/telemetry/history", methods=["GET"])
def api_telemetry_history():
    """Returns chronological telemetry series for live interactive charting."""
    limit = request.args.get("limit", default=30, type=int)
    limit = max(5, min(limit, 120))
    history = get_recent_telemetry(limit=limit)
    return jsonify({"status": "success", "data": history, "count": len(history)})

@app.route("/api/telemetry/records", methods=["GET"])
def api_telemetry_records():
    """Returns paginated telemetry logs with optional status filtering."""
    page = request.args.get("page", default=1, type=int)
    per_page = request.args.get("per_page", default=20, type=int)
    status_filter = request.args.get("status", default="ALL", type=str)
    anomaly_only = request.args.get("anomaly_only", default="false", type=str).lower() == "true"
    
    result = get_telemetry_history(
        page=page,
        per_page=per_page,
        status_filter=status_filter,
        anomaly_only=anomaly_only
    )
    return jsonify({"status": "success", **result})

@app.route("/api/telemetry/export-csv", methods=["GET"])
def api_export_csv():
    """Exports entire vehicle telemetry database as a downloadable CSV."""
    csv_data = export_telemetry_csv()
    filename = f"obd2_telemetry_export_{int(time.time())}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )

@app.route("/api/alerts", methods=["GET"])
def api_get_alerts():
    """Returns predictive maintenance alerts."""
    resolved_param = request.args.get("resolved", default=None)
    resolved = None
    if resolved_param is not None:
        resolved = resolved_param.lower() in ("true", "1")
    alerts = get_alerts(resolved=resolved, limit=50)
    return jsonify({"status": "success", "data": alerts})

@app.route("/api/alerts/<int:alert_id>/resolve", methods=["POST"])
def api_resolve_alert(alert_id):
    """Marks an alert as resolved."""
    success = resolve_alert(alert_id)
    return jsonify({"status": "success" if success else "error", "alert_id": alert_id})

@app.route("/api/simulator/fault", methods=["POST"])
def api_simulator_fault():
    """Injects an artificial fault into the simulator to test ML detection and alerts."""
    data = request.get_json() or {}
    fault_type = data.get("fault_type", "OVERHEAT")
    duration = data.get("duration", 60)
    result = simulator.set_fault(fault_type, duration_seconds=int(duration))
    return jsonify(result)

@app.route("/api/simulator/reset", methods=["POST"])
def api_simulator_reset():
    """Clears any active simulated faults and restores normal vehicle operation."""
    result = simulator.clear_fault()
    return jsonify(result)

@app.route("/api/system/status", methods=["GET"])
def api_system_status():
    """Returns connection and hardware status."""
    sys_status = obd_manager.get_system_status()
    vehicle = get_vehicle_profile()
    return jsonify({
        "status": "success",
        "system": sys_status,
        "vehicle": vehicle,
        "ml_engine": ml_engine.get_model_info()
    })

@app.route("/api/system/mode", methods=["POST"])
def api_set_system_mode():
    """Switches telemetry source between SIMULATED and HARDWARE."""
    data = request.get_json() or {}
    mode = data.get("mode", "SIMULATED").upper()
    result = obd_manager.set_mode(mode)
    return jsonify(result)

@app.route("/api/ml/status", methods=["GET"])
def api_ml_status():
    """Returns Isolation Forest model statistics and baseline parameters."""
    return jsonify({"status": "success", "data": ml_engine.get_model_info()})

@app.route("/api/ml/retrain", methods=["POST"])
def api_ml_retrain():
    """Retrains the Isolation Forest model on healthy telemetry."""
    success = ml_engine.train_and_save()
    return jsonify({"status": "success" if success else "error", "message": "Isolation Forest model retrained successfully."})

@app.route("/api/dtc/lookup", methods=["GET"])
def api_dtc_lookup():
    """Looks up Diagnostic Trouble Code definition and troubleshooting steps."""
    code = request.args.get("code", "")
    if code:
        match = lookup_dtc(code)
        if match:
            return jsonify({"status": "success", "data": match})
        return jsonify({"status": "not_found", "message": f"DTC code {code} not found in database."}), 404
    all_codes = get_all_dtcs()
    return jsonify({"status": "success", "data": all_codes})

_initialized = False
_init_lock = threading.Lock()

@app.before_request
def ensure_initialized():
    global _initialized
    if not _initialized:
        with _init_lock:
            if not _initialized:
                init_db()
                start_background_telemetry()
                _initialized = True

if __name__ == "__main__":
    init_db()
    start_background_telemetry()
    _initialized = True
    print("==================================================================")
    print("  SMART VEHICLE HEALTH MONITORING SYSTEM USING OBD-II & ML")
    print("  Server running at: http://127.0.0.1:5000")
    print("==================================================================")
    app.run(host="127.0.0.1", port=5000, debug=False)

