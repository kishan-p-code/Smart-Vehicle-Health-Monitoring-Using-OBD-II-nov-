/**
 * Smart Vehicle Health Monitoring Using OBD-II
 * Machine Learning & Predictive Maintenance Controller (ml_monitor.js)
 */

let currentAlertFilter = 'ALL';

document.addEventListener('DOMContentLoaded', () => {
  updateMLView();
  setInterval(updateMLView, 1500);

  loadMaintenanceAlerts();
  setInterval(loadMaintenanceAlerts, 5000);
});

async function updateMLView() {
  try {
    const res = await fetch('/api/telemetry/current');
    if (!res.ok) return;
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    const data = json.data;

    // 1. Update Anomaly Percentage & Status
    const score = (data.anomaly_score || 0) * 100;
    const scoreElem = document.getElementById('ml-anomaly-percentage');
    const badgeStatus = document.getElementById('ml-badge-status');
    const evalLabel = document.getElementById('ml-eval-label');
    const bar = document.getElementById('ml-anomaly-bar');
    const desc = document.getElementById('ml-diagnostic-desc');

    if (scoreElem) scoreElem.textContent = `${score.toFixed(1)}%`;

    if (bar) {
      bar.style.width = `${Math.min(Math.max(score, 5), 100)}%`;
      bar.className = 'sensor-meter-fill';
      if (score >= 65) bar.classList.add('critical');
      else if (score >= 45) bar.classList.add('warning');
    }

    const health = (data.health_status || 'HEALTHY').toUpperCase();
    if (evalLabel) {
      evalLabel.textContent = health;
      evalLabel.style.color = health === 'CRITICAL' ? 'var(--status-critical)' : (health === 'WARNING' ? 'var(--status-warning)' : 'var(--status-healthy)');
    }

    if (badgeStatus) {
      badgeStatus.className = 'table-badge';
      if (health === 'CRITICAL') {
        badgeStatus.classList.add('badge-critical');
        badgeStatus.textContent = 'HIGH RISK OUTLIER';
      } else if (health === 'WARNING') {
        badgeStatus.classList.add('badge-warning');
        badgeStatus.textContent = 'ANOMALY DETECTED';
      } else {
        badgeStatus.classList.add('badge-healthy');
        badgeStatus.textContent = 'NORMAL BASELINE';
      }
    }

    if (desc) {
      desc.textContent = data.anomaly_reason || 'Operating parameters within optimal baseline.';
    }

    // 2. Render Z-Scores Grid (Feature Deviations)
    const zScores = data.z_scores || {};
    renderZScores(zScores, data);

  } catch (err) {
    console.error('Error updating ML view:', err);
  }
}

function renderZScores(zScores, currentReadings) {
  const container = document.getElementById('z-scores-grid');
  if (!container) return;

  const featureLabels = {
    'speed': { label: 'Speed', unit: 'km/h' },
    'rpm': { label: 'Engine RPM', unit: 'RPM' },
    'engine_temp': { label: 'Coolant Temp', unit: '°C' },
    'battery_voltage': { label: 'Battery Volt', unit: 'V' },
    'fuel_level': { label: 'Fuel Tank', unit: '%' },
    'engine_load': { label: 'Engine Load', unit: '%' },
    'throttle_pos': { label: 'Throttle Pos', unit: '%' },
    'fuel_pressure': { label: 'Fuel Pressure', unit: 'kPa' },
    'intake_temp': { label: 'Intake Temp', unit: '°C' }
  };

  const keys = Object.keys(featureLabels);
  container.innerHTML = keys.map(key => {
    const info = featureLabels[key];
    const z = zScores[key] !== undefined ? zScores[key] : 0.0;
    const currentVal = currentReadings[key] !== undefined ? currentReadings[key] : '--';

    const isAbnormal = Math.abs(z) >= 2.5;
    const isCritical = Math.abs(z) >= 4.0;

    let borderStyle = 'var(--border-subtle)';
    let zColor = 'var(--accent-cyan)';
    let badgeHtml = '<span style="font-size: 0.7rem; color: #10b981;">Normal</span>';

    if (isCritical) {
      borderStyle = 'rgba(239, 68, 68, 0.6)';
      zColor = '#ef4444';
      badgeHtml = '<span class="table-badge badge-critical">Divergent Culprit</span>';
    } else if (isAbnormal) {
      borderStyle = 'rgba(245, 158, 11, 0.6)';
      zColor = '#f59e0b';
      badgeHtml = '<span class="table-badge badge-warning">High Deviation</span>';
    }

    return `
      <div style="background: rgba(18, 30, 56, 0.45); border: 1px solid ${borderStyle}; border-radius: var(--radius-sm); padding: 0.85rem; display: flex; flex-direction: column; justify-content: space-between;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
          <span style="font-size: 0.78rem; font-weight: 600; color: var(--text-secondary); text-transform: uppercase;">${info.label}</span>
          ${badgeHtml}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
          <span style="font-size: 1.15rem; font-weight: 800; color: #fff; font-family: monospace;">${currentVal} <small style="font-size: 0.75rem; color: var(--text-muted);">${info.unit}</small></span>
          <span style="font-size: 0.95rem; font-weight: 700; color: ${zColor}; font-family: monospace;">z = ${z > 0 ? '+' : ''}${z.toFixed(1)}&sigma;</span>
        </div>
      </div>
    `;
  }).join('');
}

// Maintenance Alerts Table Management
async function loadMaintenanceAlerts() {
  try {
    let url = '/api/alerts';
    if (currentAlertFilter === 'ACTIVE') url += '?resolved=false';
    else if (currentAlertFilter === 'RESOLVED') url += '?resolved=true';

    const res = await fetch(url);
    const json = await res.json();
    const tbody = document.getElementById('maintenance-alerts-tbody');
    if (!tbody) return;

    if (json.status !== 'success' || !json.data || json.data.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="7" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            No ${currentAlertFilter.toLowerCase()} maintenance alerts recorded.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = json.data.map(alert => {
      const isCrit = alert.severity === 'CRITICAL';
      const isWarn = alert.severity === 'WARNING';
      const badgeClass = isCrit ? 'badge-critical' : (isWarn ? 'badge-warning' : 'badge-healthy');
      const timeStr = alert.timestamp ? alert.timestamp : 'Recent';

      return `
        <tr>
          <td><span class="table-badge ${badgeClass}">${alert.severity}</span></td>
          <td style="color: var(--accent-cyan); font-weight: 600;">${alert.category}</td>
          <td>
            <strong style="color: #fff; display: block;">${alert.title}</strong>
            <small style="color: var(--text-secondary);">${alert.description}</small>
          </td>
          <td style="font-family: monospace; font-weight: 700; color: ${alert.dtc_code ? '#38bdf8' : 'var(--text-muted)'};">
            ${alert.dtc_code ? `<span style="cursor: pointer;" onclick="quickFillDtc('${alert.dtc_code}')" title="Lookup in DTC master">${alert.dtc_code}</span>` : 'N/A'}
          </td>
          <td style="color: #86efac; font-size: 0.82rem;">${alert.recommended_action}</td>
          <td style="color: var(--text-muted); font-size: 0.78rem; white-space: nowrap;">${timeStr}</td>
          <td>
            ${alert.is_resolved ? 
              '<span class="table-badge badge-healthy">Resolved</span>' : 
              `<button class="btn btn-secondary btn-sm" onclick="resolveAlert(${alert.id})">Mark Resolved</button>`
            }
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Error fetching maintenance alerts:', err);
  }
}

function filterAlerts(filter) {
  currentAlertFilter = filter;
  loadMaintenanceAlerts();
}

async function resolveAlert(alertId) {
  try {
    const res = await fetch(`/api/alerts/${alertId}/resolve`, { method: 'POST' });
    const json = await res.json();
    if (json.status === 'success') {
      showToast('Maintenance alert resolved.', 'info', 'Alert Closed');
      loadMaintenanceAlerts();
    }
  } catch (e) {
    showToast('Failed to resolve alert: ' + e.message, 'critical');
  }
}

// Retrain Model Trigger
async function retrainModel() {
  try {
    showToast('Retraining Isolation Forest model on healthy driving dataset...', 'info', 'Training ML Model');
    const res = await fetch('/api/ml/retrain', { method: 'POST' });
    const json = await res.json();
    if (json.status === 'success') {
      showToast('Isolation Forest model retrained and baseline weights updated!', 'info', 'Retrain Success');
    } else {
      showToast('Model retraining failed.', 'critical');
    }
  } catch (err) {
    showToast('Retrain error: ' + err.message, 'critical');
  }
}
