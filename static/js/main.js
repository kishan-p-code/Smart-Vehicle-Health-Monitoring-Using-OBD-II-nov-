/**
 * Smart Vehicle Health Monitoring Using OBD-II
 * Global Core JavaScript (main.js)
 */

// Toast Notifications System
function showToast(message, type = 'info', title = '') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconSvg = type === 'critical' ? '🚨' : (type === 'warning' ? '⚠️' : 'ℹ️');

  toast.innerHTML = `
    <span style="font-size: 1.25rem;">${iconSvg}</span>
    <div style="flex: 1;">
      ${title ? `<strong style="display: block; font-size: 0.85rem; margin-bottom: 0.2rem; color: #fff;">${title}</strong>` : ''}
      <span style="font-size: 0.8rem; color: #cbd5e1;">${message}</span>
    </div>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4500);
}

// Modal Controllers
function openFaultModal() {
  const modal = document.getElementById('fault-modal');
  if (modal) modal.classList.add('show');
}

function closeFaultModal() {
  const modal = document.getElementById('fault-modal');
  if (modal) modal.classList.remove('show');
}

function openDtcModal() {
  const modal = document.getElementById('dtc-modal');
  if (modal) {
    modal.classList.add('show');
    const input = document.getElementById('dtc-search-input');
    if (input) input.focus();
  }
}

function closeDtcModal() {
  const modal = document.getElementById('dtc-modal');
  if (modal) modal.classList.remove('show');
}

// Close modals when clicking backdrop
window.addEventListener('click', (e) => {
  const faultModal = document.getElementById('fault-modal');
  const dtcModal = document.getElementById('dtc-modal');
  if (e.target === faultModal) closeFaultModal();
  if (e.target === dtcModal) closeDtcModal();
});

// Modal button bindings
document.addEventListener('DOMContentLoaded', () => {
  const btnFault = document.getElementById('btn-quick-fault');
  if (btnFault) btnFault.addEventListener('click', openFaultModal);

  const btnDtc = document.getElementById('btn-dtc-modal');
  if (btnDtc) btnDtc.addEventListener('click', openDtcModal);

  // Poll system and vehicle status for global header
  pollGlobalStatus();
  setInterval(pollGlobalStatus, 2000);
});

// Global Header Telemetry Polling
async function pollGlobalStatus() {
  try {
    const res = await fetch('/api/telemetry/current');
    if (!res.ok) return;
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    const data = json.data;

    // Update Header Health Badge
    const badge = document.getElementById('nav-health-badge');
    const label = document.getElementById('nav-health-text');
    if (badge && label) {
      const status = (data.health_status || 'HEALTHY').toUpperCase();
      badge.className = 'health-status-badge';
      if (status === 'WARNING') badge.classList.add('status-warning');
      else if (status === 'CRITICAL') badge.classList.add('status-critical');
      label.textContent = status;
    }

    // Update Header Stream Source Label
    const streamLabel = document.getElementById('nav-stream-label');
    if (streamLabel) {
      if (data.data_source === 'HARDWARE_OBD') {
        streamLabel.textContent = 'HARDWARE ELM327';
        streamLabel.style.color = '#10b981';
      } else {
        streamLabel.textContent = data.active_fault ? `SIMULATED (${data.active_fault})` : 'SIMULATED STREAM';
        streamLabel.style.color = data.active_fault ? '#f59e0b' : 'var(--accent-cyan)';
      }
    }
  } catch (err) {
    console.debug('Global status poll error:', err);
  }
}

// Fault Injection Handlers
async function triggerSimFault(faultType) {
  try {
    const res = await fetch('/api/simulator/fault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fault_type: faultType, duration: 60 })
    });
    const json = await res.json();
    closeFaultModal();
    showToast(json.message, 'warning', `Fault Injected: ${faultType}`);
    pollGlobalStatus();
  } catch (e) {
    showToast('Failed to trigger simulated fault: ' + e.message, 'critical', 'Error');
  }
}

async function resetSimFault() {
  try {
    const res = await fetch('/api/simulator/reset', { method: 'POST' });
    const json = await res.json();
    closeFaultModal();
    showToast('Driving dynamics restored to healthy operating baseline.', 'info', 'Drive Cycle Restored');
    pollGlobalStatus();
  } catch (e) {
    showToast('Failed to reset simulation: ' + e.message, 'critical', 'Error');
  }
}

// DTC Code Lookup Handler
async function searchDTC() {
  const input = document.getElementById('dtc-search-input');
  const resultDiv = document.getElementById('dtc-search-result');
  if (!input || !resultDiv) return;

  const code = input.value.trim().toUpperCase();
  if (!code) {
    showToast('Please enter an OBD-II code (e.g. P0217, P0562)', 'warning');
    return;
  }

  try {
    const res = await fetch(`/api/dtc/lookup?code=${encodeURIComponent(code)}`);
    const json = await res.json();

    if (json.status === 'success' && json.data) {
      const dtc = json.data;
      const sevClass = dtc.severity === 'CRITICAL' ? 'badge-critical' : 'badge-warning';

      resultDiv.style.display = 'block';
      resultDiv.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
          <h4 style="font-size: 1.1rem; color: #fff; font-family: monospace;">${dtc.code}</h4>
          <span class="table-badge ${sevClass}">${dtc.severity}</span>
        </div>
        <div style="font-size: 0.85rem; color: var(--accent-cyan); margin-bottom: 0.4rem;"><strong>Subsystem:</strong> ${dtc.system}</div>
        <div style="font-size: 0.85rem; color: #fff; margin-bottom: 0.6rem;"><strong>Description:</strong> ${dtc.description}</div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.4rem;"><strong>Possible Causes:</strong> ${dtc.possible_causes}</div>
        <div style="font-size: 0.8rem; color: #86efac;"><strong>Recommended Fix:</strong> ${dtc.recommended_fix}</div>
      `;
    } else {
      resultDiv.style.display = 'block';
      resultDiv.innerHTML = `
        <div style="color: #f87171; font-size: 0.85rem;">
          ⚠️ No standard diagnostic trouble code definition found for <strong>${code}</strong> in local database.
        </div>
      `;
    }
  } catch (err) {
    showToast('DTC lookup error: ' + err.message, 'critical', 'Error');
  }
}

function quickFillDtc(code) {
  const input = document.getElementById('dtc-search-input');
  if (input) {
    input.value = code;
    searchDTC();
  }
}
