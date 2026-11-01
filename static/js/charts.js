/**
 * Smart Vehicle Health Monitoring Using OBD-II
 * Real-Time Interactive Telemetry Charts (charts.js)
 */

let chartSpeedRpm = null;
let chartEngineTemp = null;
let chartBatteryVolt = null;
let chartFuelLoad = null;
let chartMlAnomaly = null;

let isStreaming = true;
let bufferSize = 40;
let streamTimer = null;
let lastTimestamp = '';

// Shared Chart.js styling theme
const chartDarkOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: { duration: 350 },
  interaction: { intersect: false, mode: 'index' },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(12, 20, 39, 0.95)',
      borderColor: 'rgba(0, 210, 255, 0.4)',
      borderWidth: 1,
      titleColor: '#38bdf8',
      bodyColor: '#ffffff',
      padding: 10,
      boxPadding: 4
    }
  },
  scales: {
    x: {
      grid: { color: 'rgba(45, 75, 128, 0.2)' },
      ticks: { color: '#64748b', font: { size: 10 }, maxTicksLimit: 8 }
    },
    y: {
      grid: { color: 'rgba(45, 75, 128, 0.2)' },
      ticks: { color: '#94a3b8', font: { size: 11 } }
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  loadInitialHistory();

  // Polling every 1 second
  streamTimer = setInterval(pollLivePoint, 1000);

  const windowSelect = document.getElementById('chart-window-select');
  if (windowSelect) {
    windowSelect.addEventListener('change', (e) => {
      bufferSize = parseInt(e.target.value, 10) || 40;
    });
  }
});

function initCharts() {
  // 1. Speed & RPM Chart (Dual Y Axis)
  const ctxSpeedRpm = document.getElementById('chart-speed-rpm');
  if (ctxSpeedRpm) {
    chartSpeedRpm = new Chart(ctxSpeedRpm, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Speed (km/h)',
            data: [],
            borderColor: '#00d2ff',
            backgroundColor: 'rgba(0, 210, 255, 0.1)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.35,
            yAxisID: 'y_speed',
            pointRadius: 0,
            pointHoverRadius: 5
          },
          {
            label: 'RPM',
            data: [],
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderWidth: 2,
            borderDash: [4, 4],
            tension: 0.35,
            yAxisID: 'y_rpm',
            pointRadius: 0,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        ...chartDarkOptions,
        scales: {
          x: chartDarkOptions.scales.x,
          y_speed: {
            type: 'linear',
            position: 'left',
            min: 0,
            max: 180,
            grid: { color: 'rgba(45, 75, 128, 0.2)' },
            ticks: { color: '#00d2ff', callback: val => `${val} km/h` }
          },
          y_rpm: {
            type: 'linear',
            position: 'right',
            min: 0,
            max: 7000,
            grid: { drawOnChartArea: false },
            ticks: { color: '#f59e0b', callback: val => `${val} RPM` }
          }
        }
      }
    });
  }

  // 2. Coolant Temperature Chart
  const ctxTemp = document.getElementById('chart-engine-temp');
  if (ctxTemp) {
    chartEngineTemp = new Chart(ctxTemp, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Coolant Temp (°C)',
            data: [],
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.15)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.3,
            pointRadius: 0,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        ...chartDarkOptions,
        scales: {
          x: chartDarkOptions.scales.x,
          y: {
            min: 65,
            max: 125,
            grid: { color: 'rgba(45, 75, 128, 0.2)' },
            ticks: { color: '#94a3b8', callback: val => `${val}°C` }
          }
        }
      }
    });
  }

  // 3. Battery Voltage Chart
  const ctxVolt = document.getElementById('chart-battery-volt');
  if (ctxVolt) {
    chartBatteryVolt = new Chart(ctxVolt, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Voltage (V)',
            data: [],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            borderWidth: 2.5,
            fill: true,
            tension: 0.25,
            pointRadius: 0,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        ...chartDarkOptions,
        scales: {
          x: chartDarkOptions.scales.x,
          y: {
            min: 10.5,
            max: 15.5,
            grid: { color: 'rgba(45, 75, 128, 0.2)' },
            ticks: { color: '#10b981', callback: val => `${val}V` }
          }
        }
      }
    });
  }

  // 4. Fuel Level & Engine Load Chart
  const ctxFuelLoad = document.getElementById('chart-fuel-load');
  if (ctxFuelLoad) {
    chartFuelLoad = new Chart(ctxFuelLoad, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Fuel Tank (%)',
            data: [],
            borderColor: '#38bdf8',
            borderWidth: 2,
            tension: 0.2,
            pointRadius: 0
          },
          {
            label: 'Engine Load (%)',
            data: [],
            borderColor: '#c084fc',
            backgroundColor: 'rgba(192, 132, 252, 0.1)',
            fill: true,
            borderWidth: 2,
            tension: 0.35,
            pointRadius: 0
          }
        ]
      },
      options: {
        ...chartDarkOptions,
        scales: {
          x: chartDarkOptions.scales.x,
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(45, 75, 128, 0.2)' },
            ticks: { color: '#94a3b8', callback: val => `${val}%` }
          }
        }
      }
    });
  }

  // 5. ML Isolation Forest Anomaly Index
  const ctxMlAnomaly = document.getElementById('chart-ml-anomaly');
  if (ctxMlAnomaly) {
    chartMlAnomaly = new Chart(ctxMlAnomaly, {
      type: 'line',
      data: {
        labels: [],
        datasets: [
          {
            label: 'Anomaly Risk (%)',
            data: [],
            borderColor: '#ef4444',
            backgroundColor: 'rgba(239, 68, 68, 0.2)',
            fill: true,
            borderWidth: 2.5,
            tension: 0.35,
            pointRadius: 0,
            pointHoverRadius: 5
          }
        ]
      },
      options: {
        ...chartDarkOptions,
        scales: {
          x: chartDarkOptions.scales.x,
          y: {
            min: 0,
            max: 100,
            grid: { color: 'rgba(45, 75, 128, 0.2)' },
            ticks: { color: '#ef4444', callback: val => `${val}%` }
          }
        }
      }
    });
  }
}

// Fetch historical records to prepopulate chart series
async function loadInitialHistory() {
  try {
    const res = await fetch(`/api/telemetry/history?limit=${bufferSize}`);
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    const records = json.data;
    records.forEach(r => appendRecordToCharts(r, false));

    updateAllCharts();
  } catch (err) {
    console.error('Error loading initial chart history:', err);
  }
}

// Fetch single live point and append
async function pollLivePoint() {
  if (!isStreaming) return;
  try {
    const res = await fetch('/api/telemetry/current');
    const json = await res.json();
    if (json.status !== 'success' || !json.data) return;

    const record = json.data;
    if (record.timestamp === lastTimestamp) return;
    lastTimestamp = record.timestamp;

    appendRecordToCharts(record, true);
    updateAllCharts();
  } catch (err) {
    console.error('Error polling live chart point:', err);
  }
}

function appendRecordToCharts(r, pruneOld = true) {
  const timeLabel = r.timestamp ? r.timestamp.split(' ')[1] : '';

  const charts = [
    { chart: chartSpeedRpm, values: [r.speed || 0, r.rpm || 0] },
    { chart: chartEngineTemp, values: [r.engine_temp || 0] },
    { chart: chartBatteryVolt, values: [r.battery_voltage || 0] },
    { chart: chartFuelLoad, values: [r.fuel_level || 0, r.engine_load || 0] },
    { chart: chartMlAnomaly, values: [((r.anomaly_score || 0) * 100)] }
  ];

  charts.forEach(({ chart, values }) => {
    if (!chart) return;
    chart.data.labels.push(timeLabel);
    values.forEach((val, idx) => {
      if (chart.data.datasets[idx]) {
        chart.data.datasets[idx].data.push(val);
      }
    });

    if (pruneOld && chart.data.labels.length > bufferSize) {
      chart.data.labels.shift();
      chart.data.datasets.forEach(ds => ds.data.shift());
    }
  });
}

function updateAllCharts() {
  if (chartSpeedRpm) chartSpeedRpm.update('none');
  if (chartEngineTemp) chartEngineTemp.update('none');
  if (chartBatteryVolt) chartBatteryVolt.update('none');
  if (chartFuelLoad) chartFuelLoad.update('none');
  if (chartMlAnomaly) chartMlAnomaly.update('none');
}

function toggleChartStream() {
  isStreaming = !isStreaming;
  const btn = document.getElementById('btn-pause-charts');
  const text = document.getElementById('pause-text');
  const icon = document.getElementById('pause-icon');

  if (isStreaming) {
    if (text) text.textContent = 'Pause Stream';
    if (icon) icon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
    showToast('Telemetry streaming resumed.', 'info');
  } else {
    if (text) text.textContent = 'Resume Stream';
    if (icon) icon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
    showToast('Telemetry streaming paused.', 'warning');
  }
}

function resetChartHistory() {
  const charts = [chartSpeedRpm, chartEngineTemp, chartBatteryVolt, chartFuelLoad, chartMlAnomaly];
  charts.forEach(c => {
    if (c) {
      c.data.labels = [];
      c.data.datasets.forEach(ds => ds.data = []);
      c.update();
    }
  });
  showToast('Chart memory buffer cleared.', 'info');
}
