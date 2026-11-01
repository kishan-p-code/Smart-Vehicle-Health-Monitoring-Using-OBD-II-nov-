/**
 * Smart Vehicle Health Monitoring Using OBD-II
 * Automotive Cockpit Dashboard Controller (dashboard.js)
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initial fetch and continuous live polling every 1 second
  updateDashboard();
  setInterval(updateDashboard, 1000);
});

async function updateDashboard() {
  try {
    const res = await fetch('/api/telemetry/current');
    if (!res.ok) return;
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    const data = json.data;

    // 1. Update Speedometer Gauge
    const speed = data.speed || 0;
    const speedMax = 200;
    const speedRatio = Math.min(Math.max(speed / speedMax, 0), 1);
    const speedNeedleAngle = -120 + (speedRatio * 240);
    const speedDashOffset = 400 - (speedRatio * 400);

    const speedValElem = document.getElementById('dash-speed-val');
    if (speedValElem) speedValElem.textContent = Math.round(speed);

    const speedNeedle = document.getElementById('speed-needle-group');
    if (speedNeedle) speedNeedle.style.transform = `rotate(${speedNeedleAngle}deg)`;

    const speedPath = document.getElementById('speed-gauge-path');
    if (speedPath) speedPath.style.strokeDashoffset = speedDashOffset;

    // Simulated Gear Display
    const gearBadge = document.getElementById('dash-gear-badge');
    if (gearBadge) {
      if (speed < 1.0) gearBadge.textContent = 'P • Idle';
      else if (speed < 25) gearBadge.textContent = 'D • 1st Gear';
      else if (speed < 45) gearBadge.textContent = 'D • 2nd Gear';
      else if (speed < 70) gearBadge.textContent = 'D • 3rd Gear';
      else if (speed < 95) gearBadge.textContent = 'D • 4th Gear';
      else if (speed < 120) gearBadge.textContent = 'D • 5th Gear';
      else gearBadge.textContent = 'D • 6th Overdrive';
    }

    // 2. Update Tachometer (RPM) Gauge
    const rpm = data.rpm || 0;
    const rpmMax = 8000;
    const rpmRatio = Math.min(Math.max(rpm / rpmMax, 0), 1);
    const rpmNeedleAngle = -120 + (rpmRatio * 240);
    const rpmDashOffset = 400 - (rpmRatio * 400);

    const rpmValElem = document.getElementById('dash-rpm-val');
    if (rpmValElem) rpmValElem.textContent = Math.round(rpm).toLocaleString();

    const rpmNeedle = document.getElementById('rpm-needle-group');
    if (rpmNeedle) rpmNeedle.style.transform = `rotate(${rpmNeedleAngle}deg)`;

    const rpmPath = document.getElementById('rpm-gauge-path');
    if (rpmPath) rpmPath.style.strokeDashoffset = rpmDashOffset;

    const rpmStatus = document.getElementById('dash-rpm-status');
    if (rpmStatus) {
      if (rpm > 5800) {
        rpmStatus.className = 'table-badge badge-critical';
        rpmStatus.textContent = 'REDLINE WARNING';
      } else if (rpm > 4200) {
        rpmStatus.className = 'table-badge badge-warning';
        rpmStatus.textContent = 'High Load RPM';
      } else if (rpm > 1200) {
        rpmStatus.className = 'table-badge badge-healthy';
        rpmStatus.textContent = 'Cruising RPM';
      } else {
        rpmStatus.className = 'table-badge badge-healthy';
        rpmStatus.textContent = 'Optimal Idle';
      }
    }

    // 3. Sensor Cards: Engine Temp
    const temp = data.engine_temp || 0;
    const tempVal = document.getElementById('dash-temp-val');
    const meterTemp = document.getElementById('meter-temp');
    const dotTemp = document.getElementById('dot-temp');
    if (tempVal) tempVal.textContent = temp.toFixed(1);
    if (meterTemp) {
      // 50°C to 130°C range
      const tempPercent = Math.min(Math.max(((temp - 50) / 80) * 100, 5), 100);
      meterTemp.style.width = `${tempPercent}%`;
      meterTemp.className = 'sensor-meter-fill';
      if (dotTemp) dotTemp.className = 'sensor-status-dot';

      if (temp >= 108.0) {
        meterTemp.classList.add('critical');
        if (dotTemp) dotTemp.classList.add('critical');
      } else if (temp >= 98.0) {
        meterTemp.classList.add('warning');
        if (dotTemp) dotTemp.classList.add('warning');
      }
    }

    // 4. Sensor Cards: Battery Voltage
    const volt = data.battery_voltage || 0;
    const voltVal = document.getElementById('dash-volt-val');
    const meterVolt = document.getElementById('meter-volt');
    const dotVolt = document.getElementById('dot-volt');
    if (voltVal) voltVal.textContent = volt.toFixed(2);
    if (meterVolt) {
      // 10V to 16V scale
      const voltPercent = Math.min(Math.max(((volt - 10) / 6) * 100, 5), 100);
      meterVolt.style.width = `${voltPercent}%`;
      meterVolt.className = 'sensor-meter-fill';
      if (dotVolt) dotVolt.className = 'sensor-status-dot';

      if (volt <= 11.8 || volt >= 15.5) {
        meterVolt.classList.add('critical');
        if (dotVolt) dotVolt.classList.add('critical');
      } else if (volt < 12.8 || volt > 15.0) {
        meterVolt.classList.add('warning');
        if (dotVolt) dotVolt.classList.add('warning');
      }
    }

    // 5. Sensor Cards: Fuel Level
    const fuel = data.fuel_level || 0;
    const fuelVal = document.getElementById('dash-fuel-val');
    const meterFuel = document.getElementById('meter-fuel');
    const dotFuel = document.getElementById('dot-fuel');
    if (fuelVal) fuelVal.textContent = fuel.toFixed(1);
    if (meterFuel) {
      meterFuel.style.width = `${Math.min(Math.max(fuel, 2), 100)}%`;
      meterFuel.className = 'sensor-meter-fill';
      if (dotFuel) dotFuel.className = 'sensor-status-dot';

      if (fuel <= 8.0) {
        meterFuel.classList.add('critical');
        if (dotFuel) dotFuel.classList.add('critical');
      } else if (fuel <= 18.0) {
        meterFuel.classList.add('warning');
        if (dotFuel) dotFuel.classList.add('warning');
      }
    }

    // 6. Sensor Cards: Engine Load & Throttle
    const load = data.engine_load || 0;
    const loadVal = document.getElementById('dash-load-val');
    const meterLoad = document.getElementById('meter-load');
    const dotLoad = document.getElementById('dot-load');
    if (loadVal) loadVal.textContent = load.toFixed(1);
    if (meterLoad) {
      meterLoad.style.width = `${Math.min(Math.max(load, 5), 100)}%`;
      meterLoad.className = 'sensor-meter-fill';
      if (dotLoad) dotLoad.className = 'sensor-status-dot';

      if (load >= 90.0) {
        meterLoad.classList.add('critical');
        if (dotLoad) dotLoad.classList.add('critical');
      } else if (load >= 75.0) {
        meterLoad.classList.add('warning');
        if (dotLoad) dotLoad.classList.add('warning');
      }
    }

    const throttleVal = document.getElementById('dash-throttle-val');
    if (throttleVal) throttleVal.textContent = `${Math.round(data.throttle_pos || 0)}%`;

    // 7. Sensor Cards: Fuel Rail Pressure & Intake Temp
    const pressure = data.fuel_pressure || 0;
    const pressureVal = document.getElementById('dash-pressure-val');
    const meterPressure = document.getElementById('meter-pressure');
    const dotPressure = document.getElementById('dot-pressure');
    if (pressureVal) pressureVal.textContent = Math.round(pressure);
    if (meterPressure) {
      // 100 to 500 kPa scale
      const pressPercent = Math.min(Math.max(((pressure - 100) / 400) * 100, 5), 100);
      meterPressure.style.width = `${pressPercent}%`;
      meterPressure.className = 'sensor-meter-fill';
      if (dotPressure) dotPressure.className = 'sensor-status-dot';

      if (pressure < 220 || pressure > 450) {
        meterPressure.classList.add('critical');
        if (dotPressure) dotPressure.classList.add('critical');
      } else if (pressure < 280 || pressure > 410) {
        meterPressure.classList.add('warning');
        if (dotPressure) dotPressure.classList.add('warning');
      }
    }

    const intakeVal = document.getElementById('dash-intake-val');
    if (intakeVal) intakeVal.textContent = `${Math.round(data.intake_temp || 0)}°C`;

    // 8. Overall Health Status Hero Banner
    const healthStatus = (data.health_status || 'HEALTHY').toUpperCase();
    const banner = document.getElementById('dash-health-banner');
    const healthLabel = document.getElementById('dash-health-label');
    const diagSummary = document.getElementById('dash-diagnostic-summary');
    const anomalyScore = document.getElementById('dash-anomaly-score');
    const timestampElem = document.getElementById('dash-timestamp');

    if (banner) {
      banner.className = 'health-hero-banner';
      if (healthStatus === 'WARNING') banner.classList.add('banner-warning');
      else if (healthStatus === 'CRITICAL') banner.classList.add('banner-critical');
    }

    if (healthLabel) healthLabel.textContent = healthStatus;
    if (diagSummary) diagSummary.textContent = data.anomaly_reason || 'All parameters normal.';
    if (anomalyScore) anomalyScore.textContent = `${((data.anomaly_score || 0) * 100).toFixed(1)}%`;
    if (timestampElem) timestampElem.textContent = data.timestamp ? data.timestamp.split(' ')[1] : '--:--:--';

    // 9. Fault active bar
    const faultBar = document.getElementById('dash-fault-active-bar');
    const faultName = document.getElementById('dash-active-fault-name');
    if (faultBar && faultName) {
      if (data.active_fault) {
        faultBar.style.display = 'flex';
        faultName.textContent = data.active_fault;
      } else {
        faultBar.style.display = 'none';
      }
    }

  } catch (err) {
    console.error('Error updating cockpit dashboard:', err);
  }
}

// Fetch and display active maintenance alerts preview
async function loadRecentAlerts() {
  try {
    const res = await fetch('/api/alerts?resolved=false');
    const json = await res.json();
    const container = document.getElementById('dash-alerts-container');
    if (!container) return;

    if (json.status !== 'success' || !json.data || json.data.length === 0) {
      container.innerHTML = `
        <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.25); border-radius: var(--radius-sm); padding: 1rem; display: flex; align-items: center; gap: 0.85rem;">
          <span style="font-size: 1.25rem;">✅</span>
          <div>
            <strong style="color: #6ee7b7; font-size: 0.88rem;">All Systems Diagnostic Clearance</strong>
            <p style="color: var(--text-secondary); font-size: 0.8rem; margin-top: 0.15rem;">No active fault codes or unhandled maintenance warnings detected.</p>
          </div>
        </div>
      `;
      return;
    }

    container.innerHTML = json.data.slice(0, 3).map(alert => {
      const isCrit = alert.severity === 'CRITICAL';
      const borderCol = isCrit ? 'var(--status-critical)' : 'var(--status-warning)';
      const bgCol = isCrit ? 'rgba(239, 68, 68, 0.12)' : 'rgba(245, 158, 11, 0.1)';
      const badgeClass = isCrit ? 'badge-critical' : 'badge-warning';

      return `
        <div style="background: ${bgCol}; border: 1px solid ${borderCol}; border-radius: var(--radius-sm); padding: 0.85rem 1.15rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem;">
          <div style="flex: 1; min-width: 250px;">
            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;">
              <span class="table-badge ${badgeClass}">${alert.severity}</span>
              ${alert.dtc_code ? `<span style="font-family: monospace; color: var(--accent-cyan); font-weight: 700; font-size: 0.85rem;">${alert.dtc_code}</span>` : ''}
              <strong style="color: #fff; font-size: 0.9rem;">${alert.title}</strong>
            </div>
            <p style="color: var(--text-secondary); font-size: 0.8rem;">${alert.description}</p>
          </div>
          <button class="btn btn-secondary btn-sm" onclick="resolveDashboardAlert(${alert.id})">Mark Resolved</button>
        </div>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching alerts preview:', err);
  }
}

async function resolveDashboardAlert(alertId) {
  try {
    await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
    showToast('Alert marked as resolved.', 'info');
    loadRecentAlerts();
  } catch (e) {
    showToast('Failed to resolve alert: ' + e.message, 'critical');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  loadRecentAlerts();
  setInterval(loadRecentAlerts, 5000);
});
