# Smart Vehicle Health Monitoring System Using OBD-II & Machine Learning

A modern, responsive, automotive-grade web application and predictive diagnostic platform built with **Python Flask**, **SQLite**, **NumPy & Scikit-learn (Isolation Forest Algorithm)**, and vanilla **HTML5, CSS3, and JavaScript**.

---

## 🌟 Key Features

1. **Modern Automotive Cockpit UI**:
   - Dark navy theme (`#070b14` / `#0c1427`) with electric cyan (`#00d2ff`) and cobalt blue accents.
   - Glassmorphism elevation cards, glowing status badges, responsive mobile/tablet/desktop layout.
2. **Real-Time Telemetry & SVG Cockpit Gauges**:
   - Speedometer (0 - 200 km/h) with dynamic SVG arc, rotating glowing needle, and simulated transmission gear state.
   - Tachometer / Engine RPM Gauge (0 - 8,000 RPM) with high-RPM redline warning zones.
   - 5 Dynamic Sensor Cards with animated level meters: Coolant Temp (°C), Battery Voltage (V), Fuel Level (%), Engine Load & Throttle (%), and Fuel Rail Pressure & Intake Air Temp.
3. **Vehicle Health Status Classification**:
   - Live Tri-State Health Indicator: **HEALTHY** (Emerald), **WARNING** (Amber), or **CRITICAL** (Pulsing Crimson).
   - Real-time diagnostic root-cause explanation engine.
4. **Machine Learning Anomaly Detection (Isolation Forest)**:
   - High-dimensional unsupervised outlier detection running strictly in the **Python backend**.
   - Monitors 9 vehicle parameters: `[speed, rpm, engine_temp, battery_voltage, fuel_level, engine_load, throttle_pos, fuel_pressure, intake_temp]`.
   - Computes normalized anomaly risk confidence (0.0% to 100%).
   - Multi-sensor Z-score divergence matrix pinpointing the exact failing sensor component.
5. **Predictive Maintenance Alerts**:
   - Proactive failure detection mapped to official SAE J2012 Diagnostic Trouble Codes (DTCs):
     - `P0217`: Engine Overtemperature Condition
     - `P0117`: Engine Coolant Temperature Low Circuit
     - `P0562`: System Voltage Low (Alternator failure)
     - `P0563`: System Voltage High (Alternator overcharging)
     - `P0300`: Random / Multiple Cylinder Misfire Detected
     - `P0171`: System Too Lean (Fuel pressure drop)
     - `P0730`: Incorrect Gear Ratio / Transmission Slip
   - Interactive alert resolution buttons with persistent status in SQLite.
6. **Live Interactive Charts**:
   - Powered by Chart.js with dark cockpit theme:
     - Dual-axis Speed (km/h) vs Engine RPM
     - Coolant Temperature with safety threshold lines (98°C and 108°C)
     - Battery Voltage & Alternator stability
     - Fuel Level (%) vs Engine Load (%)
     - Machine Learning Anomaly Score time-series
   - Streaming controls: Pause / Resume, Window buffer size selector (20, 40, 60 points), and buffer clear.
7. **Vehicle History Reports & CSV Export**:
   - Paginated historical logbook with status filtering (All, Healthy, Warning, Critical) and anomaly-only filter.
   - One-click full database export to downloadable CSV format (`/api/telemetry/export-csv`).
   - Built-in OBD-II Diagnostic Trouble Code master reference table.
8. **Interactive OBD-II Fault Injector**:
   - In-app evaluation panel to inject simulated real-world faults:
     - 🔥 Engine Overheating (>114°C)
     - ⚡ Alternator Battery Drain (<11.4V)
     - ⚙️ Cylinder Misfire (Erratic RPM spike)
     - ⛽ Fuel Rail Pressure Loss
     - ⚠️ Transmission Slip
     - 🟢 Restore Normal Drive Cycle
9. **Hardware-Ready Architecture**:
   - Modular Hardware Abstraction Layer (`obd_hardware.py`) with support for real physical **ELM327 USB / Bluetooth** OBD-II dongles.
   - Seamless auto-fallback to high-fidelity virtual CAN-bus simulator when physical hardware is not plugged in.
   - Prominent indicator badge clearly labeling simulated data streams.

---

## 📁 Project Folder Structure

```text
Smart Vehicle Health Monitoring Using OBD-II/
│
├── app.py                      # Flask Application entry point, routing & REST APIs
├── config.py                   # Central configuration (DB path, thresholds, ML parameters)
├── database.py                 # SQLite database models, initialization, seed data, queries
├── ml_engine.py                # Isolation Forest model training, Z-score divergence, inference
├── obd_simulator.py            # High-fidelity OBD-II telemetry simulator with fault injection
├── obd_hardware.py             # Hardware abstraction layer (Real ELM327 vs Simulated stream)
├── requirements.txt            # Python dependencies
├── README.md                   # Comprehensive documentation & setup guide
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern dark navy automotive design system & responsive layout
│   └── js/
│       ├── main.js             # Global navigation, toasts, modal controllers, header polling
│       ├── dashboard.js        # SVG cockpit gauges, needles, dynamic meters, alerts preview
│       ├── charts.js           # Real-time multi-metric Chart.js telemetry time-series streaming
│       ├── ml_monitor.js       # Isolation Forest anomaly meter, Z-scores, alert resolution
│       └── reports.js          # Telemetry history table, pagination, status filters, DTC lookup
│
└── templates/
    ├── base.html               # Master layout (Sticky header, health pill, modals, footer)
    ├── index.html              # Home page with project overview, architecture & features
    ├── dashboard.html          # Core Cockpit Dashboard: speed, RPM, temp, battery, fuel, fault injector
    ├── live_charts.html        # Interactive live multi-charts with streaming controls
    ├── ml_anomalies.html       # ML Anomaly Detection & Predictive Maintenance Center
    └── reports.html            # Historical telemetry records, pagination, and CSV download
```

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
|---|---|
| **Frontend** | HTML5, CSS3 (Vanilla design system with glassmorphism), JavaScript (Vanilla ES6+), Chart.js |
| **Backend** | Python 3.10+, Flask 3.x (RESTful API architecture) |
| **Machine Learning** | NumPy, Pandas, Scikit-learn (Isolation Forest Algorithm) |
| **Database** | SQLite3 (Embedded, zero-config relational storage) |
| **Hardware Protocol** | SAE J1979 / ISO 15765-4 (CAN bus standard), ELM327 interface abstraction |

---

## 🚀 Setup & Execution Instructions

### Prerequisites
- Python 3.10, 3.11, 3.12, or 3.13 installed on your system.
- Standard web browser (Chrome, Edge, Firefox, Safari).

### 1. Open Terminal or PowerShell
Navigate into the project root directory:
```bash
cd "Smart Vehicle Health Monitoring Using OBD-II"
```

### 2. Create and Activate Virtual Environment (Recommended)
**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
**Windows (CMD):**
```cmd
python -m venv venv
.\venv\Scripts\activate.bat
```
**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Flask Server
```bash
python app.py
```
You will see the startup banner:
```text
==================================================================
  SMART VEHICLE HEALTH MONITORING SYSTEM USING OBD-II & ML
  Server running at: http://127.0.0.1:5000
==================================================================
 * Running on http://127.0.0.1:5000
```

### 5. Access the Website
Open your browser and navigate to:
```text
http://127.0.0.1:5000
```

---

## 🔌 Integrating Real OBD-II Hardware

This project is architected with a production-ready **Hardware Abstraction Layer** in `obd_hardware.py`.

### How to Connect a Physical ELM327 Adapter:
1. Plug your **ELM327 Bluetooth or USB OBD-II Scanner** into your vehicle's 16-pin DLC port (typically located under the dashboard beneath the steering wheel).
2. If using Bluetooth, pair the dongle with your computer (default PIN is usually `1234` or `0000`). Note the assigned COM port (e.g., `COM3` on Windows or `/dev/rfcomm0` on Linux).
3. If using USB, note the USB-Serial COM port in Device Manager.
4. Install `obd` library:
   ```bash
   pip install obd
   ```
5. In `obd_hardware.py`, the `HardwareOBDAdapter` automatically connects via `obd.OBD()` or you can specify your port:
   ```python
   self.connection = obd.OBD("COM3", baudrate=38400)
   ```
6. Switch data source via REST API:
   ```bash
   curl -X POST http://127.0.0.1:5000/api/system/mode -H "Content-Type: application/json" -d "{\"mode\": \"HARDWARE\"}"
   ```
7. When hardware is disconnected or unavailable, the system automatically falls back to the high-fidelity simulator with clear labels.

---

## 🧪 Testing the Machine Learning & Anomaly Engine

You can immediately test the Isolation Forest and predictive alerts without driving a real car:
1. Open `http://127.0.0.1:5000/dashboard`.
2. Notice the **Health Status: HEALTHY** with normal baseline metrics.
3. In the **Live Fault Injector** panel (or via top right **Inject Fault** button), click **🔥 Engine Overheat**.
4. Within 1-2 seconds, observe:
   - Coolant Temperature meter ramps past 108°C.
   - Health status changes to **CRITICAL**.
   - Active Predictive Maintenance Alert triggers: `P0217 - Severe Engine Overheating Risk`.
   - On the **Predictive ML** page, the Isolation Forest Anomaly Index rises above 85% and the Z-score for `engine_temp` spikes to +6.8σ!
5. Click **🟢 Restore Normal Drive Cycle** to clear the fault and resume smooth cruising.

---

## 📡 REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `GET /api/telemetry/current` | GET | Returns latest vehicle readings, ML anomaly score, and health status |
| `GET /api/telemetry/history?limit=30` | GET | Chronological telemetry series for live charting |
| `GET /api/telemetry/records?page=1&per_page=20` | GET | Paginated historical logs with status filter |
| `GET /api/telemetry/export-csv` | GET | Direct downloadable CSV export of complete vehicle history |
| `GET /api/alerts?resolved=false` | GET | Retrieves active predictive maintenance alerts |
| `POST /api/alerts/<id>/resolve` | POST | Marks a maintenance alert as resolved in SQLite |
| `POST /api/simulator/fault` | POST | Injects artificial fault (`OVERHEAT`, `BATTERY_FAIL`, `MISFIRE`, etc.) |
| `POST /api/simulator/reset` | POST | Clears injected fault and restores normal drive profile |
| `GET /api/system/status` | GET | Connection status (Simulated vs Physical ELM327) |
| `POST /api/ml/retrain` | POST | Retrains Isolation Forest on healthy baseline dataset |
| `GET /api/dtc/lookup?code=P0217` | GET | Queries Diagnostic Trouble Code definition and recommended fix |

---

## 📄 License & Academic Attribution
Developed for Smart Vehicle Health Monitoring and Predictive Maintenance research.
Engineered using Python Flask, Scikit-learn Isolation Forest, and Vanilla Web Technologies.
#   S m a r t - V e h i c l e - H e a l t h - M o n i t o r i n g - U s i n g - O B D - I I  
 #   S m a r t - V e h i c l e - H e a l t h - M o n i t o r i n g - U s i n g - O B D - I I - n o v -  
 