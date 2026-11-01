/**
 * Smart Vehicle Health Monitoring Using OBD-II
 * Reports & Historical Records Controller (reports.js)
 */

let currentPage = 1;
let perPage = 20;
let currentStatus = 'ALL';
let anomaliesOnly = false;
let totalPages = 1;

document.addEventListener('DOMContentLoaded', () => {
  loadTelemetryRecords();
  loadDtcMasterReference();
});

async function loadTelemetryRecords() {
  const tbody = document.getElementById('telemetry-logs-tbody');
  const countLabel = document.getElementById('reports-count-label');
  const paginationInfo = document.getElementById('pagination-info');
  const pageIndicator = document.getElementById('page-indicator');
  const btnPrev = document.getElementById('btn-page-prev');
  const btnNext = document.getElementById('btn-page-next');

  try {
    const url = `/api/telemetry/records?page=${currentPage}&per_page=${perPage}&status=${currentStatus}&anomaly_only=${anomaliesOnly}`;
    const res = await fetch(url);
    const json = await res.json();

    if (json.status !== 'success') {
      if (tbody) tbody.innerHTML = `<tr><td colspan="12" style="text-align: center; color: #ef4444; padding: 2rem;">Error loading records.</td></tr>`;
      return;
    }

    const records = json.records || [];
    totalPages = json.total_pages || 1;
    const totalCount = json.total || 0;

    if (countLabel) countLabel.textContent = `Total Logs: ${totalCount} records`;
    if (pageIndicator) pageIndicator.textContent = `${currentPage} / ${totalPages}`;
    if (paginationInfo) paginationInfo.textContent = `Showing page ${currentPage} of ${totalPages} (${totalCount} total entries)`;

    if (btnPrev) btnPrev.disabled = currentPage <= 1;
    if (btnNext) btnNext.disabled = currentPage >= totalPages;

    if (!tbody) return;

    if (records.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="12" style="text-align: center; color: var(--text-muted); padding: 2rem;">
            No records found matching current criteria.
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = records.map(r => {
      const status = (r.health_status || 'HEALTHY').toUpperCase();
      let badgeClass = 'badge-healthy';
      if (status === 'CRITICAL') badgeClass = 'badge-critical';
      else if (status === 'WARNING') badgeClass = 'badge-warning';

      const anomalyScorePct = ((r.anomaly_score || 0) * 100).toFixed(1);
      const isAnomaly = r.is_anomaly ? '<span style="color: #ef4444; font-weight: 700;">YES</span>' : '<span style="color: #64748b;">No</span>';

      return `
        <tr>
          <td style="font-family: monospace; color: var(--text-muted);">#${r.id}</td>
          <td style="white-space: nowrap; font-size: 0.8rem; color: #cbd5e1;">${r.timestamp}</td>
          <td style="font-family: monospace; font-weight: 700; color: #00d2ff;">${r.speed} km/h</td>
          <td style="font-family: monospace; color: #f59e0b;">${Math.round(r.rpm)} RPM</td>
          <td style="font-family: monospace; color: ${r.engine_temp >= 100 ? '#ef4444' : '#fff'};">${r.engine_temp}°C</td>
          <td style="font-family: monospace; color: ${r.battery_voltage < 12.0 ? '#ef4444' : '#fff'};">${r.battery_voltage}V</td>
          <td style="font-family: monospace;">${r.fuel_level}%</td>
          <td style="font-family: monospace;">${r.engine_load}%</td>
          <td style="font-family: monospace; color: ${r.anomaly_score > 0.5 ? '#ef4444' : 'var(--text-muted)'};">${anomalyScorePct}%</td>
          <td><span class="table-badge ${badgeClass}">${status}</span></td>
          <td style="font-size: 0.8rem; color: var(--text-secondary); max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${r.anomaly_reason || ''}">
            ${r.anomaly_reason || 'Normal operation'}
          </td>
          <td><span class="sim-source-tag" style="font-size: 0.68rem; padding: 0.15rem 0.4rem;">${r.data_source}</span></td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading telemetry records:', err);
  }
}

function applyStatusFilter(status) {
  currentStatus = status;
  currentPage = 1;

  // Update button visual states
  ['all', 'healthy', 'warning', 'critical'].forEach(s => {
    const btn = document.getElementById(`filter-${s}`);
    if (btn) {
      if (s.toUpperCase() === status) {
        btn.classList.add('btn-primary');
        btn.classList.remove('btn-secondary');
      } else {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-secondary');
      }
    }
  });

  loadTelemetryRecords();
}

function toggleAnomaliesOnly() {
  const chk = document.getElementById('chk-anomalies-only');
  anomaliesOnly = chk ? chk.checked : false;
  currentPage = 1;
  loadTelemetryRecords();
}

function changePerPage(val) {
  perPage = parseInt(val, 10) || 20;
  currentPage = 1;
  loadTelemetryRecords();
}

function goToPage(page) {
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  loadTelemetryRecords();
}

// Load master DTC table
async function loadDtcMasterReference() {
  const tbody = document.getElementById('dtc-master-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/dtc/lookup');
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    tbody.innerHTML = json.data.map(dtc => {
      const isCrit = dtc.severity === 'CRITICAL';
      const badgeClass = isCrit ? 'badge-critical' : 'badge-warning';

      return `
        <tr>
          <td style="font-family: monospace; font-weight: 700; color: #38bdf8;">${dtc.code}</td>
          <td style="color: var(--accent-cyan); font-weight: 600;">${dtc.system}</td>
          <td><span class="table-badge ${badgeClass}">${dtc.severity}</span></td>
          <td style="color: #fff; font-weight: 500;">${dtc.description}</td>
          <td style="color: var(--text-secondary); font-size: 0.8rem;">${dtc.possible_causes}</td>
          <td style="color: #86efac; font-size: 0.8rem;">${dtc.recommended_fix}</td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading DTC master definitions:', err);
  }
}
