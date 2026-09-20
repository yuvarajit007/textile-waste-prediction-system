/**
 * TexPulse AI - Frontend Application Logic
 * Manages tab switching, real-time predictions, Chart.js visualizations,
 * data table filtering/pagination, file uploads, and system settings.
 */

// Global State
const state = {
  activeTab: 'tab-overview',
  currentPage: 1,
  pageSize: 50,
  totalBatches: 0,
  filters: {
    machine: 'ALL',
    fabric: 'ALL',
    shift: 'ALL',
    operator: 'ALL',
    risk: 'ALL',
    search: ''
  },
  charts: {},
  lastPrediction: null,
  predictorSubTab: 'subtab-expected-waste',
  lastAfterPrediction: null,
  afterPredictionBatch: null,
  config: {},
  rcaData: null,
  activeRcaBatch: null,
  activeRcaDiag: null,
  digitalTwin: {
    scene: null,
    camera: null,
    renderer: null,
    controls: null,
    animationId: null,
    isInitialized: false,
    isPlaying: true,
    viewMode: 'realistic',
    cameraPreset: 'overview',
    speedRpm: 850,
    explosionDistance: 0.7,
    vibrationEnabled: true,
    particlesEnabled: true,
    targetMachineId: 'M02',
    targetFabric: 'Silk',
    activeComponent: 'motor',
    raycaster: null,
    mouse: null,
    parts: {},
    groups: {},
    materials: {},
    particles: null,
    fps: 60,
    lastFrameTime: performance.now(),
    frameCount: 0,
    fpsUpdateTime: performance.now()
  }
};

// Preset Edge Cases Data
const PRESETS = {
  expected_waste_demo: {
    batch_id: 'BATCH-EXP-M03-' + Math.floor(1000 + Math.random() * 9000),
    machine_id: 'M03',
    fabric_type: 'Cotton',
    shift: 'Night',
    operator: 'Marcus Vance',
    total_production: 1000,
    waste_quantity: '', // Pre-production: waste unknown
    production_speed: 880,
    machine_age: 8.0,
    last_maintenance_date: getDaysAgoDate(200),
    humidity: 75,
    temperature: 34.0
  },
  normal: {
    batch_id: 'BATCH-NORMAL-' + Math.floor(1000 + Math.random() * 9000),
    machine_id: 'M08',
    fabric_type: 'Cotton',
    shift: 'Morning',
    operator: 'David Kim',
    total_production: 1200,
    waste_quantity: 42,
    production_speed: 850,
    machine_age: 1.5,
    last_maintenance_date: getDaysAgoDate(12),
    humidity: 56,
    temperature: 24.5
  },
  high_prod_low_pct: {
    batch_id: 'BATCH-HIGH-PROD-LOW-PCT',
    machine_id: 'M08',
    fabric_type: 'Denim',
    shift: 'Morning',
    operator: 'David Kim',
    total_production: 5000,
    waste_quantity: 100, // 2.0% waste!
    production_speed: 780,
    machine_age: 1.5,
    last_maintenance_date: getDaysAgoDate(10),
    humidity: 58,
    temperature: 25.0
  },
  low_prod_high_pct: {
    batch_id: 'BATCH-LOW-PROD-HIGH-PCT',
    machine_id: 'M02',
    fabric_type: 'Silk',
    shift: 'Night',
    operator: 'Priya Sharma',
    total_production: 100,
    waste_quantity: 30, // 30.0% waste!
    production_speed: 660,
    machine_age: 6.2,
    last_maintenance_date: getDaysAgoDate(88),
    humidity: 38,
    temperature: 29.0
  },
  new_machine: {
    batch_id: 'BATCH-NEW-M10',
    machine_id: 'M10',
    fabric_type: 'Cotton',
    shift: 'Morning',
    operator: 'Wei Zhang',
    total_production: 1100,
    waste_quantity: 40,
    production_speed: 840,
    machine_age: 0.1,
    last_maintenance_date: getDaysAgoDate(3),
    humidity: 55,
    temperature: 25.0
  },
  overdue_maint: {
    batch_id: 'BATCH-OVERDUE-MAINT',
    machine_id: 'M02',
    fabric_type: 'Wool',
    shift: 'Night',
    operator: 'Elena Rostova',
    total_production: 950,
    waste_quantity: 85,
    production_speed: 710,
    machine_age: 6.2,
    last_maintenance_date: getDaysAgoDate(95),
    humidity: 50,
    temperature: 26.5
  },
  missing_humidity: {
    batch_id: 'BATCH-MISSING-HUMIDITY',
    machine_id: 'M04',
    fabric_type: 'Polyester',
    shift: 'Afternoon',
    operator: 'Carlos Rossi',
    total_production: 1600,
    waste_quantity: 46,
    production_speed: 920,
    machine_age: 3.5,
    last_maintenance_date: getDaysAgoDate(20),
    humidity: '', // Missing!
    temperature: 26.0
  },
  high_speed_stress: {
    batch_id: 'BATCH-HIGH-SPEED',
    machine_id: 'M03',
    fabric_type: 'Silk',
    shift: 'Afternoon',
    operator: 'Marcus Vance',
    total_production: 750,
    waste_quantity: 90,
    production_speed: 980, // Safe pace is ~650
    machine_age: 9.0,
    last_maintenance_date: getDaysAgoDate(42),
    humidity: 42,
    temperature: 30.5
  },
  zero_prod: {
    batch_id: 'BATCH-ZERO-PROD',
    machine_id: 'M06',
    fabric_type: 'Cotton',
    shift: 'Morning',
    operator: 'John Doe',
    total_production: 0, // Zero production!
    waste_quantity: 15,
    production_speed: 0,
    machine_age: 2.8,
    last_maintenance_date: getDaysAgoDate(15),
    humidity: 55,
    temperature: 25.0
  }
};

function getDaysAgoDate(days) {
  const d = new Date();
  d.setDate(d.getDate() - days);
  return d.toISOString().split('T')[0];
}

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ------------------------------------------------------------
// INITIALIZATION
// ------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  initNavigation();
  initPredictorSubTabs();
  initPredictorForm();
  initAfterPredictionSubTab();
  initRootCauseAI();
  init3DDigitalTwin();
  initFilters();
  initFileUpload();
  initSettings();
  loadConfig();
  loadOverviewData();
  
  // Set default dates for forms
  const dateInput = document.getElementById('p-maint-date');
  if (dateInput) {
    dateInput.value = getDaysAgoDate(25);
  }
  const apDateInput = document.getElementById('ap-maint-date');
  if (apDateInput) {
    apDateInput.value = getDaysAgoDate(95);
  }

  // Initial predictions so Risk Level and hero stats are live and accurate
  setTimeout(() => {
    runSinglePrediction(false);
  }, 100);

  // Auto-refresh periodically (e.g. every 60s)
  setInterval(() => {
    if (state.activeTab === 'tab-overview') loadOverviewData(false);
  }, 60000);
});


// ------------------------------------------------------------
// NAVIGATION & TAB SWITCHING
// ------------------------------------------------------------
function initNavigation() {
  const navItems = document.querySelectorAll('.nav-item');
  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const tabId = item.getAttribute('data-tab');
      switchTab(tabId);
    });
  });

  document.getElementById('btn-quick-predict')?.addEventListener('click', () => {
    switchTab('tab-predictor');
  });

  document.getElementById('btn-quick-upload')?.addEventListener('click', () => {
    switchTab('tab-ingestion-settings');
  });

  document.getElementById('btn-refresh-all')?.addEventListener('click', () => {
    refreshActiveTabData();
    showToast('Dashboard refreshed with latest telemetry', 'info');
  });

  // Executive Plant Report in Top Navbar
  document.getElementById('btn-plant-report')?.addEventListener('click', () => {
    openPlantExecutiveReport();
  });

  // Report Modal Close & Print buttons
  document.getElementById('btn-close-report-modal')?.addEventListener('click', closeReportModal);
  document.getElementById('btn-print-report')?.addEventListener('click', () => {
    window.print();
  });
  document.getElementById('btn-download-report-txt')?.addEventListener('click', downloadCurrentReportAsText);

  // Close modals on overlay click or Escape key
  document.getElementById('batch-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'batch-modal') closeModal();
  });
  document.getElementById('finalized-report-modal')?.addEventListener('click', (e) => {
    if (e.target.id === 'finalized-report-modal') closeReportModal();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeModal();
      closeReportModal();
    }
  });

  document.getElementById('btn-close-modal')?.addEventListener('click', closeModal);
}

function switchTab(tabId) {
  state.activeTab = tabId;

  // Update Nav Active State
  document.querySelectorAll('.nav-item').forEach(el => {
    el.classList.toggle('active', el.getAttribute('data-tab') === tabId);
  });

  // Update Panes
  document.querySelectorAll('.tab-pane').forEach(el => {
    el.classList.toggle('active', el.id === tabId);
  });

  // Update Header Title
  const activeNav = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
  if (activeNav) {
    const text = activeNav.querySelector('span')?.textContent || 'Dashboard';
    document.getElementById('current-tab-title').textContent = text;
  }

  // Load Data for Tab
  refreshActiveTabData();
}

function refreshActiveTabData() {
  switch (state.activeTab) {
    case 'tab-overview':
      loadOverviewData();
      break;
    case 'tab-3d-model':
      load3DModelTab();
      break;
    case 'tab-root-cause':
      loadRootCauseTab();
      break;
    case 'tab-machines':
      loadMachineAnalytics();
      break;
    case 'tab-fabrics-shifts':
      loadFabricAndShiftAnalytics();
      break;
    case 'tab-operator-maintenance':
      loadOperatorAndMaintenanceAnalytics();
      break;
    case 'tab-batches':
      loadBatchesTable();
      break;
    case 'tab-ingestion-settings':
      loadConfig();
      break;
  }
}


// ------------------------------------------------------------
// TAB 1: OVERVIEW & DASHBOARD KPIS
// ------------------------------------------------------------
async function loadOverviewData(showLoading = true) {
  try {
    const res = await fetch('/api/overview');
    if (!res.ok) throw new Error('Failed to fetch overview data');
    const data = await res.json();

    // Populate KPIs
    const kpis = data.kpis;
    document.getElementById('kpi-total-batches').textContent = kpis.total_batches.toLocaleString();
    document.getElementById('kpi-total-prod').textContent = `${(kpis.total_production_kg / 1000).toFixed(1)}k kg total processed`;
    document.getElementById('kpi-avg-waste').textContent = `${kpis.average_waste_percentage.toFixed(2)}%`;
    document.getElementById('kpi-total-waste').textContent = `${kpis.total_waste_kg.toLocaleString()} kg total waste`;
    document.getElementById('kpi-normal-count').textContent = kpis.normal_count.toLocaleString();
    document.getElementById('kpi-warning-count').textContent = kpis.warning_count.toLocaleString();
    document.getElementById('kpi-high-risk-count').textContent = kpis.high_risk_count.toLocaleString();

    // Urgent Alerts Banner
    const alertBanner = document.getElementById('high-risk-alert-banner');
    if (kpis.high_risk_count > 0 && data.recent_high_risk_alerts?.length > 0) {
      alertBanner.classList.remove('hidden');
      const recent = data.recent_high_risk_alerts[0];
      document.getElementById('alert-banner-text').textContent = 
        `${kpis.high_risk_count} batches flagged HIGH RISK. Latest Batch: ${recent.batch_id} on ${recent.machine_id} (${recent.waste_percentage}% waste).`;
    } else {
      alertBanner.classList.add('hidden');
    }

    // Machine Benchmarks Box
    if (data.lowest_waste_machine) {
      document.getElementById('bench-lowest-machine').textContent = 
        `${data.lowest_waste_machine.machine_id} (${data.lowest_waste_machine.average_waste_pct}%)`;
    }
    if (data.highest_waste_machine) {
      document.getElementById('bench-highest-machine').textContent = 
        `${data.highest_waste_machine.machine_id} (${data.highest_waste_machine.average_waste_pct}%)`;
    }

    // High-Risk Fabrics
    const fabricsContainer = document.getElementById('high-risk-fabrics-list');
    if (fabricsContainer && data.high_risk_fabrics) {
      if (data.high_risk_fabrics.length === 0) {
        fabricsContainer.innerHTML = '<span class="text-muted text-sm">No fabrics currently exceed threshold.</span>';
      } else {
        fabricsContainer.innerHTML = data.high_risk_fabrics.map(f => `
          <span class="tag tag-danger">${f.fabric_type} (${f.average_waste_pct}%)</span>
        `).join('');
      }
    }

    // Load Root-Cause AI Spotlight Summary
    try {
      const rcaRes = await fetch('/api/root-cause/plant-analysis');
      if (rcaRes.ok) {
        const rcaData = await rcaRes.json();
        if (rcaData.pareto_causes && rcaData.pareto_causes.length > 0) {
          document.getElementById('bench-rc-top-cause').textContent = rcaData.pareto_causes[0].title;
        } else {
          document.getElementById('bench-rc-top-cause').textContent = 'All Batches Nominal';
        }
        const savingsKg = rcaData.total_potential_waste_kg_saved || 0;
        document.getElementById('bench-rc-savings').textContent = `${savingsKg.toLocaleString()} kg`;
      }
    } catch (rcaErr) {
      console.warn('Could not load overview RCA summary:', rcaErr);
    }

    // Render Charts and Tables
    renderRiskDonutChart(kpis.normal_count, kpis.warning_count, kpis.high_risk_count);
    loadMachineWasteChart();
    loadWasteCausesPreventionTable();
    loadOverviewRecentBatches();

  } catch (err) {
    console.error('Error loading overview data:', err);
  }
}

async function loadWasteCausesPreventionTable() {
  const tbody = document.getElementById('waste-causes-tbody');
  if (!tbody) return;

  try {
    const res = await fetch('/api/analytics/waste-causes-prevention');
    if (!res.ok) throw new Error('Failed to fetch waste causes');
    const data = await res.json();
    const rows = data.summary || [];

    if (rows.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-muted">All recorded production batches are within optimal operating tolerances.</td></tr>';
      return;
    }

    tbody.innerHTML = rows.map(r => {
      let riskBadgeClass = 'badge-normal';
      if (r.risk_level === 'HIGH RISK') riskBadgeClass = 'badge-danger';
      else if (r.risk_level === 'WARNING') riskBadgeClass = 'badge-warning';

      return `
        <tr>
          <td class="font-bold">
            <i class="fa-solid ${r.icon || 'fa-triangle-exclamation'} mr-2 text-cyan"></i>
            ${escapeHtml(r.cause_name)}
          </td>
          <td><span class="badge badge-subtle text-xs">${escapeHtml(r.category)}</span></td>
          <td class="text-right font-bold">${r.affected_batches.toLocaleString()}</td>
          <td class="text-right font-bold ${r.avg_waste_pct > 6 ? 'text-danger' : (r.avg_waste_pct > 4 ? 'text-warning' : 'text-normal')}">${r.avg_waste_pct.toFixed(2)}%</td>
          <td>
            <div class="flex-center-y gap-1 text-sm text-muted">
              <i class="fa-solid fa-arrow-right text-cyan text-xs"></i>
              <span>${escapeHtml(r.preventive_action)}</span>
            </div>
          </td>
          <td>
            <span class="badge ${riskBadgeClass}">${escapeHtml(r.risk_level)}</span>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading waste causes prevention table:', err);
    tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-danger">Failed to load waste causes analytics.</td></tr>';
  }
}

function renderRiskDonutChart(normal, warning, highRisk) {
  const ctx = document.getElementById('chart-risk-donut');
  if (!ctx) return;

  if (state.charts['riskDonut']) {
    state.charts['riskDonut'].destroy();
  }

  const total = normal + warning + highRisk || 1;

  state.charts['riskDonut'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Normal', 'Warning', 'High Risk'],
      datasets: [{
        data: [normal, warning, highRisk],
        backgroundColor: ['#10B981', '#F59E0B', '#EF4444'],
        borderWidth: 2,
        borderColor: '#111827',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '72%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: { color: '#9CA3AF', boxWidth: 12, font: { size: 12 } }
        },
        tooltip: {
          callbacks: {
            label: function(item) {
              const val = item.raw || 0;
              const pct = ((val / total) * 100).toFixed(1);
              return ` ${item.label}: ${val} batches (${pct}%)`;
            }
          }
        }
      }
    }
  });
}

async function loadMachineWasteChart() {
  try {
    const res = await fetch('/api/analytics/machines');
    if (!res.ok) return;
    const data = await res.json();
    const machines = data.machines || [];

    const ctx = document.getElementById('chart-machine-waste');
    if (!ctx) return;

    if (state.charts['machineWaste']) {
      state.charts['machineWaste'].destroy();
    }

    const labels = machines.map(m => m.machine_id);
    const wasteValues = machines.map(m => m.average_waste_pct);
    const bgColors = machines.map(m => m.maintenance_status === 'OVERDUE' ? '#EF4444' : '#3B82F6');

    // Correlation benchmark text
    if (document.getElementById('bench-age-corr')) {
      document.getElementById('bench-age-corr').textContent = 
        `${data.age_waste_correlation > 0 ? '+' : ''}${data.age_waste_correlation} Correlation`;
    }

    state.charts['machineWaste'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Avg Waste %',
          data: wasteValues,
          backgroundColor: bgColors,
          borderRadius: 6,
          borderSkipped: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#9CA3AF', callback: val => val + '%' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#9CA3AF' }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });

  } catch (err) {
    console.error('Error loading machine waste chart:', err);
  }
}

async function loadOverviewRecentBatches() {
  try {
    const res = await fetch('/api/batches?limit=6&offset=0');
    if (!res.ok) return;
    const data = await res.json();
    const batches = data.batches || [];

    const tbody = document.getElementById('overview-recent-tbody');
    if (!tbody) return;

    if (batches.length === 0) {
      tbody.innerHTML = '<tr><td colspan="11" class="text-center py-4 text-muted">No batches recorded yet.</td></tr>';
      return;
    }

    tbody.innerHTML = batches.map(b => `
      <tr>
        <td class="font-bold">${b.batch_id}</td>
        <td><span class="badge badge-subtle">${b.machine_id}</span></td>
        <td>${b.fabric_type}</td>
        <td>${b.shift}</td>
        <td>${b.operator}</td>
        <td>${b.total_production?.toLocaleString()} kg</td>
        <td>${b.waste_quantity?.toFixed(1)} kg</td>
        <td class="font-bold font-accent">${b.waste_percentage?.toFixed(2)}%</td>
        <td>${renderRiskBadge(b.risk_level)}</td>
        <td><strong>${b.risk_score?.toFixed(0)}</strong>/100</td>
        <td>
          <button class="btn btn-sm btn-secondary" onclick="inspectBatch('${b.batch_id}')">
            <i class="fa-solid fa-eye"></i>
          </button>
        </td>
      </tr>
    `).join('');

  } catch (err) {
    console.error('Error loading overview batches preview:', err);
  }
}


// ------------------------------------------------------------
// ------------------------------------------------------------
// ------------------------------------------------------------
// TAB 2: LIVE PREDICTOR & AFTER-PREDICTION WHAT-IF SIMULATOR
// ------------------------------------------------------------

// Sub-Tab Navigation Switcher
function initPredictorSubTabs() {
  document.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const subTabId = btn.getAttribute('data-subtab');
      if (subTabId) {
        switchPredictorSubTab(subTabId);
      }
    });
  });
}

function switchPredictorSubTab(subTabId) {
  state.predictorSubTab = subTabId;
  document.querySelectorAll('.sub-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-subtab') === subTabId);
  });
  document.querySelectorAll('.sub-tab-pane').forEach(pane => {
    pane.classList.toggle('active', pane.id === subTabId);
  });

  if (subTabId === 'subtab-after-prediction') {
    if (!state.lastAfterPrediction) {
      runAfterPrediction(false);
    }
  }
}

// ------------------------------------------------------------
// SUB-TAB 1: EXPECTED WASTE PREDICTION
// ------------------------------------------------------------
function initPredictorForm() {
  const form = document.getElementById('predict-form');
  const totalProdInput = document.getElementById('p-total-prod');
  const wasteQtyInput = document.getElementById('p-waste-qty');
  const computedDisplay = document.getElementById('p-computed-waste-display');

  // Live Waste % calculation listener
  function updateLiveWasteDisplay() {
    const prod = parseFloat(totalProdInput?.value) || 0;
    const wasteStr = wasteQtyInput?.value?.trim();
    const waste = wasteStr !== '' ? parseFloat(wasteStr) : null;
    
    if (prod <= 0) {
      computedDisplay.textContent = 'Invalid (Production Quantity = 0)';
      computedDisplay.style.color = 'var(--risk-danger)';
    } else if (waste === null || isNaN(waste)) {
      computedDisplay.textContent = 'Pre-Production Forecast Mode (Expected waste will be predicted by AI)';
      computedDisplay.style.color = 'var(--cyan)';
    } else {
      const pct = (waste / prod) * 100;
      computedDisplay.textContent = `Actual Waste Entered: ${pct.toFixed(2)}% (${waste.toFixed(1)} kg / ${prod.toFixed(0)} kg)`;
      computedDisplay.style.color = pct > 6.5 ? 'var(--risk-danger)' : (pct > 4.5 ? 'var(--risk-warning)' : 'var(--cyan)');
    }
  }

  totalProdInput?.addEventListener('input', updateLiveWasteDisplay);
  wasteQtyInput?.addEventListener('input', updateLiveWasteDisplay);

  // Initial display update
  updateLiveWasteDisplay();

  // Form Submit
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await runSinglePrediction(false);
  });

  // Save button
  document.getElementById('btn-save-predicted-batch')?.addEventListener('click', async () => {
    if (!state.lastPrediction) {
      showToast('Please predict expected waste first before saving.', 'error');
      return;
    }
    await runSinglePrediction(true);
  });

  // Generate Finalized Report button
  document.getElementById('btn-open-batch-report')?.addEventListener('click', async () => {
    if (!state.lastPrediction) {
      await runSinglePrediction(false);
    }
    if (state.lastPrediction) {
      openBatchFinalizedReport(state.lastPrediction);
    }
  });

  // Preset Buttons for Expected Waste
  document.querySelectorAll('#subtab-expected-waste .btn-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      const preset = PRESETS[presetKey];
      if (preset) {
        loadPresetIntoForm(preset);
        runSinglePrediction(false);
      }
    });
  });
}

function loadPresetIntoForm(preset) {
  document.getElementById('p-batch-id').value = preset.batch_id;
  document.getElementById('p-machine-id').value = preset.machine_id;
  document.getElementById('p-fabric-type').value = preset.fabric_type;
  document.getElementById('p-shift').value = preset.shift;
  document.getElementById('p-operator').value = preset.operator;
  document.getElementById('p-total-prod').value = preset.total_production;
  document.getElementById('p-waste-qty').value = preset.waste_quantity !== undefined && preset.waste_quantity !== null ? preset.waste_quantity : '';
  document.getElementById('p-speed').value = preset.production_speed;
  document.getElementById('p-machine-age').value = preset.machine_age;
  document.getElementById('p-maint-date').value = preset.last_maintenance_date;
  document.getElementById('p-humidity').value = preset.humidity !== null && preset.humidity !== undefined ? preset.humidity : '';
  document.getElementById('p-temperature').value = preset.temperature;

  // Trigger input update
  document.getElementById('p-total-prod').dispatchEvent(new Event('input'));
}

async function runSinglePrediction(saveToDb = false) {
  const wasteQtyStr = document.getElementById('p-waste-qty')?.value?.trim();
  const batchData = {
    batch_id: document.getElementById('p-batch-id').value,
    machine_id: document.getElementById('p-machine-id').value,
    fabric_type: document.getElementById('p-fabric-type').value,
    shift: document.getElementById('p-shift').value,
    operator: document.getElementById('p-operator').value,
    total_production: parseFloat(document.getElementById('p-total-prod').value),
    waste_quantity: wasteQtyStr !== '' ? parseFloat(wasteQtyStr) : null,
    production_speed: parseFloat(document.getElementById('p-speed').value),
    machine_age: parseFloat(document.getElementById('p-machine-age').value),
    last_maintenance_date: document.getElementById('p-maint-date').value,
    humidity: document.getElementById('p-humidity').value !== '' ? parseFloat(document.getElementById('p-humidity').value) : null,
    temperature: parseFloat(document.getElementById('p-temperature').value)
  };

  try {
    const url = `/api/predict-expected?save=${saveToDb}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batchData)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Prediction failed');
    }

    const result = await res.json();
    state.lastPrediction = result;

    renderPredictionResult(result);

    if (saveToDb) {
      showToast(`Batch ${result.batch_id} saved to database!`, 'success');
      loadOverviewData(false);
    }

  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

function renderPredictionResult(result) {
  const riskScore = result.risk_score || 0;
  const riskLevel = result.risk_level || 'NORMAL';
  const confidence = result.confidence_score || 95;

  // 1. EXPECTED WASTE HERO METRICS
  const expWastePctEl = document.getElementById('res-expected-waste-pct');
  if (expWastePctEl) {
    if (result.expected_waste_percentage != null) {
      expWastePctEl.textContent = `${result.expected_waste_percentage.toFixed(1)}%`;
      expWastePctEl.className = `stat-value font-accent ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-cyan')}`;
    } else {
      expWastePctEl.textContent = '--';
    }
  }

  const likelyPctRangeEl = document.getElementById('res-likely-pct-range');
  if (likelyPctRangeEl) {
    if (result.likely_range_pct) {
      likelyPctRangeEl.textContent = `Likely: ${result.likely_range_pct.display || (result.likely_range_pct.min + '%–' + result.likely_range_pct.max + '%')}`;
    } else {
      likelyPctRangeEl.textContent = 'Likely Range: N/A';
    }
  }

  const expWasteKgEl = document.getElementById('res-expected-waste-kg');
  if (expWasteKgEl) {
    if (result.expected_waste_kg != null) {
      expWasteKgEl.textContent = `${result.expected_waste_kg.toFixed(0)} kg`;
    } else {
      expWasteKgEl.textContent = '--';
    }
  }

  const likelyKgRangeEl = document.getElementById('res-likely-kg-range');
  if (likelyKgRangeEl) {
    if (result.likely_range_kg) {
      likelyKgRangeEl.textContent = `Likely: ${result.likely_range_kg.display || (result.likely_range_kg.min + '–' + result.likely_range_kg.max + ' kg')}`;
    } else {
      likelyKgRangeEl.textContent = 'Likely: N/A';
    }
  }

  const expGoodProdEl = document.getElementById('res-expected-good-prod');
  if (expGoodProdEl) {
    if (result.expected_good_production_kg != null) {
      expGoodProdEl.textContent = `${result.expected_good_production_kg.toLocaleString()} kg`;
    } else {
      expGoodProdEl.textContent = '--';
    }
  }

  // ----------------------------------------------------
  // DYNAMIC & REACTIVE RISK LEVEL HERO CARD
  // ----------------------------------------------------
  const badge = document.getElementById('res-risk-badge');
  const meterFill = document.getElementById('res-risk-meter-fill');
  const riskStatusTag = document.getElementById('res-risk-status-tag');
  
  if (badge) {
    let badgeClass = 'badge-normal';
    let iconClass = 'fa-solid fa-circle-check';
    let meterColor = 'var(--risk-normal)';
    
    if (riskLevel === 'WARNING') {
      badgeClass = 'badge-warning';
      iconClass = 'fa-solid fa-triangle-exclamation';
      meterColor = 'var(--risk-warning)';
    } else if (riskLevel === 'HIGH RISK') {
      badgeClass = 'badge-danger';
      iconClass = 'fa-solid fa-triangle-exclamation';
      meterColor = 'var(--risk-danger)';
    } else if (riskLevel === 'INVALID') {
      badgeClass = 'badge-invalid';
      iconClass = 'fa-solid fa-ban';
      meterColor = 'rgba(156, 163, 175, 0.4)';
    }
    
    badge.className = `risk-badge-large ${badgeClass}`;
    badge.innerHTML = `<i class="${iconClass}"></i> <span id="res-risk-text">${escapeHtml(riskLevel)}</span>`;
    
    if (meterFill) {
      meterFill.style.width = `${Math.min(100, Math.max(0, riskScore))}%`;
      meterFill.style.background = meterColor;
    }
    
    if (riskStatusTag) {
      riskStatusTag.textContent = riskLevel === 'INVALID' ? 'Invalid Telemetry' : (riskLevel === 'HIGH RISK' ? 'Elevated Hazard' : (riskLevel === 'WARNING' ? 'Caution Needed' : 'Nominal Safe'));
      riskStatusTag.className = `text-xs font-bold ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-green')}`;
    }
  }

  const riskScoreSub = document.getElementById('res-risk-score-sub');
  if (riskScoreSub) {
    riskScoreSub.textContent = `Risk Score: ${riskScore.toFixed(0)}/100`;
  }

  // Interactive Click to scroll & highlight Risk Breakdown
  const riskCardContainer = document.getElementById('res-risk-card-container');
  if (riskCardContainer && !riskCardContainer._hasClickListener) {
    riskCardContainer._hasClickListener = true;
    riskCardContainer.addEventListener('click', () => {
      const target = document.getElementById('section-factor-breakdown') || document.getElementById('panel-why-at-risk');
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        target.style.boxShadow = '0 0 25px rgba(6, 182, 212, 0.4)';
        setTimeout(() => { target.style.boxShadow = ''; }, 1800);
      }
    });
  }

  // Confidence Badge
  const confBadge = document.getElementById('res-confidence-badge');
  if (confBadge) {
    confBadge.textContent = `Confidence: ${confidence.toFixed(0)}%`;
    if (riskLevel === 'INVALID') {
      confBadge.className = 'badge badge-invalid';
    } else {
      confBadge.className = result.is_new_machine ? 'badge badge-warning' : 'badge badge-subtle';
    }
  }

  // 2. MULTI-LEVEL HISTORICAL COMPARISON MATRIX
  const comp = result.historical_comparison || {};
  const compSummaryEl = document.getElementById('res-hist-comparison-summary');
  if (compSummaryEl) {
    compSummaryEl.textContent = comp.comparison_summary || 'Historical baselines evaluated for factory, machine, and fabric profiles.';
  }
  const fAvgEl = document.getElementById('hist-comp-factory');
  if (fAvgEl) fAvgEl.textContent = `${comp.factory_average_pct != null ? comp.factory_average_pct.toFixed(1) : '4.0'}%`;
  const mAvgEl = document.getElementById('hist-comp-machine');
  if (mAvgEl) mAvgEl.textContent = `${comp.machine_average_pct != null ? comp.machine_average_pct.toFixed(1) : '4.2'}%`;
  const fabAvgEl = document.getElementById('hist-comp-fabric');
  if (fabAvgEl) fabAvgEl.textContent = `${comp.fabric_average_pct != null ? comp.fabric_average_pct.toFixed(1) : '5.1'}%`;
  const comboAvgEl = document.getElementById('hist-comp-combo');
  if (comboAvgEl) comboAvgEl.textContent = `${comp.machine_fabric_combination_avg_pct != null ? comp.machine_fabric_combination_avg_pct.toFixed(1) : '4.6'}%`;
  const shiftAvgEl = document.getElementById('hist-comp-shift');
  if (shiftAvgEl) shiftAvgEl.textContent = `${comp.shift_average_pct != null ? comp.shift_average_pct.toFixed(1) : '3.9'}%`;

  // 3. EXPECTED VS ACTUAL COMPARISON TABLE
  const evaPanel = document.getElementById('panel-expected-vs-actual');
  const eva = result.expected_vs_actual;
  if (evaPanel) {
    if (eva && eva.has_actual) {
      evaPanel.classList.remove('hidden');
      document.getElementById('eva-expected-pct').textContent = `${eva.expected_waste_pct?.toFixed(1)}%`;
      document.getElementById('eva-actual-pct').textContent = `${eva.actual_waste_pct?.toFixed(1)}%`;
      document.getElementById('eva-expected-kg').textContent = `${eva.expected_waste_kg?.toFixed(1)} kg`;
      document.getElementById('eva-actual-kg').textContent = `${eva.actual_waste_kg?.toFixed(1)} kg`;
      document.getElementById('eva-diff-kg').textContent = eva.difference_sign || `${eva.difference_kg?.toFixed(1)} kg`;
      document.getElementById('eva-abs-error').textContent = `${eva.absolute_error_kg?.toFixed(1)} kg`;
      document.getElementById('eva-accuracy-pct').textContent = `${eva.prediction_accuracy_pct?.toFixed(1)}%`;
    } else {
      evaPanel.classList.add('hidden');
    }
  }

  // 4. REASON CARDS (WHY IS THIS WASTE EXPECTED?)
  const reasonCardsContainer = document.getElementById('res-reason-cards-container');
  const reasonCards = result.reason_cards || (result.root_cause_analysis && result.root_cause_analysis.reason_cards) || [];
  if (reasonCardsContainer) {
    if (reasonCards.length > 0) {
      reasonCardsContainer.innerHTML = reasonCards.map((rc, idx) => `
        <div class="reason-card card-severity-${(rc.severity || 'warning').toLowerCase()}">
          <div class="reason-card-header">
            <div class="reason-title">
              <i class="fa-solid ${rc.icon || 'fa-triangle-exclamation'}"></i>
              <span>${escapeHtml(rc.title || `Reason ${idx + 1}`)}</span>
            </div>
            <span class="badge badge-${rc.badge_color || 'warning'}">${escapeHtml(rc.severity || 'WARNING')}</span>
          </div>
          <div class="observed-benchmark-grid">
            <div class="stat-chip">
              <span class="stat-chip-label">Observed Telemetry</span>
              <div class="stat-chip-val text-${rc.badge_color || 'warning'}">${escapeHtml(rc.observed || 'N/A')}</div>
            </div>
            <div class="stat-chip">
              <span class="stat-chip-label">Normal Benchmark</span>
              <div class="stat-chip-val text-muted">${escapeHtml(rc.benchmark || 'Nominal Range')}</div>
            </div>
          </div>
          <div class="reason-impact-box">
            <strong>Impact:</strong> ${escapeHtml(rc.impact || rc.evidence_text || 'Potential material loss and defect escalation.')}
          </div>
        </div>
      `).join('');
    } else if (result.reasons && result.reasons.length > 0) {
      reasonCardsContainer.innerHTML = result.reasons.map((r, i) => `
        <div class="reason-card card-severity-nominal">
          <div class="reason-card-header">
            <div class="reason-title"><i class="fa-solid fa-circle-check text-normal"></i> <span>Reason ${i + 1}</span></div>
            <span class="badge badge-normal">NOMINAL</span>
          </div>
          <p class="text-sm text-muted">${escapeHtml(r)}</p>
        </div>
      `).join('');
    } else {
      reasonCardsContainer.innerHTML = '<div class="empty-state-notice">All operational telemetry parameters are within validated baseline limits.</div>';
    }
  }

  // 5. PREVENTIVE SOLUTIONS (HOW CAN THE EXPECTED WASTE BE REDUCED?)
  const solutionsContainer = document.getElementById('res-preventive-solutions-container');
  const solutions = result.preventive_solutions || (result.root_cause_analysis && result.root_cause_analysis.preventive_solutions) || [];
  if (solutionsContainer) {
    if (solutions.length > 0) {
      solutionsContainer.innerHTML = solutions.map((sol, idx) => `
        <div class="solution-card">
          <div class="solution-icon-box">
            <i class="fa-solid ${sol.icon || 'fa-shield-halved'}"></i>
          </div>
          <div class="solution-card-body">
            <div class="solution-title-row">
              <h5 class="solution-title">${escapeHtml(sol.title || `Solution ${idx + 1}`)}</h5>
              <span class="badge badge-subtle text-xs">${escapeHtml(sol.priority || 'MEDIUM')} PRIORITY</span>
            </div>
            <p class="solution-text">${escapeHtml(sol.solution)}</p>
          </div>
        </div>
      `).join('');
    } else if (result.actions && result.actions.length > 0) {
      solutionsContainer.innerHTML = result.actions.map((act, i) => `
        <div class="solution-card">
          <div class="solution-icon-box"><i class="fa-solid fa-check text-cyan"></i></div>
          <div class="solution-card-body">
            <h5 class="solution-title">Standard Preventive Action ${i + 1}</h5>
            <p class="solution-text">${escapeHtml(act)}</p>
          </div>
        </div>
      `).join('');
    } else {
      solutionsContainer.innerHTML = '<div class="empty-state-notice">Maintain nominal operating standards and routine inspections.</div>';
    }
  }

  // 6. RECOMMENDED ACTION PLAN (Inspect -> Adjust -> Maintain -> Monitor)
  const actionPlan = result.recommended_action_plan || (result.root_cause_analysis && result.root_cause_analysis.recommended_action_plan) || {};
  const actionSummaryEl = document.getElementById('res-action-summary');
  const actionStepsEl = document.getElementById('res-action-steps-list');
  const actionBox = document.getElementById('res-action-box');
  if (actionPlan && actionSummaryEl && actionStepsEl) {
    actionSummaryEl.textContent = actionPlan.summary || (riskLevel === 'HIGH RISK' ? 'Multiple factors indicate a high probability of abnormal waste. Immediate inspection is recommended before continuing production.' : (riskLevel === 'WARNING' ? 'The batch shows moderate risk factors. Review the highlighted conditions before continuing large-scale production.' : 'Production conditions are within the expected range. Continue monitoring waste percentage.'));
    if (actionBox) {
      actionBox.className = `risk-action-box action-box-${(actionPlan.risk_level || 'normal').toLowerCase().replace(' ', '-')}`;
    }
    const steps = actionPlan.steps || result.actions || [
      'Continue production according to standard operational schedule.',
      'Monitor machine performance and tension telemetry.',
      'Maintain standard scheduled maintenance timeline.'
    ];
    actionStepsEl.innerHTML = steps.map(step => `<li>${escapeHtml(step)}</li>`).join('');
  }

  // 7. FACTOR CONTRIBUTIONS BARS
  const factors = result.factor_contributions || {};
  updateFactorBar('bar-factor-waste', 'factor-waste-val', factors.waste_deviation || 0);
  updateFactorBar('bar-factor-maint', 'factor-maint-val', factors.maintenance_health || 0);
  updateFactorBar('bar-factor-speed', 'factor-speed-val', factors.speed_stress || 0);
  updateFactorBar('bar-factor-env', 'factor-env-val', factors.environment_age || 0);

  // ROOT-CAUSE AI PRIMARY CAUSE CALLOUT
  const rcaCallout = document.getElementById('pred-rca-container');
  if (rcaCallout) {
    const rca = result.root_cause_analysis;
    if (rca && rca.primary_cause && rca.primary_cause.is_active) {
      const pc = rca.primary_cause;
      rcaCallout.classList.remove('hidden');
      document.getElementById('pred-rca-pct').textContent = `${pc.attribution_pct || 0}% Attribution`;
      document.getElementById('pred-rca-title').textContent = pc.title;
      document.getElementById('pred-rca-explanation').textContent = pc.explanation;
      const sev = rca.severity || 'HIGH';
      document.getElementById('pred-rca-badge').textContent = `${sev} ROOT CAUSE`;
      document.getElementById('pred-rca-badge').className = `badge ${sev === 'CRITICAL' ? 'badge-danger' : (sev === 'HIGH' ? 'badge-warning' : 'badge-normal')}`;
    } else {
      rcaCallout.classList.add('hidden');
    }
  }
}

function updateFactorBar(barId, labelId, val) {
  const bar = document.getElementById(barId);
  const lbl = document.getElementById(labelId);
  if (bar) bar.style.width = Math.min(100, Math.max(0, val)) + '%';
  if (lbl) lbl.textContent = Math.round(val) + '%';
}


// ------------------------------------------------------------
// SUB-TAB 2: AI-RISK PREDICTOR WITH AFTER PREDICTION
// ------------------------------------------------------------
function initAfterPredictionSubTab() {
  const form = document.getElementById('after-pred-form');
  const totalProdInput = document.getElementById('ap-total-prod');
  const wasteQtyInput = document.getElementById('ap-waste-qty');
  const liveCalc = document.getElementById('ap-computed-waste-display');

  function updateLiveCalc() {
    const prod = parseFloat(totalProdInput?.value) || 0;
    const waste = parseFloat(wasteQtyInput?.value) || 0;
    if (prod > 0 && waste >= 0) {
      const pct = (waste / prod) * 100;
      liveCalc.textContent = `${pct.toFixed(2)}% (${waste.toFixed(1)} kg / ${prod.toFixed(0)} kg)`;
      liveCalc.style.color = pct > 6.5 ? 'var(--risk-danger)' : (pct > 4.5 ? 'var(--risk-warning)' : 'var(--cyan)');
    } else {
      liveCalc.textContent = 'Enter production & waste quantities';
      liveCalc.style.color = 'var(--text-muted)';
    }
  }

  totalProdInput?.addEventListener('input', updateLiveCalc);
  wasteQtyInput?.addEventListener('input', updateLiveCalc);
  updateLiveCalc();

  // Form Submit
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    await runAfterPrediction(false);
  });

  // Preset Buttons
  document.querySelectorAll('.btn-after-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      const presetKey = btn.getAttribute('data-preset');
      const preset = PRESETS[presetKey];
      if (preset) {
        loadAfterPredictionPreset(preset);
        runAfterPrediction(false);
      }
    });
  });

  // Real-time Simulator Sliders
  const speedSlider = document.getElementById('slider-ap-speed');
  const humiditySlider = document.getElementById('slider-ap-humidity');
  const maintSlider = document.getElementById('slider-ap-maint');
  const tempSlider = document.getElementById('slider-ap-temp');

  let simDebounceTimer = null;
  function onSliderInput() {
    document.getElementById('lbl-ap-speed').textContent = `${speedSlider.value} RPM`;
    document.getElementById('lbl-ap-humidity').textContent = `${humiditySlider.value}% RH`;
    document.getElementById('lbl-ap-maint').textContent = `${maintSlider.value} Days`;
    document.getElementById('lbl-ap-temp').textContent = `${parseFloat(tempSlider.value).toFixed(1)}°C`;

    clearTimeout(simDebounceTimer);
    simDebounceTimer = setTimeout(() => {
      updateAfterPredictionSimulation();
    }, 60);
  }

  speedSlider?.addEventListener('input', onSliderInput);
  humiditySlider?.addEventListener('input', onSliderInput);
  maintSlider?.addEventListener('input', onSliderInput);
  tempSlider?.addEventListener('input', onSliderInput);

  // Auto-Tune Safe Levers Button
  document.getElementById('btn-ap-auto-tune')?.addEventListener('click', () => {
    autoTuneAfterPredictionLevers();
  });

  // Reset Sliders Button
  document.getElementById('btn-ap-reset-sliders')?.addEventListener('click', () => {
    resetAfterPredictionSliders();
  });

  // Apply Tuned Levers to Form
  document.getElementById('btn-ap-apply-to-form')?.addEventListener('click', () => {
    applyAfterPredictionLeversToForm();
  });

  // Save Batch to Database
  document.getElementById('btn-ap-save-batch')?.addEventListener('click', async () => {
    await saveAfterPredictionBatch();
  });

  // Generate Audit Report
  document.getElementById('btn-ap-open-report')?.addEventListener('click', () => {
    if (state.lastAfterPrediction) {
      openBatchFinalizedReport(state.lastAfterPrediction);
    } else {
      showToast('Please run risk assessment first before generating report.', 'info');
    }
  });
}

function loadAfterPredictionPreset(preset) {
  document.getElementById('ap-batch-id').value = preset.batch_id;
  document.getElementById('ap-machine-id').value = preset.machine_id;
  document.getElementById('ap-fabric-type').value = preset.fabric_type;
  document.getElementById('ap-shift').value = preset.shift;
  document.getElementById('ap-operator').value = preset.operator;
  document.getElementById('ap-total-prod').value = preset.total_production;
  document.getElementById('ap-waste-qty').value = preset.waste_quantity !== undefined && preset.waste_quantity !== null && preset.waste_quantity !== '' ? preset.waste_quantity : Math.round(preset.total_production * 0.05);
  document.getElementById('ap-speed').value = preset.production_speed;
  document.getElementById('ap-machine-age').value = preset.machine_age;
  document.getElementById('ap-maint-date').value = preset.last_maintenance_date;
  document.getElementById('ap-humidity').value = preset.humidity !== null && preset.humidity !== undefined ? preset.humidity : 55;
  document.getElementById('ap-temperature').value = preset.temperature;

  // Trigger input
  document.getElementById('ap-total-prod').dispatchEvent(new Event('input'));
}

async function runAfterPrediction(saveToDb = false) {
  const batchData = {
    batch_id: document.getElementById('ap-batch-id').value,
    machine_id: document.getElementById('ap-machine-id').value,
    fabric_type: document.getElementById('ap-fabric-type').value,
    shift: document.getElementById('ap-shift').value,
    operator: document.getElementById('ap-operator').value,
    total_production: parseFloat(document.getElementById('ap-total-prod').value) || 1000,
    waste_quantity: parseFloat(document.getElementById('ap-waste-qty').value) || 0,
    production_speed: parseFloat(document.getElementById('ap-speed').value) || 800,
    machine_age: parseFloat(document.getElementById('ap-machine-age').value) || 3.0,
    last_maintenance_date: document.getElementById('ap-maint-date').value,
    humidity: document.getElementById('ap-humidity').value !== '' ? parseFloat(document.getElementById('ap-humidity').value) : 55,
    temperature: parseFloat(document.getElementById('ap-temperature').value) || 25.0
  };

  try {
    const url = `/api/predict?save=${saveToDb}`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batchData)
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || 'Risk assessment failed');
    }

    const result = await res.json();
    state.lastAfterPrediction = result;
    state.afterPredictionBatch = batchData;

    renderInitialAfterPredictionRisk(result);

    // Synchronize simulator sliders to match the newly submitted batch
    const speedSlider = document.getElementById('slider-ap-speed');
    const humiditySlider = document.getElementById('slider-ap-humidity');
    const maintSlider = document.getElementById('slider-ap-maint');
    const tempSlider = document.getElementById('slider-ap-temp');

    if (speedSlider) speedSlider.value = result.production_speed || 800;
    if (humiditySlider) humiditySlider.value = result.humidity || 55;
    if (maintSlider) maintSlider.value = result.maintenance_age_days != null ? result.maintenance_age_days : 30;
    if (tempSlider) tempSlider.value = result.temperature || 25.0;

    document.getElementById('lbl-ap-speed').textContent = `${speedSlider?.value || 800} RPM`;
    document.getElementById('lbl-ap-humidity').textContent = `${humiditySlider?.value || 55}% RH`;
    document.getElementById('lbl-ap-maint').textContent = `${maintSlider?.value || 30} Days`;
    document.getElementById('lbl-ap-temp').textContent = `${parseFloat(tempSlider?.value || 25).toFixed(1)}°C`;

    // Run simulation
    await updateAfterPredictionSimulation();

    if (saveToDb) {
      showToast(`Batch ${result.batch_id} saved to database!`, 'success');
      loadOverviewData(false);
    }

  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

function renderInitialAfterPredictionRisk(result) {
  const riskLevel = result.risk_level || 'NORMAL';
  const riskScore = result.risk_score || 0;
  const wastePct = result.waste_percentage != null ? result.waste_percentage : 0.0;
  const wasteKg = result.waste_quantity != null ? result.waste_quantity : 0.0;

  // Initial Assessment Hero Card
  const initBadge = document.getElementById('ap-initial-risk-badge');
  if (initBadge) {
    initBadge.textContent = riskLevel;
    initBadge.className = `badge ${riskLevel === 'HIGH RISK' ? 'badge-danger' : (riskLevel === 'WARNING' ? 'badge-warning' : 'badge-normal')}`;
  }

  const initWasteEl = document.getElementById('ap-init-waste-pct');
  if (initWasteEl) {
    initWasteEl.textContent = `${wastePct.toFixed(2)}%`;
    initWasteEl.className = `font-bold font-accent ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-cyan')}`;
  }

  const initWasteKgEl = document.getElementById('ap-init-waste-kg');
  if (initWasteKgEl) {
    initWasteKgEl.textContent = `${wasteKg.toFixed(1)} kg total waste`;
  }

  const initScoreEl = document.getElementById('ap-init-risk-score');
  if (initScoreEl) {
    initScoreEl.textContent = `${riskScore.toFixed(0)}/100`;
    initScoreEl.className = `font-bold ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-green')}`;
  }

  const initAnomalyEl = document.getElementById('ap-init-anomaly-tag');
  if (initAnomalyEl) {
    initAnomalyEl.textContent = result.is_abnormal ? 'Abnormal Deviation' : 'Nominal Safe Range';
    initAnomalyEl.className = `text-xs ${result.is_abnormal ? 'text-danger font-bold' : 'text-green'}`;
  }

  const rca = result.root_cause_analysis;
  const primaryDriver = (rca && rca.primary_cause && rca.primary_cause.title) || (result.reasons && result.reasons[0]) || 'Operational Baseline Limits';
  const explanation = (rca && rca.primary_cause && rca.primary_cause.explanation) || 'Parameters evaluated against standard manufacturing baselines.';
  
  const driverEl = document.getElementById('ap-init-primary-driver');
  if (driverEl) driverEl.textContent = primaryDriver;

  const explEl = document.getElementById('ap-init-explanation');
  if (explEl) explEl.textContent = explanation;

  const confEl = document.getElementById('ap-init-confidence');
  if (confEl) confEl.textContent = `${(result.confidence_score || 95).toFixed(0)}% Confidence`;

  // Before Column in Comparison
  const beforeTag = document.getElementById('ap-before-risk-tag');
  if (beforeTag) {
    beforeTag.textContent = riskLevel;
    beforeTag.className = `badge ${riskLevel === 'HIGH RISK' ? 'badge-danger' : (riskLevel === 'WARNING' ? 'badge-warning' : 'badge-normal')} text-xs`;
  }

  const beforeWasteVal = document.getElementById('ap-before-waste-val');
  if (beforeWasteVal) {
    beforeWasteVal.textContent = `${wastePct.toFixed(2)}%`;
    beforeWasteVal.className = `comparison-hero-stat font-accent ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-cyan')}`;
  }

  const beforeScoreVal = document.getElementById('ap-before-score-val');
  if (beforeScoreVal) {
    beforeScoreVal.textContent = `${riskScore.toFixed(0)} / 100`;
    beforeScoreVal.className = `font-bold ${riskLevel === 'HIGH RISK' ? 'text-danger' : (riskLevel === 'WARNING' ? 'text-warning' : 'text-green')}`;
  }

  const beforeWasteKgVal = document.getElementById('ap-before-waste-kg-val');
  if (beforeWasteKgVal) {
    beforeWasteKgVal.textContent = `${wasteKg.toFixed(1)} kg`;
  }
}

async function updateAfterPredictionSimulation() {
  const currentBatch = state.afterPredictionBatch || {
    machine_id: document.getElementById('ap-machine-id')?.value || 'M02',
    fabric_type: document.getElementById('ap-fabric-type')?.value || 'Cotton',
    total_production: parseFloat(document.getElementById('ap-total-prod')?.value) || 1000,
    waste_quantity: parseFloat(document.getElementById('ap-waste-qty')?.value) || 85,
    production_speed: parseFloat(document.getElementById('slider-ap-speed')?.value) || 800,
    machine_age: parseFloat(document.getElementById('ap-machine-age')?.value) || 6.2,
    maintenance_age_days: parseInt(document.getElementById('slider-ap-maint')?.value) || 30,
    humidity: parseFloat(document.getElementById('slider-ap-humidity')?.value) || 55,
    temperature: parseFloat(document.getElementById('slider-ap-temp')?.value) || 25.0
  };

  const modifiedParams = {
    production_speed: parseFloat(document.getElementById('slider-ap-speed')?.value || 800),
    humidity: parseFloat(document.getElementById('slider-ap-humidity')?.value || 55),
    maintenance_age_days: parseInt(document.getElementById('slider-ap-maint')?.value || 30),
    temperature: parseFloat(document.getElementById('slider-ap-temp')?.value || 25.0)
  };

  try {
    const res = await fetch('/api/root-cause/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        batch: currentBatch,
        modified_params: modifiedParams
      })
    });

    if (!res.ok) return;
    const sim = await res.json();

    // After Column Update
    const afterRiskLevel = sim.simulated_risk_level || 'NORMAL';
    const afterRiskScore = sim.simulated_risk_score != null ? sim.simulated_risk_score : 20;
    const afterWastePct = sim.simulated_waste_percentage != null ? sim.simulated_waste_percentage : (sim.simulated_waste_pct != null ? sim.simulated_waste_pct : 3.8);
    const wasteReductionPct = sim.waste_reduction_pct != null ? sim.waste_reduction_pct : (sim.estimated_waste_reduction_pct != null ? sim.estimated_waste_reduction_pct : 0);
    const wasteSavedKg = sim.estimated_kg_saved != null ? sim.estimated_kg_saved : (sim.estimated_waste_saved_kg != null ? sim.estimated_waste_saved_kg : 0);
    const initialRisk = sim.initial_risk_score != null ? sim.initial_risk_score : (currentBatch.risk_score || 0);
    const riskDelta = sim.risk_delta != null ? sim.risk_delta : Math.round(afterRiskScore - initialRisk);

    const afterTag = document.getElementById('ap-after-risk-tag');
    if (afterTag) {
      afterTag.textContent = afterRiskLevel;
      afterTag.className = `badge ${afterRiskLevel === 'HIGH RISK' ? 'badge-danger' : (afterRiskLevel === 'WARNING' ? 'badge-warning' : 'badge-normal')} text-xs`;
    }

    const afterWasteVal = document.getElementById('ap-after-waste-val');
    if (afterWasteVal) {
      afterWasteVal.textContent = `${afterWastePct.toFixed(2)}%`;
      afterWasteVal.className = `comparison-hero-stat font-accent ${afterRiskLevel === 'HIGH RISK' ? 'text-danger' : (afterRiskLevel === 'WARNING' ? 'text-warning' : 'text-normal')}`;
    }

    const deltaWasteBadge = document.getElementById('ap-delta-waste-badge');
    if (deltaWasteBadge) {
      const deltaSign = wasteReductionPct > 0 ? '-' : '+';
      deltaWasteBadge.textContent = `${deltaSign}${Math.abs(wasteReductionPct).toFixed(2)}%`;
      deltaWasteBadge.className = `delta-badge ${wasteReductionPct >= 0 ? 'delta-improved' : 'delta-degraded'}`;
    }

    const afterScoreVal = document.getElementById('ap-after-score-val');
    if (afterScoreVal) {
      afterScoreVal.textContent = `${afterRiskScore} / 100`;
      afterScoreVal.className = `font-bold ${afterRiskLevel === 'HIGH RISK' ? 'text-danger' : (afterRiskLevel === 'WARNING' ? 'text-warning' : 'text-normal')}`;
    }

    const deltaScoreBadge = document.getElementById('ap-delta-score-badge');
    if (deltaScoreBadge) {
      deltaScoreBadge.textContent = `${riskDelta <= 0 ? '' : '+'}${riskDelta} pts`;
      deltaScoreBadge.className = `delta-badge ${riskDelta <= 0 ? 'delta-improved' : 'delta-degraded'}`;
    }

    const afterWasteKgVal = document.getElementById('ap-after-waste-kg-val');
    if (afterWasteKgVal) {
      const totalProd = currentBatch.total_production || 1000;
      const simKg = (afterWastePct / 100) * totalProd;
      afterWasteKgVal.textContent = `${simKg.toFixed(1)} kg`;
    }

    // Savings Box
    const savedKgEl = document.getElementById('ap-saved-kg-display');
    if (savedKgEl) {
      savedKgEl.textContent = `${wasteSavedKg >= 0 ? '+' : ''}${wasteSavedKg.toFixed(1)} kg`;
      savedKgEl.className = `savings-amount ${wasteSavedKg >= 0 ? 'text-normal' : 'text-danger'}`;
    }

    const savedPctEl = document.getElementById('ap-saved-pct-display');
    if (savedPctEl) {
      const origWaste = currentBatch.waste_quantity || (currentBatch.total_production * 0.08);
      const relPct = origWaste > 0 ? (wasteSavedKg / origWaste) * 100 : 0;
      savedPctEl.textContent = `${Math.max(0, relPct).toFixed(1)}% waste reduction`;
    }

    // Prescriptive Steps
    const stepsList = document.getElementById('ap-prescriptive-steps-list');
    if (stepsList) {
      const steps = [];
      if (modifiedParams.maintenance_age_days < 25) {
        steps.push(`Perform preventive maintenance & calibration on machine ${currentBatch.machine_id} (resetting cycle).`);
      }
      if (modifiedParams.production_speed <= 780) {
        steps.push(`Regulate loom speed to ${modifiedParams.production_speed} RPM to alleviate mechanical yarn friction.`);
      }
      if (modifiedParams.humidity >= 55 && modifiedParams.humidity <= 65) {
        steps.push(`Maintain climate humidity at ${modifiedParams.humidity}% RH in loom shed to prevent static yarn snapping.`);
      }
      if (modifiedParams.temperature <= 26.0) {
        steps.push(`Control bay temperature at ${modifiedParams.temperature.toFixed(1)}°C to avoid thermal motor drift.`);
      }
      if (steps.length === 0) {
        steps.push('Parameters are tuned to standard operational baseline limits. Continue real-time monitoring.');
      }
      stepsList.innerHTML = steps.map(s => `<li>${escapeHtml(s)}</li>`).join('');
    }

  } catch (err) {
    console.error('Error updating after prediction simulation:', err);
  }
}

function autoTuneAfterPredictionLevers() {
  const fabric = document.getElementById('ap-fabric-type')?.value || 'Cotton';
  
  // Safe speed table
  const safeSpeeds = {
    'Silk': 680,
    'Wool': 700,
    'Cotton': 820,
    'Polyester': 850,
    'Denim': 760,
    'Linen': 720,
    'Rayon': 780
  };

  const safeSpeed = safeSpeeds[fabric] || 780;
  
  const speedSlider = document.getElementById('slider-ap-speed');
  const humiditySlider = document.getElementById('slider-ap-humidity');
  const maintSlider = document.getElementById('slider-ap-maint');
  const tempSlider = document.getElementById('slider-ap-temp');

  if (speedSlider) speedSlider.value = safeSpeed;
  if (humiditySlider) humiditySlider.value = 58;
  if (maintSlider) maintSlider.value = 10;
  if (tempSlider) tempSlider.value = 24.0;

  document.getElementById('lbl-ap-speed').textContent = `${safeSpeed} RPM`;
  document.getElementById('lbl-ap-humidity').textContent = `58% RH`;
  document.getElementById('lbl-ap-maint').textContent = `10 Days`;
  document.getElementById('lbl-ap-temp').textContent = `24.0°C`;

  updateAfterPredictionSimulation();
  showToast('AI optimal safe operating levers applied!', 'success');
}

function resetAfterPredictionSliders() {
  if (state.afterPredictionBatch) {
    const b = state.afterPredictionBatch;
    const speedSlider = document.getElementById('slider-ap-speed');
    const humiditySlider = document.getElementById('slider-ap-humidity');
    const maintSlider = document.getElementById('slider-ap-maint');
    const tempSlider = document.getElementById('slider-ap-temp');

    if (speedSlider) speedSlider.value = b.production_speed || 800;
    if (humiditySlider) humiditySlider.value = b.humidity || 55;
    if (maintSlider) maintSlider.value = 95;
    if (tempSlider) tempSlider.value = b.temperature || 25.0;

    document.getElementById('lbl-ap-speed').textContent = `${speedSlider.value} RPM`;
    document.getElementById('lbl-ap-humidity').textContent = `${humiditySlider.value}% RH`;
    document.getElementById('lbl-ap-maint').textContent = `${maintSlider.value} Days`;
    document.getElementById('lbl-ap-temp').textContent = `${parseFloat(tempSlider.value).toFixed(1)}°C`;

    updateAfterPredictionSimulation();
    showToast('Sliders reset to batch telemetry values', 'info');
  }
}

function applyAfterPredictionLeversToForm() {
  const speed = document.getElementById('slider-ap-speed')?.value;
  const humidity = document.getElementById('slider-ap-humidity')?.value;
  const maintDays = parseInt(document.getElementById('slider-ap-maint')?.value) || 10;
  const temp = document.getElementById('slider-ap-temp')?.value;

  if (speed) document.getElementById('ap-speed').value = speed;
  if (humidity) document.getElementById('ap-humidity').value = humidity;
  if (temp) document.getElementById('ap-temperature').value = temp;
  
  // Set maintenance date
  const dateStr = getDaysAgoDate(maintDays);
  document.getElementById('ap-maint-date').value = dateStr;

  // Estimate new reduced waste
  const prod = parseFloat(document.getElementById('ap-total-prod')?.value) || 1000;
  const simWasteVal = document.getElementById('ap-after-waste-val')?.textContent || '3.8%';
  const newPct = parseFloat(simWasteVal) || 3.8;
  const newWasteKg = (newPct / 100) * prod;
  document.getElementById('ap-waste-qty').value = newWasteKg.toFixed(1);

  document.getElementById('ap-total-prod').dispatchEvent(new Event('input'));
  showToast('Optimized After-Prediction levers applied to form!', 'success');
}

async function saveAfterPredictionBatch() {
  await runAfterPrediction(true);
}


// ------------------------------------------------------------
// TAB 3: MACHINE-WISE ANALYTICS
// ------------------------------------------------------------
async function loadMachineAnalytics() {
  try {
    const res = await fetch('/api/analytics/machines');
    if (!res.ok) return;
    const data = await res.json();
    const machines = data.machines || [];

    // Highest / Lowest Highlights
    if (data.highest_waste_machine) {
      document.getElementById('mach-tab-highest').innerHTML = `
        <h3 class="text-danger">${data.highest_waste_machine.machine_id}</h3>
        <p class="text-sm text-muted">Avg Waste: <strong>${data.highest_waste_machine.average_waste_pct}%</strong> | Age: ${data.highest_waste_machine.machine_age_years} yrs | ${data.highest_waste_machine.maintenance_status}</p>
      `;
    }
    if (data.lowest_waste_machine) {
      document.getElementById('mach-tab-lowest').innerHTML = `
        <h3 class="text-normal">${data.lowest_waste_machine.machine_id}</h3>
        <p class="text-sm text-muted">Avg Waste: <strong>${data.lowest_waste_machine.average_waste_pct}%</strong> | Age: ${data.lowest_waste_machine.machine_age_years} yrs | ${data.lowest_waste_machine.maintenance_status}</p>
      `;
    }
    if (document.getElementById('mach-corr-val')) {
      document.getElementById('mach-corr-val').textContent = 
        `${data.age_waste_correlation > 0 ? '+' : ''}${data.age_waste_correlation} Correlation`;
    }

    // Machine Age vs Waste Scatter Chart
    renderAgeVsWasteChart(machines);

    // Fleet Table
    const tbody = document.getElementById('machine-fleet-tbody');
    if (tbody) {
      tbody.innerHTML = machines.map(m => `
        <tr>
          <td class="font-bold">${m.machine_id}</td>
          <td>${m.machine_age_years}</td>
          <td>${m.batch_count}</td>
          <td class="font-bold text-cyan">${m.average_waste_pct}%</td>
          <td>${m.min_waste_pct}% - ${m.max_waste_pct}%</td>
          <td>${m.abnormal_batches}</td>
          <td>${m.abnormal_rate_pct}%</td>
          <td>${m.average_speed}</td>
          <td>${m.days_since_maintenance} days</td>
          <td>${renderMaintenanceBadge(m.maintenance_status)}</td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading machine analytics:', err);
  }
}

function renderAgeVsWasteChart(machines) {
  const ctx = document.getElementById('chart-age-vs-waste');
  if (!ctx) return;

  if (state.charts['ageVsWaste']) {
    state.charts['ageVsWaste'].destroy();
  }

  const scatterData = machines.map(m => ({
    x: m.machine_age_years,
    y: m.average_waste_pct,
    label: m.machine_id
  }));

  state.charts['ageVsWaste'] = new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Machines',
        data: scatterData,
        backgroundColor: '#8B5CF6',
        pointRadius: 8,
        pointHoverRadius: 11
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          title: { display: true, text: 'Machine Age (Years)', color: '#9CA3AF' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF' }
        },
        y: {
          title: { display: true, text: 'Average Waste Percentage (%)', color: '#9CA3AF' },
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', callback: v => v + '%' }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.raw.label}: Age ${ctx.raw.x} yrs → ${ctx.raw.y}% Avg Waste`
          }
        }
      }
    }
  });
}


// ------------------------------------------------------------
// TAB 4: FABRIC & SHIFT ANALYTICS
// ------------------------------------------------------------
async function loadFabricAndShiftAnalytics() {
  try {
    const [fabricRes, shiftRes] = await Promise.all([
      fetch('/api/analytics/fabrics'),
      fetch('/api/analytics/shifts')
    ]);

    const fabricData = await fabricRes.json();
    const shiftData = await shiftRes.json();

    // 1. Fabric Waste Chart
    const fCtx = document.getElementById('chart-fabric-waste');
    if (fCtx) {
      if (state.charts['fabricWaste']) state.charts['fabricWaste'].destroy();

      const fabrics = fabricData.fabrics || [];
      state.charts['fabricWaste'] = new Chart(fCtx, {
        type: 'bar',
        data: {
          labels: fabrics.map(f => f.fabric_type),
          datasets: [{
            label: 'Avg Waste %',
            data: fabrics.map(f => f.average_waste_pct),
            backgroundColor: fabrics.map(f => f.is_high_risk ? '#EF4444' : '#06B6D4'),
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { ticks: { color: '#9CA3AF', callback: v => v + '%' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            x: { ticks: { color: '#9CA3AF' }, grid: { display: false } }
          },
          plugins: { legend: { display: false } }
        }
      });
    }

    // 2. Shift Chart
    const sCtx = document.getElementById('chart-shift-waste');
    if (sCtx) {
      if (state.charts['shiftWaste']) state.charts['shiftWaste'].destroy();

      const shifts = shiftData.shifts || [];
      state.charts['shiftWaste'] = new Chart(sCtx, {
        type: 'bar',
        data: {
          labels: shifts.map(s => s.shift),
          datasets: [
            {
              label: 'Avg Waste %',
              data: shifts.map(s => s.average_waste_pct),
              backgroundColor: '#8B5CF6',
              borderRadius: 6,
              yAxisID: 'y'
            },
            {
              label: 'Abnormal Rate %',
              data: shifts.map(s => s.abnormal_rate_pct),
              backgroundColor: '#F59E0B',
              borderRadius: 6,
              yAxisID: 'y'
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { ticks: { color: '#9CA3AF', callback: v => v + '%' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            x: { ticks: { color: '#9CA3AF' }, grid: { display: false } }
          },
          plugins: {
            legend: { labels: { color: '#9CA3AF' } }
          }
        }
      });
    }

    // 3. Fabric Summary Table
    const fTbody = document.getElementById('fabric-summary-tbody');
    if (fTbody) {
      fTbody.innerHTML = (fabricData.fabrics || []).map(f => `
        <tr>
          <td class="font-bold">${f.fabric_type}</td>
          <td>${f.batch_count}</td>
          <td class="font-bold text-cyan">${f.average_waste_pct}%</td>
          <td>${f.total_production_kg?.toLocaleString()}</td>
          <td>${f.total_waste_kg?.toLocaleString()}</td>
          <td>${f.abnormal_batches}</td>
          <td>${f.abnormal_rate_pct}%</td>
          <td>${f.average_speed} rpm</td>
          <td>${f.is_high_risk ? '<span class="tag tag-danger">HIGH RISK PROFILE</span>' : '<span class="badge badge-subtle">Standard</span>'}</td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading fabric/shift analytics:', err);
  }
}


// ------------------------------------------------------------
// TAB 5: MAINTENANCE & OPERATOR ANALYTICS
// ------------------------------------------------------------
async function loadOperatorAndMaintenanceAnalytics() {
  try {
    const [maintRes, opRes] = await Promise.all([
      fetch('/api/analytics/maintenance'),
      fetch('/api/analytics/operators')
    ]);

    const maintData = await maintRes.json();
    const opData = await opRes.json();

    // 1. Maintenance Degradation Chart
    const mCtx = document.getElementById('chart-maint-degradation');
    if (mCtx) {
      if (state.charts['maintDegradation']) state.charts['maintDegradation'].destroy();

      const bins = maintData.degradation_bins || [];
      state.charts['maintDegradation'] = new Chart(mCtx, {
        type: 'line',
        data: {
          labels: bins.map(b => b.bin),
          datasets: [{
            label: 'Avg Waste %',
            data: bins.map(b => b.avg_waste_pct),
            borderColor: '#F59E0B',
            backgroundColor: 'rgba(245, 158, 11, 0.15)',
            tension: 0.35,
            fill: true,
            pointRadius: 6,
            pointBackgroundColor: '#F59E0B'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { ticks: { color: '#9CA3AF', callback: v => v + '%' }, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            x: { title: { display: true, text: 'Days Since Last Maintenance', color: '#9CA3AF' }, ticks: { color: '#9CA3AF' }, grid: { display: false } }
          }
        }
      });
    }

    // 2. Overdue Maintenance Action Matrix Table
    const mTbody = document.getElementById('maintenance-matrix-tbody');
    if (mTbody) {
      const allMaint = [
        ...(maintData.overdue || []).map(m => ({ ...m, status: 'OVERDUE' })),
        ...(maintData.approaching || []).map(m => ({ ...m, status: 'APPROACHING' })),
        ...(maintData.recently_maintained || []).map(m => ({ ...m, status: 'GOOD' }))
      ];

      if (allMaint.length === 0) {
        mTbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No maintenance records found.</td></tr>';
      } else {
        mTbody.innerHTML = allMaint.map(m => `
          <tr>
            <td class="font-bold">${m.machine_id}</td>
            <td>${m.days_since_maintenance} days</td>
            <td>${renderMaintenanceBadge(m.status)}</td>
            <td>${m.status === 'OVERDUE' ? `<span class="text-danger font-bold">${m.days_overdue} days overdue</span>` : (m.status === 'APPROACHING' ? `${m.days_until_overdue} days left` : 'Optimal')}</td>
            <td>${m.machine_age_years} yrs</td>
            <td>${m.average_waste_pct}%</td>
            <td>${m.status === 'OVERDUE' ? '<strong>Schedule Urgent Calibration</strong>' : (m.status === 'APPROACHING' ? 'Plan Preventive Slot' : 'Routine Operation')}</td>
          </tr>
        `).join('');
      }
    }

    // 3. Operator Performance Table
    const opTbody = document.getElementById('operator-summary-tbody');
    if (opTbody) {
      opTbody.innerHTML = (opData.operators || []).map(op => `
        <tr>
          <td class="font-bold">${op.operator}</td>
          <td>${op.batch_count}</td>
          <td class="font-bold text-cyan">${op.average_waste_pct}%</td>
          <td>${op.average_speed} rpm</td>
          <td>${op.abnormal_batches}</td>
          <td>${op.abnormal_rate_pct}%</td>
          <td><span class="badge badge-subtle">${(op.machines_operated || []).join(', ')}</span></td>
        </tr>
      `).join('');
    }

  } catch (err) {
    console.error('Error loading operator/maintenance analytics:', err);
  }
}


// ------------------------------------------------------------
// TAB 6: BATCH DATA EXPLORER & TABLE
// ------------------------------------------------------------
function initFilters() {
  const searchInput = document.getElementById('filter-search');
  const machineSelect = document.getElementById('filter-machine');
  const fabricSelect = document.getElementById('filter-fabric');
  const shiftSelect = document.getElementById('filter-shift');
  const riskSelect = document.getElementById('filter-risk');
  const clearBtn = document.getElementById('btn-clear-filters');
  const exportBtn = document.getElementById('btn-export-csv');

  // Populate Dropdown options
  populateFilterDropdowns();

  // Search debounce
  let searchTimer;
  searchInput?.addEventListener('input', (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.filters.search = e.target.value;
      state.currentPage = 1;
      loadBatchesTable();
    }, 300);
  });

  machineSelect?.addEventListener('change', (e) => {
    state.filters.machine = e.target.value;
    state.currentPage = 1;
    loadBatchesTable();
  });

  fabricSelect?.addEventListener('change', (e) => {
    state.filters.fabric = e.target.value;
    state.currentPage = 1;
    loadBatchesTable();
  });

  shiftSelect?.addEventListener('change', (e) => {
    state.filters.shift = e.target.value;
    state.currentPage = 1;
    loadBatchesTable();
  });

  riskSelect?.addEventListener('change', (e) => {
    state.filters.risk = e.target.value;
    state.currentPage = 1;
    loadBatchesTable();
  });

  clearBtn?.addEventListener('click', () => {
    state.filters = { machine: 'ALL', fabric: 'ALL', shift: 'ALL', operator: 'ALL', risk: 'ALL', search: '' };
    if (searchInput) searchInput.value = '';
    if (machineSelect) machineSelect.value = 'ALL';
    if (fabricSelect) fabricSelect.value = 'ALL';
    if (shiftSelect) shiftSelect.value = 'ALL';
    if (riskSelect) riskSelect.value = 'ALL';
    state.currentPage = 1;
    loadBatchesTable();
  });

  // Pagination Buttons
  document.getElementById('btn-page-prev')?.addEventListener('click', () => {
    if (state.currentPage > 1) {
      state.currentPage--;
      loadBatchesTable();
    }
  });

  document.getElementById('btn-page-next')?.addEventListener('click', () => {
    const maxPage = Math.ceil(state.totalBatches / state.pageSize);
    if (state.currentPage < maxPage) {
      state.currentPage++;
      loadBatchesTable();
    }
  });

  // CSV Export
  exportBtn?.addEventListener('click', () => {
    window.location.href = '/api/export';
  });
}

function populateFilterDropdowns() {
  const machineSelect = document.getElementById('filter-machine');
  const fabricSelect = document.getElementById('filter-fabric');

  if (machineSelect) {
    const machines = ['M01', 'M02', 'M03', 'M04', 'M05', 'M06', 'M07', 'M08', 'M09', 'M10'];
    machineSelect.innerHTML = '<option value="ALL">All Machines</option>' + 
      machines.map(m => `<option value="${m}">${m}</option>`).join('');
  }

  if (fabricSelect) {
    const fabrics = ['Cotton', 'Polyester', 'Silk', 'Denim', 'Wool', 'Linen', 'Rayon'];
    fabricSelect.innerHTML = '<option value="ALL">All Fabrics</option>' + 
      fabrics.map(f => `<option value="${f}">${f}</option>`).join('');
  }
}

async function loadBatchesTable() {
  const offset = (state.currentPage - 1) * state.pageSize;
  const params = new URLSearchParams({
    machine: state.filters.machine,
    fabric: state.filters.fabric,
    shift: state.filters.shift,
    operator: state.filters.operator,
    risk: state.filters.risk,
    limit: state.pageSize,
    offset: offset
  });

  if (state.filters.search) {
    params.append('search', state.filters.search);
  }

  try {
    const res = await fetch(`/api/batches?${params.toString()}`);
    if (!res.ok) return;
    const data = await res.json();
    const batches = data.batches || [];
    state.totalBatches = data.total_count || 0;

    // Update Counter & Pagination
    document.getElementById('explorer-count-label').textContent = 
      `Showing ${state.totalBatches.toLocaleString()} matching production batches`;
    
    document.getElementById('pagination-info').textContent = 
      `Showing ${Math.min(state.totalBatches, offset + 1)}-${Math.min(state.totalBatches, offset + batches.length)} of ${state.totalBatches.toLocaleString()}`;
    
    document.getElementById('current-page-num').textContent = state.currentPage;
    document.getElementById('btn-page-prev').disabled = state.currentPage <= 1;
    document.getElementById('btn-page-next').disabled = (offset + batches.length) >= state.totalBatches;

    const tbody = document.getElementById('batches-table-tbody');
    if (!tbody) return;

    if (batches.length === 0) {
      tbody.innerHTML = '<tr><td colspan="12" class="text-center py-4 text-muted">No matching batches found.</td></tr>';
      return;
    }

    tbody.innerHTML = batches.map(b => {
      const reasonSnippet = b.reasons && b.reasons.length > 0 ? b.reasons[0] : 'Nominal conditions';
      return `
        <tr>
          <td class="font-bold">${b.batch_id}</td>
          <td><span class="badge badge-subtle">${b.machine_id}</span></td>
          <td>${b.fabric_type}</td>
          <td>${b.shift}</td>
          <td>${b.operator}</td>
          <td>${b.total_production?.toLocaleString()} kg</td>
          <td>${b.waste_quantity?.toFixed(1)} kg</td>
          <td class="font-bold text-cyan">${b.waste_percentage?.toFixed(2)}%</td>
          <td>${renderRiskBadge(b.risk_level)}</td>
          <td><strong>${b.risk_score?.toFixed(0)}</strong>/100</td>
          <td style="max-width: 250px; overflow: hidden; text-overflow: ellipsis;" title="${reasonSnippet}">
            <small class="text-muted">${reasonSnippet}</small>
          </td>
          <td>
            <button class="btn btn-sm btn-secondary" onclick="inspectBatch('${b.batch_id}')">
              <i class="fa-solid fa-circle-info"></i> Inspect
            </button>
          </td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    console.error('Error loading batches table:', err);
  }
}

async function inspectBatch(batchId) {
  try {
    const res = await fetch(`/api/batches?search=${encodeURIComponent(batchId)}&limit=1`);
    if (!res.ok) return;
    const data = await res.json();
    if (!data.batches || data.batches.length === 0) return;

    const b = data.batches[0];
    document.getElementById('modal-batch-id').textContent = `Batch: ${b.batch_id}`;
    
    const modalBadge = document.getElementById('modal-risk-badge');
    if (modalBadge) {
      let modalBadgeClass = 'badge-normal';
      if (b.risk_level === 'HIGH RISK') modalBadgeClass = 'badge-danger';
      else if (b.risk_level === 'WARNING') modalBadgeClass = 'badge-warning';
      else if (b.risk_level === 'INVALID') modalBadgeClass = 'badge-invalid';
      modalBadge.className = `badge ${modalBadgeClass}`;
      modalBadge.textContent = `${b.risk_level || 'UNKNOWN'} (${b.risk_score != null ? b.risk_score.toFixed(0) : '0'}/100)`;
    }

    // Fetch deep diagnostic for reason cards
    let diag = null;
    try {
      const diagRes = await fetch('/api/root-cause/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(b)
      });
      if (diagRes.ok) diag = await diagRes.json();
    } catch (dErr) {
      console.warn('Could not fetch deep diagnosis for modal:', dErr);
    }

    const reasonCards = (diag && diag.reason_cards) || [];
    const solutions = (diag && diag.preventive_solutions) || [];
    const actionPlan = (diag && diag.recommended_action_plan) || {};

    const modalBody = document.getElementById('modal-body-content');
    modalBody.innerHTML = `
      <div class="grid-2-col mb-3">
        <div>
          <div class="sub-metric mb-2"><span class="sub-label">Machine ID:</span> <span class="sub-val">${escapeHtml(b.machine_id)} (Age: ${b.machine_age} yrs)</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Fabric Type:</span> <span class="sub-val">${escapeHtml(b.fabric_type)}</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Shift & Operator:</span> <span class="sub-val">${escapeHtml(b.shift)} | ${escapeHtml(b.operator)}</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Production Speed:</span> <span class="sub-val">${b.production_speed} rpm</span></div>
        </div>
        <div>
          <div class="sub-metric mb-2"><span class="sub-label">Total Production:</span> <span class="sub-val font-bold">${b.total_production?.toLocaleString()} kg</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Waste Quantity:</span> <span class="sub-val font-bold">${b.waste_quantity?.toFixed(1)} kg</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Waste Percentage:</span> <span class="sub-val text-cyan font-bold" style="font-size: 1.1rem;">${b.waste_percentage?.toFixed(2)}%</span></div>
          <div class="sub-metric mb-2"><span class="sub-label">Days Since Maintenance:</span> <span class="sub-val">${b.maintenance_age_days} days (${escapeHtml(b.last_maintenance_date || 'N/A')})</span></div>
        </div>
      </div>

      <!-- WHY IS THIS BATCH AT RISK? -->
      <div class="card p-3 mb-3" style="background: rgba(0,0,0,0.25); border-left: 3px solid var(--risk-danger);">
        <h5 class="section-heading mb-2 text-danger"><i class="fa-solid fa-circle-question"></i> WHY IS THIS BATCH AT RISK?</h5>
        <div class="reason-cards-grid">
          ${reasonCards.length > 0 ? reasonCards.map((rc, idx) => `
            <div class="reason-card card-severity-${(rc.severity || 'warning').toLowerCase()}" style="padding: 0.75rem;">
              <div class="reason-card-header">
                <div class="reason-title" style="font-size: 0.85rem;">
                  <i class="fa-solid ${rc.icon || 'fa-triangle-exclamation'}"></i>
                  <span>${escapeHtml(rc.title || `Reason ${idx + 1}`)}</span>
                </div>
                <span class="badge badge-${rc.badge_color || 'warning'} text-xs">${escapeHtml(rc.severity || 'WARNING')}</span>
              </div>
              <div class="observed-benchmark-grid" style="margin-bottom: 0.4rem;">
                <div class="stat-chip" style="padding: 0.35rem 0.5rem;">
                  <span class="stat-chip-label">Observed</span>
                  <div class="stat-chip-val text-xs text-${rc.badge_color || 'warning'}">${escapeHtml(rc.observed || 'N/A')}</div>
                </div>
                <div class="stat-chip" style="padding: 0.35rem 0.5rem;">
                  <span class="stat-chip-label">Benchmark</span>
                  <div class="stat-chip-val text-xs text-muted">${escapeHtml(rc.benchmark || 'Nominal')}</div>
                </div>
              </div>
              <div class="reason-impact-box" style="padding: 0.4rem 0.6rem; font-size: 0.75rem;">
                <strong>Impact:</strong> ${escapeHtml(rc.impact || rc.evidence_text)}
              </div>
            </div>
          `).join('') : `
            <ul class="reasons-list">
              ${(b.reasons || ['Nominal parameters']).map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
          `}
        </div>
      </div>

      <!-- HOW CAN THE WASTE BE PREVENTED? -->
      <div class="card p-3 mb-3" style="background: rgba(0,0,0,0.25); border-left: 3px solid var(--cyan);">
        <h5 class="section-heading mb-2 text-cyan"><i class="fa-solid fa-shield-halved"></i> HOW CAN THE WASTE BE PREVENTED?</h5>
        <div class="solution-cards-grid">
          ${solutions.length > 0 ? solutions.map((sol, idx) => `
            <div class="solution-card" style="padding: 0.65rem 0.85rem;">
              <div class="solution-icon-box" style="width: 28px; height: 28px; min-width: 28px; font-size: 0.85rem;">
                <i class="fa-solid ${sol.icon || 'fa-shield-halved'}"></i>
              </div>
              <div class="solution-card-body">
                <div class="solution-title-row">
                  <h6 class="solution-title" style="font-size: 0.82rem;">${escapeHtml(sol.title || `Solution ${idx + 1}`)}</h6>
                  <span class="badge badge-subtle text-xs">${escapeHtml(sol.priority || 'MEDIUM')}</span>
                </div>
                <p class="solution-text" style="font-size: 0.78rem;">${escapeHtml(sol.solution)}</p>
              </div>
            </div>
          `).join('') : `
            <ul class="actions-list">
              ${(b.actions || ['Maintain standard operating parameters']).map(a => `<li>${escapeHtml(a)}</li>`).join('')}
            </ul>
          `}
        </div>
      </div>

      <div class="mt-3 flex-center gap-2">
        <button class="btn btn-outline-cyan flex-1" onclick="closeModal(); loadMachineBatchesToRca('${b.machine_id}');">
          <i class="fa-solid fa-brain-circuit"></i> Root-Cause AI Studio
        </button>
        <button class="btn btn-primary flex-1 btn-report-glow" onclick="openBatchFinalizedReportById('${b.batch_id}')">
          <i class="fa-solid fa-file-contract"></i> View Audit Report
        </button>
      </div>
    `;

    document.getElementById('batch-modal').classList.remove('hidden');

  } catch (err) {
    console.error('Error inspecting batch:', err);
  }
}

function closeModal() {
  document.getElementById('batch-modal')?.classList.add('hidden');
}


// ------------------------------------------------------------
// TAB 7: FILE UPLOAD & CONFIGURATION
// ------------------------------------------------------------
function initFileUpload() {
  const dropZone = document.getElementById('file-drop-zone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('btn-browse-file');

  browseBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput.click();
  });

  dropZone?.addEventListener('click', () => fileInput.click());

  dropZone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone?.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput?.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  // Download Sample CSV Template
  document.getElementById('btn-download-sample-csv')?.addEventListener('click', () => {
    const sampleCsv = `Batch ID,Machine ID,Fabric Type,Operator,Shift,Total Production Quantity,Production Speed,Waste Quantity,Machine Age,Last Maintenance Date,Humidity,Temperature
BATCH-DEMO-001,M01,Cotton,David Kim,Morning,1200,820,42,4.0,${getDaysAgoDate(15)},55,24.5
BATCH-DEMO-002,M02,Silk,Priya Sharma,Night,900,940,95,6.2,${getDaysAgoDate(85)},38,31.0
BATCH-DEMO-003,M03,Denim,Carlos Rossi,Afternoon,1500,780,30,8.5,${getDaysAgoDate(10)},62,25.0
BATCH-DEMO-004,M04,Polyester,Fatima Al-Mansoor,Morning,1600,920,,3.5,${getDaysAgoDate(20)},,26.0
BATCH-DEMO-005,M08,Cotton,Wei Zhang,Morning,1100,850,38,1.5,${getDaysAgoDate(8)},56,24.0
`;
    const blob = new Blob([sampleCsv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'sample_textile_production_batches.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    showToast('Sample CSV template downloaded successfully!', 'info');
  });
}

async function handleFileUpload(file) {
  const statusBox = document.getElementById('upload-status-box');
  const statusText = document.getElementById('upload-status-text');
  const reportCard = document.getElementById('upload-report-card');

  statusBox?.classList.remove('hidden');
  reportCard?.classList.add('hidden');
  if (statusText) statusText.textContent = `Uploading and processing ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await res.json();
    statusBox?.classList.add('hidden');
    reportCard?.classList.remove('hidden');

    const summary = data.validation_summary || {};
    document.getElementById('rep-total').textContent = summary.total_records || 0;
    document.getElementById('rep-valid').textContent = summary.valid_records || 0;
    document.getElementById('rep-dup').textContent = summary.duplicate_ids_found || 0;
    document.getElementById('rep-imputed').textContent = summary.imputed_humidity_count || 0;
    document.getElementById('rep-zero').textContent = summary.zero_or_negative_production_count || 0;

    showToast(data.message, 'success');
    loadOverviewData(false);

  } catch (err) {
    statusBox?.classList.add('hidden');
    showToast(`Upload Error: ${err.message}`, 'error');
  }
}

function initSettings() {
  const form = document.getElementById('settings-form');
  form?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const newSettings = {
      risk_threshold_warning: parseFloat(document.getElementById('cfg-warn-thresh').value),
      risk_threshold_high: parseFloat(document.getElementById('cfg-high-thresh').value),
      maintenance_interval_days: parseInt(document.getElementById('cfg-maint-interval').value),
      duplicate_strategy: document.getElementById('cfg-dup-strategy').value
    };

    try {
      const res = await fetch('/api/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newSettings)
      });
      if (!res.ok) throw new Error('Failed to update settings');
      showToast('Settings saved successfully. Risk thresholds updated.', 'success');
      loadOverviewData(false);
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    }
  });

  // Re-seed sample database button
  document.getElementById('btn-reset-sample-data')?.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to reset and re-seed the entire database with 1,000+ realistic sample batches?')) {
      return;
    }
    try {
      const res = await fetch('/api/reset-data?count=1000', { method: 'POST' });
      if (!res.ok) throw new Error('Failed to reset dataset');
      const data = await res.json();
      showToast(data.message, 'success');
      loadOverviewData();
    } catch (err) {
      showToast(`Error: ${err.message}`, 'error');
    }
  });
}

async function loadConfig() {
  try {
    const res = await fetch('/api/config');
    if (!res.ok) return;
    const cfg = await res.json();
    state.config = cfg;

    if (document.getElementById('cfg-warn-thresh')) {
      document.getElementById('cfg-warn-thresh').value = cfg.risk_threshold_warning || 40;
    }
    if (document.getElementById('cfg-high-thresh')) {
      document.getElementById('cfg-high-thresh').value = cfg.risk_threshold_high || 70;
    }
    if (document.getElementById('cfg-maint-interval')) {
      document.getElementById('cfg-maint-interval').value = cfg.maintenance_interval_days || 60;
    }
    if (document.getElementById('cfg-dup-strategy')) {
      document.getElementById('cfg-dup-strategy').value = cfg.duplicate_strategy || 'keep_latest';
    }

  } catch (err) {
    console.error('Error loading config:', err);
  }
}


// ------------------------------------------------------------
// UTILITY & HELPER FUNCTIONS
// ------------------------------------------------------------
function renderRiskBadge(riskLevel) {
  if (riskLevel === 'NORMAL') {
    return '<span class="badge badge-normal"><i class="fa-solid fa-circle-check"></i> NORMAL</span>';
  } else if (riskLevel === 'WARNING') {
    return '<span class="badge badge-warning"><i class="fa-solid fa-triangle-exclamation"></i> WARNING</span>';
  } else if (riskLevel === 'HIGH RISK') {
    return '<span class="badge badge-danger"><i class="fa-solid fa-fire"></i> HIGH RISK</span>';
  } else if (riskLevel === 'INVALID') {
    return '<span class="badge badge-invalid"><i class="fa-solid fa-ban"></i> INVALID</span>';
  } else {
    return `<span class="badge badge-subtle">${escapeHtml(riskLevel || 'UNKNOWN')}</span>`;
  }
}

function renderMaintenanceBadge(status) {
  if (status === 'GOOD') {
    return '<span class="badge badge-normal">GOOD</span>';
  } else if (status === 'APPROACHING') {
    return '<span class="badge badge-warning">APPROACHING</span>';
  } else if (status === 'OVERDUE') {
    return '<span class="badge badge-danger font-bold">OVERDUE</span>';
  }
  return `<span class="badge badge-subtle">${status}</span>`;
}

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = 'fa-circle-info';
  if (type === 'success') icon = 'fa-circle-check text-green';
  if (type === 'error') icon = 'fa-circle-xmark text-danger';

  toast.innerHTML = `
    <i class="fa-solid ${icon}"></i>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Global scope access for row click handlers
window.inspectBatch = inspectBatch;


// ------------------------------------------------------------
// FINALIZED REPORT GENERATOR & AUDIT MODAL
// ------------------------------------------------------------
let activeReportContext = null;

async function openBatchFinalizedReportById(batchId) {
  try {
    closeModal();
    const res = await fetch(`/api/report/batch/${encodeURIComponent(batchId)}`);
    if (!res.ok) {
      // Fallback: try from batches endpoint or construct from prediction
      const bRes = await fetch(`/api/batches?search=${encodeURIComponent(batchId)}&limit=1`);
      if (bRes.ok) {
        const bData = await bRes.json();
        if (bData.batches && bData.batches.length > 0) {
          openBatchFinalizedReport(bData.batches[0]);
          return;
        }
      }
      throw new Error(`Report not found for batch ${batchId}`);
    }
    const reportData = await res.json();
    renderBatchReportHTML(reportData);
  } catch (err) {
    showToast(`Error generating report: ${err.message}`, 'error');
  }
}

function openBatchFinalizedReport(batchData) {
  closeModal();
  
  const m_id = batchData.machine_id || 'M01';
  const f_type = batchData.fabric_type || 'Cotton';
  const waste_pct = parseFloat(batchData.waste_percentage) || 0.0;
  const prod_qty = parseFloat(batchData.total_production) || 0.0;
  const waste_qty = parseFloat(batchData.waste_quantity) || 0.0;
  const risk_level = batchData.risk_level || 'NORMAL';
  const risk_score = parseFloat(batchData.risk_score) || 0.0;
  const conf_score = parseFloat(batchData.confidence_score) || 95.0;

  let status_statement = "QUALITY CERTIFIED: Batch telemetry and waste metrics operate within nominal manufacturing tolerances.";
  if (risk_level === "HIGH RISK") {
    status_statement = "CRITICAL DEFECT RISK: Significant abnormal waste or multi-factor operating stress identified. Immediate mitigation and machine inspection required.";
  } else if (risk_level === "WARNING") {
    status_statement = "CAUTION ADVISED: Moderate variance from historical baselines or maintenance limit approached. Supervisory monitoring recommended.";
  }

  const report = {
    report_id: `REP-TX-${(batchData.batch_id || 'TEMP').toUpperCase()}`,
    timestamp: batchData.created_at || new Date().toLocaleString(),
    plant_facility: "TexPulse Manufacturing Plant - Weaving & Finishing Unit 1",
    compliance_standard: "ISO 9001:2015 / ISO 14001 Textile Waste Minimization Protocol",
    batch_telemetry: {
      batch_id: batchData.batch_id || 'PREDICTED-BATCH',
      machine_id: m_id,
      fabric_type: f_type,
      operator: batchData.operator || 'Assigned Operator',
      shift: batchData.shift || 'Morning',
      total_production_kg: prod_qty,
      waste_quantity_kg: waste_qty,
      waste_percentage: waste_pct,
      production_speed_rpm: parseFloat(batchData.production_speed) || 800,
      machine_age_years: parseFloat(batchData.machine_age) || 3.0,
      last_maintenance_date: batchData.last_maintenance_date || 'N/A',
      maintenance_age_days: parseInt(batchData.maintenance_age_days || 20),
      humidity_rh: batchData.humidity !== null && batchData.humidity !== undefined ? batchData.humidity : '55.0 (Imputed)',
      humidity_imputed: Boolean(batchData.humidity_imputed),
      temperature_c: parseFloat(batchData.temperature) || 25.0
    },
    risk_assessment: {
      classification: risk_level,
      risk_score: risk_score,
      confidence_score: conf_score,
      is_abnormal_anomaly: Boolean(batchData.is_abnormal),
      status_statement: status_statement
    },
    baseline_comparison: {
      machine_historical_avg_waste_pct: 4.2,
      fabric_historical_avg_waste_pct: 3.8,
      factory_benchmark_avg_waste_pct: 4.1,
      waste_variance_from_machine_baseline_pct: (waste_pct - 4.2).toFixed(2),
      speed_variance_from_safe_fabric_rpm: ((parseFloat(batchData.production_speed) || 800) - 800).toFixed(1)
    },
    reason_cards: batchData.reason_cards || (batchData.root_cause_analysis && batchData.root_cause_analysis.reason_cards) || [],
    preventive_solutions: batchData.preventive_solutions || (batchData.root_cause_analysis && batchData.root_cause_analysis.preventive_solutions) || [],
    recommended_action_plan: batchData.recommended_action_plan || (batchData.root_cause_analysis && batchData.root_cause_analysis.recommended_action_plan) || {},
    explainability_reasons: batchData.reasons || ['Operating conditions evaluated by AI.'],
    actionable_recommendations: batchData.actions || ['Maintain nominal speed and monitoring.'],
    audit_signoff: {
      audited_by: "TexPulse AI Intelligent Production Engine v1.0",
      supervisor_approval: "Pending Plant Supervisor Review",
      maintenance_lead_sign: "Pending Maintenance Lead Sign-off"
    }
  };

  renderBatchReportHTML(report);
}

function renderBatchReportHTML(report) {
  activeReportContext = { type: 'batch', data: report };

  document.getElementById('rep-modal-title').textContent = `Quality & Risk Audit Report: ${report.batch_telemetry.batch_id}`;
  document.getElementById('rep-modal-subtitle').textContent = `Document #${report.report_id} | Issued: ${report.timestamp}`;

  const r = report;
  const b = r.batch_telemetry;
  const a = r.risk_assessment;
  const comp = r.baseline_comparison;
  const reasonCards = r.reason_cards || [];
  const solutions = r.preventive_solutions || [];
  const actionPlan = r.recommended_action_plan || {};

  let bannerClass = 'banner-normal';
  let badgeClass = 'text-green';
  if (a.classification === 'WARNING') {
    bannerClass = 'banner-warning';
    badgeClass = 'text-warning';
  } else if (a.classification === 'HIGH RISK') {
    bannerClass = 'banner-danger';
    badgeClass = 'text-danger';
  }

  const container = document.getElementById('finalized-report-content');
  container.innerHTML = `
    <div class="report-document" id="printable-report-body">
      
      <!-- LETTERHEAD -->
      <div class="report-letterhead">
        <div class="letterhead-brand">
          <h2>TEXPULSE TEXTILE MANUFACTURING</h2>
          <p>${r.plant_facility} | ${r.compliance_standard}</p>
        </div>
        <div class="letterhead-meta">
          <div>Report Ref: <strong>${r.report_id}</strong></div>
          <div>Generated: ${r.timestamp}</div>
          <div>AI Confidence: <strong>${a.confidence_score}%</strong></div>
        </div>
      </div>

      <!-- EXECUTIVE RISK EVALUATION BANNER -->
      <div class="report-exec-banner ${bannerClass}">
        <div class="banner-text">
          <h4 class="${badgeClass}"><i class="fa-solid fa-shield-halved"></i> AI RISK CLASSIFICATION: ${a.classification}</h4>
          <p>${a.status_statement}</p>
        </div>
        <div class="banner-score">
          <div class="score-big ${badgeClass}">${a.risk_score.toFixed(0)}<span style="font-size: 1rem; color: var(--text-muted);">/100</span></div>
          <span class="text-xs text-muted">COMPOSITE RISK</span>
        </div>
      </div>

      <!-- BATCH TELEMETRY DATA TABLE -->
      <div>
        <div class="report-section-title"><i class="fa-solid fa-microchip text-cyan"></i> Batch Production & Operational Telemetry</div>
        <table class="report-grid-table">
          <tr>
            <td class="td-label">Batch Identifier</td>
            <td class="td-val font-bold">${b.batch_id}</td>
            <td class="td-label">Fabric Material</td>
            <td class="td-val font-bold">${b.fabric_type}</td>
          </tr>
          <tr>
            <td class="td-label">Machine ID & Age</td>
            <td class="td-val">${b.machine_id} (${b.machine_age_years} yrs)</td>
            <td class="td-label">Operating Speed</td>
            <td class="td-val font-bold">${b.production_speed_rpm} rpm</td>
          </tr>
          <tr>
            <td class="td-label">Shift & Operator</td>
            <td class="td-val">${b.shift} | ${b.operator}</td>
            <td class="td-label">Maintenance Age</td>
            <td class="td-val">${b.maintenance_age_days} days (${b.last_maintenance_date})</td>
          </tr>
          <tr>
            <td class="td-label">Total Production Volume</td>
            <td class="td-val font-bold">${b.total_production_kg.toLocaleString()} kg</td>
            <td class="td-label">Computed Waste %</td>
            <td class="td-val font-bold text-cyan" style="font-size: 1rem;">${b.waste_percentage.toFixed(2)}% (${b.waste_quantity_kg.toFixed(1)} kg)</td>
          </tr>
          <tr>
            <td class="td-label">Ambient Humidity</td>
            <td class="td-val">${b.humidity_rh}% RH ${b.humidity_imputed ? '<span class="text-xs text-warning">(Imputed)</span>' : ''}</td>
            <td class="td-label">Ambient Temperature</td>
            <td class="td-val">${b.temperature_c}°C</td>
          </tr>
        </table>
      </div>

      <!-- EXPLAINABILITY REASONS (WHY IS THIS BATCH AT RISK?) -->
      <div>
        <div class="report-section-title"><i class="fa-solid fa-magnifying-glass-chart text-purple"></i> Why is this Batch at Risk? (Evidence-Based Reasons)</div>
        ${reasonCards.length > 0 ? `
          <div class="reason-cards-grid" style="margin-bottom: 1rem;">
            ${reasonCards.map(rc => `
              <div class="reason-card card-severity-${(rc.severity || 'warning').toLowerCase()}">
                <div class="reason-card-header">
                  <div class="reason-title"><i class="fa-solid ${rc.icon || 'fa-triangle-exclamation'}"></i> <span>${escapeHtml(rc.title)}</span></div>
                  <span class="badge badge-${rc.badge_color || 'warning'}">${escapeHtml(rc.severity || 'WARNING')}</span>
                </div>
                <div class="observed-benchmark-grid">
                  <div class="stat-chip">
                    <span class="stat-chip-label">Observed</span>
                    <div class="stat-chip-val text-${rc.badge_color || 'warning'}">${escapeHtml(rc.observed)}</div>
                  </div>
                  <div class="stat-chip">
                    <span class="stat-chip-label">Normal Benchmark</span>
                    <div class="stat-chip-val text-muted">${escapeHtml(rc.benchmark)}</div>
                  </div>
                </div>
                <div class="reason-impact-box">
                  <strong>Impact:</strong> ${escapeHtml(rc.impact || rc.evidence_text)}
                </div>
              </div>
            `).join('')}
          </div>
        ` : `
          <ul class="reasons-list">
            ${r.explainability_reasons.map(reason => `<li><strong>Finding:</strong> ${escapeHtml(reason)}</li>`).join('')}
          </ul>
        `}
      </div>

      <!-- PREVENTIVE SOLUTIONS (HOW CAN WASTE BE PREVENTED?) -->
      <div>
        <div class="report-section-title"><i class="fa-solid fa-shield-halved text-cyan"></i> How can the Waste be Prevented? (Actionable Remedies)</div>
        ${solutions.length > 0 ? `
          <div class="solution-cards-grid" style="margin-bottom: 1rem;">
            ${solutions.map(sol => `
              <div class="solution-card">
                <div class="solution-icon-box"><i class="fa-solid ${sol.icon || 'fa-shield-halved'}"></i></div>
                <div class="solution-card-body">
                  <div class="solution-title-row">
                    <h5 class="solution-title">${escapeHtml(sol.title)}</h5>
                    <span class="badge badge-subtle text-xs">${escapeHtml(sol.priority || 'MEDIUM')} PRIORITY</span>
                  </div>
                  <p class="solution-text">${escapeHtml(sol.solution)}</p>
                </div>
              </div>
            `).join('')}
          </div>
        ` : `
          <ul class="actions-list">
            ${r.actionable_recommendations.map(action => `<li><i class="fa-regular fa-square"></i> ${escapeHtml(action)}</li>`).join('')}
          </ul>
        `}
      </div>

      <!-- RECOMMENDED ACTION PLAN (Inspect -> Adjust -> Maintain -> Monitor) -->
      ${actionPlan && actionPlan.steps ? `
      <div>
        <div class="report-section-title"><i class="fa-solid fa-list-check text-green"></i> Recommended Action Plan (Inspect → Adjust → Maintain → Monitor)</div>
        <div class="risk-action-box" style="margin-bottom: 1rem;">
          <div class="risk-action-summary">${escapeHtml(actionPlan.summary)}</div>
          <ol class="action-steps-checklist">
            ${actionPlan.steps.map(step => `<li>${escapeHtml(step)}</li>`).join('')}
          </ol>
        </div>
      </div>
      ` : ''}

      <!-- ROOT-CAUSE AI CAUSAL ATTRIBUTION -->
      ${r.root_cause_analysis && r.root_cause_analysis.primary_cause && r.root_cause_analysis.primary_cause.is_active ? `
      <div>
        <div class="report-section-title"><i class="fa-solid fa-brain-circuit text-yellow"></i> Root-Cause AI Causal Decomposition & Estimated Waste Savings</div>
        <div class="p-3 mb-3" style="background: rgba(0,0,0,0.25); border-radius: var(--radius-sm); border-left: 3px solid var(--risk-danger);">
          <div class="flex-between">
            <span class="font-bold text-yellow" style="font-size: 0.95rem;">${escapeHtml(r.root_cause_analysis.primary_cause.title)}</span>
            <span class="badge badge-danger">${r.root_cause_analysis.primary_cause.attribution_pct}% Risk Attribution</span>
          </div>
          <p class="text-xs text-muted mt-1">${escapeHtml(r.root_cause_analysis.primary_cause.explanation)}</p>
        </div>
      </div>
      ` : ''}

      <!-- AUDIT SIGNOFF BOXES -->
      <div class="report-signatures-grid">
        <div class="sig-box">
          <span class="sig-title">Automated AI Engine</span>
          <div class="sig-line font-bold text-xs" style="color: var(--cyan);">Certified by TexPulse AI v1.0</div>
          <span class="sig-sub">Algorithmic Verification Hash</span>
        </div>
        <div class="sig-box">
          <span class="sig-title">Plant Quality Supervisor</span>
          <div class="sig-line"></div>
          <span class="sig-sub">Sign & Date Approval</span>
        </div>
        <div class="sig-box">
          <span class="sig-title">Maintenance Lead</span>
          <div class="sig-line"></div>
          <span class="sig-sub">Sign & Date Calibration</span>
        </div>
      </div>

    </div>
  `;

  document.getElementById('finalized-report-modal').classList.remove('hidden');
}

async function openPlantExecutiveReport() {
  try {
    const res = await fetch('/api/report/plant-summary');
    if (!res.ok) throw new Error('Failed to generate plant summary report');
    const p = await res.json();

    activeReportContext = { type: 'plant', data: p };

    document.getElementById('rep-modal-title').textContent = `Plant-Wide Production Waste & Quality Audit Report`;
    document.getElementById('rep-modal-subtitle').textContent = `Generated: ${p.generated_at} | Facility Executive Overview`;

    const container = document.getElementById('finalized-report-content');
    container.innerHTML = `
      <div class="report-document" id="printable-report-body">
        
        <!-- LETTERHEAD -->
        <div class="report-letterhead">
          <div class="letterhead-brand">
            <h2>TEXPULSE TEXTILE MANUFACTURING</h2>
            <p>Plant-Wide Operations & Risk Compliance Audit | ISO 9001 / ISO 14001</p>
          </div>
          <div class="letterhead-meta">
            <div>Generated: <strong>${p.generated_at}</strong></div>
            <div>Audited Batches: <strong>${p.total_batches_audited.toLocaleString()}</strong></div>
          </div>
        </div>

        <!-- EXECUTIVE SUMMARY STATS -->
        <div class="grid-3-col">
          <div class="card p-3" style="background: rgba(0,0,0,0.25);">
            <span class="text-xs text-muted">TOTAL PRODUCTION VOLUME</span>
            <h3 class="font-bold text-cyan">${p.total_production_volume_kg?.toLocaleString()} kg</h3>
            <span class="text-xs text-muted">${p.total_waste_generated_kg?.toLocaleString()} kg waste generated</span>
          </div>
          <div class="card p-3" style="background: rgba(0,0,0,0.25);">
            <span class="text-xs text-muted">PLANT-WIDE WASTE RATE</span>
            <h3 class="font-bold text-green">${p.plant_wide_waste_percentage}%</h3>
            <span class="text-xs text-muted">Benchmark Target: < 4.5%</span>
          </div>
          <div class="card p-3" style="background: rgba(0,0,0,0.25);">
            <span class="text-xs text-muted">RISK PROFILE DISTRIBUTION</span>
            <div class="text-sm mt-1">
              <span class="text-green font-bold">${p.normal_batches_count} Normal</span> | 
              <span class="text-warning font-bold">${p.warning_batches_count} Warning</span> | 
              <span class="text-danger font-bold">${p.high_risk_batches_count} High Risk</span>
            </div>
            <span class="text-xs text-muted">${p.abnormal_anomaly_count} Statistical Anomalies Detected</span>
          </div>
        </div>

        <!-- FLEET & FABRIC BENCHMARK SUMMARY -->
        <div>
          <div class="report-section-title"><i class="fa-solid fa-industry text-cyan"></i> Critical Production Fleet & Material Insights</div>
          <table class="report-grid-table">
            <tr>
              <td class="td-label">Highest Waste Machine</td>
              <td class="td-val text-danger font-bold">${p.highest_waste_machine?.machine_id || 'M02'} (${p.highest_waste_machine?.average_waste_pct}%)</td>
              <td class="td-label">Lowest Waste Machine</td>
              <td class="td-val text-green font-bold">${p.lowest_waste_machine?.machine_id || 'M09'} (${p.lowest_waste_machine?.average_waste_pct}%)</td>
            </tr>
            <tr>
              <td class="td-label">Overdue Maintenance Machines</td>
              <td class="td-val text-warning font-bold" colspan="3">
                ${(p.overdue_machines || []).length > 0 ? p.overdue_machines.map(m => `${m.machine_id} (${m.days_overdue}d overdue)`).join(', ') : 'All machines are up to date with maintenance schedules.'}
              </td>
            </tr>
            <tr>
              <td class="td-label">High-Risk Fabric Profiles</td>
              <td class="td-val" colspan="3">
                ${(p.high_risk_fabrics || []).length > 0 ? p.high_risk_fabrics.map(f => `<span class="tag tag-danger">${f.fabric_type} (${f.average_waste_pct}% waste)</span>`).join(' ') : 'All fabrics operate within nominal bounds.'}
              </td>
            </tr>
          </table>
        </div>

        <!-- EXECUTIVE AUDIT RECOMMENDATIONS -->
        <div>
          <div class="report-section-title"><i class="fa-solid fa-list-check text-green"></i> Key Supervisory Directives</div>
          <ul class="actions-list">
            <li><strong>Immediate Machine Calibration:</strong> Priority service scheduled for machine ${(p.overdue_machines && p.overdue_machines[0] ? p.overdue_machines[0].machine_id : 'M02')} to prevent mechanical friction waste.</li>
            <li><strong>Fabric Speed Regulations:</strong> Enforce strict operating speed caps on Silk and Wool production batches.</li>
            <li><strong>Night Shift Audit:</strong> Inspect ambient temperature controls and shift handover protocols to minimize variance.</li>
          </ul>
        </div>

        <!-- AUDIT SIGNOFF BOXES -->
        <div class="report-signatures-grid">
          <div class="sig-box">
            <span class="sig-title">Automated AI Engine</span>
            <div class="sig-line font-bold text-xs" style="color: var(--cyan);">Certified by TexPulse AI v1.0</div>
            <span class="sig-sub">Algorithmic Verification Hash</span>
          </div>
          <div class="sig-box">
            <span class="sig-title">Operations Director</span>
            <div class="sig-line"></div>
            <span class="sig-sub">Executive Sign-off</span>
          </div>
          <div class="sig-box">
            <span class="sig-title">Chief Quality Officer</span>
            <div class="sig-line"></div>
            <span class="sig-sub">Quality Certification</span>
          </div>
        </div>

      </div>
    `;

    document.getElementById('finalized-report-modal').classList.remove('hidden');
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
}

function closeReportModal() {
  document.getElementById('finalized-report-modal')?.classList.add('hidden');
}

function downloadCurrentReportAsText() {
  if (!activeReportContext) {
    showToast('No active report to export.', 'error');
    return;
  }

  let textContent = '';
  let filename = 'textile_audit_report.txt';

  if (activeReportContext.type === 'batch') {
    const r = activeReportContext.data;
    const b = r.batch_telemetry;
    const a = r.risk_assessment;

    filename = `audit_report_${b.batch_id}.txt`;
    textContent = `
================================================================================
TEXPULSE TEXTILE MANUFACTURING - FINALIZED QUALITY & RISK AUDIT REPORT
================================================================================
Report Reference   : ${r.report_id}
Timestamp          : ${r.timestamp}
Plant Facility     : ${r.plant_facility}
Standard           : ${r.compliance_standard}

--------------------------------------------------------------------------------
1. EXECUTIVE RISK CLASSIFICATION
--------------------------------------------------------------------------------
Classification     : ${a.classification}
Risk Score         : ${a.risk_score.toFixed(1)} / 100
Confidence Score   : ${a.confidence_score.toFixed(1)}%
Anomaly Status     : ${a.is_abnormal_anomaly ? 'ABNORMAL ANOMALY DETECTED' : 'NOMINAL RANGE'}
Evaluation Summary : ${a.status_statement}

--------------------------------------------------------------------------------
2. BATCH PRODUCTION TELEMETRY
--------------------------------------------------------------------------------
Batch ID           : ${b.batch_id}
Machine ID         : ${b.machine_id} (Age: ${b.machine_age_years} years)
Fabric Type        : ${b.fabric_type}
Shift & Operator   : ${b.shift} Shift | Operator: ${b.operator}
Total Production   : ${b.total_production_kg} kg
Waste Quantity     : ${b.waste_quantity_kg} kg
Waste Percentage   : ${b.waste_percentage.toFixed(2)}%
Operating Speed    : ${b.production_speed_rpm} rpm
Maintenance Status : ${b.maintenance_age_days} days since service (${b.last_maintenance_date})
Ambient Conditions : ${b.humidity_rh}% RH | ${b.temperature_c}°C

--------------------------------------------------------------------------------
3. EXPLAINABILITY AUDIT FINDINGS
--------------------------------------------------------------------------------
${r.explainability_reasons.map((reason, idx) => `${idx + 1}. ${reason}`).join('\n')}

--------------------------------------------------------------------------------
4. REQUIRED CORRECTIVE MITIGATION ACTIONS
--------------------------------------------------------------------------------
${r.actionable_recommendations.map((action, idx) => `[ ] ${idx + 1}. ${action}`).join('\n')}

--------------------------------------------------------------------------------
5. OFFICIAL AUDIT SIGN-OFF
--------------------------------------------------------------------------------
Audited by         : ${r.audit_signoff.audited_by}
Plant Supervisor   : ___________________________ Date: ______________
Maintenance Lead   : ___________________________ Date: ______________
================================================================================
`;
  } else {
    const p = activeReportContext.data;
    filename = `plant_wide_audit_report.txt`;
    textContent = `
================================================================================
TEXPULSE TEXTILE MANUFACTURING - PLANT-WIDE EXECUTIVE QUALITY AUDIT REPORT
================================================================================
Report Title       : ${p.report_title}
Generated At       : ${p.generated_at}

Total Volume       : ${p.total_production_volume_kg} kg
Total Waste        : ${p.total_waste_generated_kg} kg
Plant Waste Rate   : ${p.plant_wide_waste_percentage}%
Total Batches      : ${p.total_batches_audited}
Normal Batches     : ${p.normal_batches_count}
Warning Batches    : ${p.warning_batches_count}
High Risk Batches  : ${p.high_risk_batches_count}
Anomalies Detected : ${p.abnormal_anomaly_count}

Highest Waste Mach : ${p.highest_waste_machine?.machine_id} (${p.highest_waste_machine?.average_waste_pct}%)
Lowest Waste Mach  : ${p.lowest_waste_machine?.machine_id} (${p.lowest_waste_machine?.average_waste_pct}%)
Overdue Machines   : ${p.overdue_machines_count} machines

================================================================================
`;
  }

  const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  showToast(`Report downloaded as ${filename}`, 'success');
}

window.openBatchFinalizedReportById = openBatchFinalizedReportById;
window.openBatchFinalizedReport = openBatchFinalizedReport;
window.openPlantExecutiveReport = openPlantExecutiveReport;
window.closeReportModal = closeReportModal;
window.loadMachineBatchesToRca = loadMachineBatchesToRca;
window.diagnoseBatchById = diagnoseBatchById;
window.loadBatchIntoRca = loadBatchIntoRca;


// ------------------------------------------------------------
// ROOT-CAUSE AI & EXPLAINABILITY ENGINE MODULE
// ------------------------------------------------------------
function initRootCauseAI() {
  // Refresh button
  document.getElementById('btn-rca-refresh')?.addEventListener('click', async () => {
    await loadRootCauseTab();
    showToast('Root-Cause AI diagnostics refreshed.', 'info');
  });

  // Overview quick button
  document.getElementById('btn-goto-rca')?.addEventListener('click', () => {
    switchTab('tab-root-cause');
  });

  // Predictor to RCA button
  document.getElementById('btn-pred-to-rca')?.addEventListener('click', () => {
    if (state.lastPrediction) {
      switchTab('tab-root-cause');
      loadBatchIntoRca(state.lastPrediction);
    }
  });

  // Diagnose selected batch button
  document.getElementById('btn-rc-diagnose-selected')?.addEventListener('click', async () => {
    const selector = document.getElementById('rc-batch-selector');
    const batchId = selector.value;
    if (!batchId) {
      showToast('Please select a batch from the list.', 'warning');
      return;
    }
    await diagnoseBatchById(batchId);
  });

  // Selector change listener
  document.getElementById('rc-batch-selector')?.addEventListener('change', async (e) => {
    const batchId = e.target.value;
    if (batchId) {
      await diagnoseBatchById(batchId);
    }
  });

  // Counterfactual Sliders Listeners
  initCounterfactualSimulator();
}

async function loadRootCauseTab() {
  try {
    // 1. Fetch plant-wide RCA analysis
    const res = await fetch('/api/root-cause/plant-analysis');
    if (!res.ok) throw new Error('Failed to load plant root-cause analysis');
    const data = await res.json();
    state.rcaData = data;

    // Update KPI Cards
    const totalEvents = data.total_failure_events || 0;
    document.getElementById('rc-kpi-events').textContent = totalEvents;
    
    if (data.pareto_causes && data.pareto_causes.length > 0) {
      const top = data.pareto_causes[0];
      document.getElementById('rc-kpi-leading-cause').textContent = top.title;
      document.getElementById('rc-kpi-leading-share').textContent = `${top.percentage_of_failures}% of abnormal failures`;
    } else {
      document.getElementById('rc-kpi-leading-cause').textContent = 'None';
      document.getElementById('rc-kpi-leading-share').textContent = 'All batches nominal';
    }

    const savedKg = data.total_potential_waste_kg_saved || 0;
    document.getElementById('rc-kpi-potential-savings').textContent = `${savedKg.toLocaleString()} kg`;

    // Find top category
    let topCatName = 'N/A';
    let topCatPct = 0;
    if (data.category_distribution) {
      for (const [cat, info] of Object.entries(data.category_distribution)) {
        if (info.percentage > topCatPct) {
          topCatPct = info.percentage;
          topCatName = cat;
        }
      }
    }
    document.getElementById('rc-kpi-top-category').textContent = topCatName;
    document.getElementById('rc-kpi-top-category-pct').textContent = `${topCatPct}% of total risk points`;

    // Render Pareto Chart
    renderRcaParetoChart(data.pareto_causes || []);

    // Render Category Donut Chart
    renderRcaCategoryChart(data.category_distribution || {});

    // Render Strategic Recommendations
    renderStrategicRecs(data.top_plant_recommendations || []);

    // Render Machine Vulnerability Matrix
    renderMachineRcaMatrix(data.machine_root_causes || []);

    // Populate Batch Selector with abnormal and high-risk batches
    await populateRcaBatchSelector();

  } catch (err) {
    console.error('Error loading Root-Cause AI tab:', err);
    showToast(`Root-Cause AI error: ${err.message}`, 'error');
  }
}

function renderRcaParetoChart(paretoCauses) {
  const ctx = document.getElementById('chart-rc-pareto');
  if (!ctx) return;

  if (state.charts['rcaPareto']) {
    state.charts['rcaPareto'].destroy();
  }

  if (!paretoCauses || paretoCauses.length === 0) {
    return;
  }

  const labels = paretoCauses.map(c => {
    return c.title.length > 25 ? c.title.substring(0, 23) + '...' : c.title;
  });
  const counts = paretoCauses.map(c => c.count);
  const cumPcts = paretoCauses.map(c => c.cumulative_percentage);

  state.charts['rcaPareto'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          type: 'line',
          label: 'Cumulative Impact %',
          data: cumPcts,
          borderColor: '#06B6D4',
          backgroundColor: 'rgba(6, 182, 212, 0.15)',
          borderWidth: 3,
          pointBackgroundColor: '#06B6D4',
          pointRadius: 4,
          yAxisID: 'yCum',
          tension: 0.25
        },
        {
          type: 'bar',
          label: 'Failure Count',
          data: counts,
          backgroundColor: [
            '#EF4444', '#F97316', '#F59E0B', '#EAB308',
            '#84CC16', '#10B981', '#06B6D4', '#6366F1'
          ],
          borderRadius: 6,
          yAxisID: 'yCount'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      scales: {
        yCount: {
          type: 'linear',
          position: 'left',
          beginAtZero: true,
          grid: { color: 'rgba(255, 255, 255, 0.05)' },
          ticks: { color: '#9CA3AF', precision: 0 },
          title: { display: true, text: 'Occurrences', color: '#9CA3AF' }
        },
        yCum: {
          type: 'linear',
          position: 'right',
          beginAtZero: true,
          max: 100,
          grid: { display: false },
          ticks: { color: '#06B6D4', callback: v => v + '%' },
          title: { display: true, text: 'Cumulative %', color: '#06B6D4' }
        },
        x: {
          grid: { display: false },
          ticks: { color: '#9CA3AF', maxRotation: 30, minRotation: 0, font: { size: 11 } }
        }
      },
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#9CA3AF', boxWidth: 12 }
        },
        tooltip: {
          callbacks: {
            afterBody: function(items) {
              const idx = items[0].dataIndex;
              const cause = paretoCauses[idx];
              if (cause && cause.potential_savings_kg) {
                return `\nCategory: ${cause.category}\nPotential Recoverable Waste: ${cause.potential_savings_kg.toLocaleString()} kg`;
              }
              return '';
            }
          }
        }
      }
    }
  });
}

function renderRcaCategoryChart(catData) {
  const ctx = document.getElementById('chart-rc-category');
  if (!ctx) return;

  if (state.charts['rcaCategory']) {
    state.charts['rcaCategory'].destroy();
  }

  const labels = Object.keys(catData);
  const values = labels.map(k => catData[k].count || 0);

  const colors = [
    '#EF4444', // Mechanical
    '#F59E0B', // Operational
    '#06B6D4', // Atmospheric
    '#A855F7', // Material
    '#F43F5E', // Thermal
    '#64748B'  // Operator
  ];

  state.charts['rcaCategory'] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: values,
        backgroundColor: colors.slice(0, labels.length),
        borderWidth: 2,
        borderColor: '#111827',
        hoverOffset: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#9CA3AF', boxWidth: 10, font: { size: 10 } }
        }
      }
    }
  });
}

function renderStrategicRecs(recs) {
  const container = document.getElementById('rc-strategic-recs-list');
  if (!container) return;

  if (!recs || recs.length === 0) {
    container.innerHTML = '<span class="text-muted text-xs">No strategic adjustments required.</span>';
    return;
  }

  container.innerHTML = recs.map(r => `
    <div class="strategic-rec-item">
      <div class="strategic-rec-title"><i class="fa-solid fa-arrow-trend-down text-normal"></i> #${r.rank} ${r.title}</div>
      <div class="strategic-rec-impact">${r.impact}</div>
      <div class="strategic-rec-action">${r.action}</div>
    </div>
  `).join('');
}

function renderMachineRcaMatrix(matrix) {
  const tbody = document.getElementById('rc-machine-matrix-tbody');
  if (!tbody) return;

  if (!matrix || matrix.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" class="text-center py-4 text-muted">No machine root causes recorded.</td></tr>';
    return;
  }

  tbody.innerHTML = matrix.map(m => {
    let dominant = 'Nominal';
    let maxCnt = 0;
    if (m.mechanical_count > maxCnt) { maxCnt = m.mechanical_count; dominant = 'Mechanical / Maintenance'; }
    if (m.speed_count > maxCnt) { maxCnt = m.speed_count; dominant = 'Loom Speed Stress'; }
    if (m.humidity_count > maxCnt) { maxCnt = m.humidity_count; dominant = 'Humidity Deviations'; }

    return `
      <tr>
        <td class="font-bold"><span class="badge badge-subtle">${m.machine_id}</span></td>
        <td class="font-bold text-danger">${m.total_abnormal_events}</td>
        <td>${m.mechanical_count}</td>
        <td>${m.speed_count}</td>
        <td>${m.humidity_count}</td>
        <td><span class="tag ${dominant.includes('Mechanical') ? 'tag-danger' : (dominant.includes('Speed') ? 'tag-warning' : 'tag-subtle')}">${dominant}</span></td>
        <td>
          <button class="btn btn-xs btn-secondary" onclick="loadMachineBatchesToRca('${m.machine_id}')">
            <i class="fa-solid fa-magnifying-glass"></i> Inspect
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

async function populateRcaBatchSelector() {
  const selector = document.getElementById('rc-batch-selector');
  if (!selector) return;

  try {
    const res = await fetch('/api/batches?limit=100');
    if (!res.ok) return;
    const data = await res.json();
    const batches = data.batches || [];

    const highRiskBatches = batches.filter(b => b.risk_level === 'HIGH RISK' || b.is_abnormal === 1);
    const otherBatches = batches.filter(b => b.risk_level !== 'HIGH RISK' && b.is_abnormal !== 1);
    const sorted = [...highRiskBatches, ...otherBatches];

    if (sorted.length === 0) {
      selector.innerHTML = '<option value="">No batches available</option>';
      return;
    }

    selector.innerHTML = sorted.map(b => `
      <option value="${b.batch_id}">
        [${b.risk_level}] ${b.batch_id} - ${b.machine_id} (${b.fabric_type}, ${b.waste_percentage?.toFixed(1)}% waste)
      </option>
    `).join('');

    if (state.activeRcaBatch) {
      selector.value = state.activeRcaBatch.batch_id;
      await diagnoseBatchById(state.activeRcaBatch.batch_id);
    } else if (sorted.length > 0) {
      selector.value = sorted[0].batch_id;
      await diagnoseBatchById(sorted[0].batch_id);
    }

  } catch (err) {
    console.error('Error populating RCA batch selector:', err);
  }
}

async function diagnoseBatchById(batchId) {
  try {
    const res = await fetch(`/api/root-cause/batch/${batchId}`);
    if (!res.ok) {
      const bRes = await fetch(`/api/batches?search=${batchId}&limit=1`);
      const bData = await bRes.json();
      if (bData.batches && bData.batches.length > 0) {
        const batch = bData.batches[0];
        const diagRes = await fetch('/api/root-cause/diagnose', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(batch)
        });
        const diag = await diagRes.json();
        renderRcaDiagnosis(diag, batch);
        return;
      }
      throw new Error(`Batch ${batchId} not found`);
    }

    const data = await res.json();
    renderRcaDiagnosis(data.diagnosis, data.batch);

  } catch (err) {
    console.error('Error diagnosing batch:', err);
    showToast(`Diagnosis error: ${err.message}`, 'error');
  }
}

function loadBatchIntoRca(batch) {
  state.activeRcaBatch = batch;
  const selector = document.getElementById('rc-batch-selector');
  if (selector) {
    let exists = false;
    for (let opt of selector.options) {
      if (opt.value === batch.batch_id) {
        exists = true;
        break;
      }
    }
    if (!exists) {
      const newOpt = document.createElement('option');
      newOpt.value = batch.batch_id;
      newOpt.textContent = `[LIVE] ${batch.batch_id} - ${batch.machine_id} (${batch.fabric_type})`;
      selector.prepend(newOpt);
    }
    selector.value = batch.batch_id;
  }
  
  if (batch.root_cause_analysis) {
    renderRcaDiagnosis(batch.root_cause_analysis, batch);
  } else {
    diagnoseBatchById(batch.batch_id);
  }
}

function loadMachineBatchesToRca(machineId) {
  switchTab('tab-root-cause');
  const selector = document.getElementById('rc-batch-selector');
  if (selector) {
    for (let opt of selector.options) {
      if (opt.textContent.includes(machineId)) {
        selector.value = opt.value;
        diagnoseBatchById(opt.value);
        break;
      }
    }
  }
}

function renderRcaDiagnosis(diag, batch) {
  state.activeRcaDiag = diag;
  state.activeRcaBatch = batch;

  if (!diag || diag.status === 'INVALID_BATCH') {
    return;
  }

  // 1. Primary Spotlight Card
  const primary = diag.primary_cause || {};
  const severity = diag.severity || 'NOMINAL';

  const sevBadge = document.getElementById('rc-severity-badge');
  if (sevBadge) {
    sevBadge.textContent = `${severity} CAUSE`;
    sevBadge.className = `badge ${severity === 'CRITICAL' ? 'badge-danger' : (severity === 'HIGH' ? 'badge-warning' : 'badge-normal')}`;
  }

  document.getElementById('rc-category-badge').textContent = primary.category || 'Nominal';
  document.getElementById('rc-attribution-pct-pill').textContent = `${primary.attribution_pct || 0}% Attribution`;
  document.getElementById('rc-primary-title').textContent = primary.title || 'Nominal Operating Conditions';
  document.getElementById('rc-primary-explanation').textContent = primary.explanation || 'No abnormal waste risk triggers detected.';
  document.getElementById('rc-impact-points').textContent = `${primary.impact_points || primary.weighted_points || 0} / 100`;
  document.getElementById('rc-active-batch-id').textContent = batch.batch_id || 'N/A';
  document.getElementById('rc-active-waste-pct').textContent = `${batch.waste_percentage?.toFixed(2) || '0.00'}%`;

  // 2. Secondary Causes
  const secList = document.getElementById('rc-secondary-list');
  if (secList) {
    const secCauses = diag.secondary_causes || [];
    if (secCauses.length === 0) {
      secList.innerHTML = '<span class="text-sm text-muted">No secondary triggers detected. Telemetry nominal outside primary driver.</span>';
    } else {
      secList.innerHTML = secCauses.map(s => `
        <div class="secondary-cause-item">
          <div>
            <div class="sec-cause-title">${s.title}</div>
            <div class="sec-cause-exp">${s.explanation}</div>
          </div>
          <span class="sec-cause-badge">${s.attribution_pct}% Impact</span>
        </div>
      `).join('');
    }
  }

  // 3. SHAP-Style Decomposition Bars
  const barsContainer = document.getElementById('rc-attribution-bars-container');
  if (barsContainer && diag.attributions) {
    const catClassMap = {
      'mechanical_maintenance': { cls: 'fill-mechanical', icon: 'fa-wrench' },
      'operational_speed': { cls: 'fill-operational', icon: 'fa-gauge-high' },
      'atmospheric_humidity': { cls: 'fill-atmospheric', icon: 'fa-droplet' },
      'fabric_sensitivity': { cls: 'fill-material', icon: 'fa-layer-group' },
      'thermal_environment': { cls: 'fill-thermal', icon: 'fa-temperature-half' },
      'shift_operator': { cls: 'fill-operator', icon: 'fa-user-clock' }
    };

    barsContainer.innerHTML = Object.entries(diag.attributions).map(([key, attr]) => {
      const meta = catClassMap[key] || { cls: 'fill-operational', icon: 'fa-circle' };
      const pct = attr.attribution_pct || 0;
      const pts = attr.impact_points || 0;
      return `
        <div class="attr-bar-item">
          <div class="attr-info">
            <span class="attr-label"><i class="fa-solid ${meta.icon}"></i> ${attr.label}</span>
            <span class="attr-chip">${pct}% (${pts} pts)</span>
          </div>
          <div class="attr-track">
            <div class="attr-fill ${meta.cls}" style="width: ${Math.min(100, Math.max(0, pct))}%;"></div>
          </div>
        </div>
      `;
    }).join('');
  }

  // 4. Prescriptive Remediation Playbook
  renderPlaybook(diag.prescriptive_playbook || []);

  // 5. Initialize Counterfactual Sliders with Batch Telemetry
  initBatchInSimulator(batch, diag);
}

function renderPlaybook(playbook) {
  const container = document.getElementById('rc-playbook-container');
  const countBadge = document.getElementById('rc-playbook-steps-count');
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = `${playbook.length} Step${playbook.length === 1 ? '' : 's'}`;
  }

  if (!playbook || playbook.length === 0) {
    container.innerHTML = '<span class="text-sm text-muted">No corrective maintenance or operational actions required.</span>';
    return;
  }

  container.innerHTML = playbook.map(step => {
    const prioColor = step.priority === 'CRITICAL' ? 'border-left: 3px solid var(--risk-danger);' : (step.priority === 'HIGH' ? 'border-left: 3px solid var(--risk-warning);' : 'border-left: 3px solid var(--risk-normal);');
    const badgeCls = step.priority === 'CRITICAL' ? 'badge-danger' : (step.priority === 'HIGH' ? 'badge-warning' : 'badge-normal');
    
    return `
      <div class="playbook-step-card" style="${prioColor}">
        <div class="playbook-step-num">${step.step}</div>
        <div class="playbook-step-body">
          <div class="playbook-step-header">
            <span class="playbook-step-action">${step.action}</span>
            <span class="badge ${badgeCls}">${step.priority}</span>
          </div>
          <p class="playbook-step-detail">${step.technical_details || ''}</p>
          <div class="flex-between mt-1">
            <span class="text-xs text-muted">Category: <strong>${step.category || 'Process'}</strong></span>
            <span class="playbook-step-saving">Save ~${step.estimated_waste_reduction_pct}% waste (${step.estimated_kg_saved || 0} kg)</span>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

function initBatchInSimulator(batch, diag) {
  const speed = parseFloat(batch.production_speed) || 800;
  const hum = parseFloat(batch.humidity) || 55;
  const maint = parseInt(batch.maintenance_age_days) || 30;
  const temp = parseFloat(batch.temperature) || 25;

  const sliderSpeed = document.getElementById('slider-sim-speed');
  const sliderHum = document.getElementById('slider-sim-humidity');
  const sliderMaint = document.getElementById('slider-sim-maint');
  const sliderTemp = document.getElementById('slider-sim-temp');

  if (sliderSpeed) { sliderSpeed.value = speed; document.getElementById('lbl-sim-speed').textContent = `${Math.round(speed)} RPM`; }
  if (sliderHum) { sliderHum.value = hum; document.getElementById('lbl-sim-humidity').textContent = `${hum.toFixed(1)}% RH`; }
  if (sliderMaint) { sliderMaint.value = maint; document.getElementById('lbl-sim-maint').textContent = `${maint} Days`; }
  if (sliderTemp) { sliderTemp.value = temp; document.getElementById('lbl-sim-temp').textContent = `${temp.toFixed(1)}°C`; }

  // Set initial simulated display
  const cfTarget = diag.counterfactual_target || {};
  document.getElementById('sim-res-risk-score').textContent = `${cfTarget.simulated_risk_score || diag.current_risk_score || 0}`;
  document.getElementById('sim-res-waste-pct').textContent = `${cfTarget.simulated_waste_percentage || batch.waste_percentage?.toFixed(2) || 0}%`;
  document.getElementById('sim-res-kg-saved').textContent = `${cfTarget.estimated_kg_saved || 0} kg`;
  document.getElementById('sim-res-pct-saved').textContent = `-${cfTarget.estimated_waste_savings_pct || 0}% waste reduction`;

  const riskDelta = Math.round((cfTarget.simulated_risk_score || 0) - (diag.current_risk_score || 0));
  document.getElementById('sim-res-risk-delta').textContent = `${riskDelta <= 0 ? '' : '+'}${riskDelta} pts`;
  document.getElementById('sim-res-risk-delta').className = riskDelta <= 0 ? 'sim-stat-delta text-normal' : 'sim-stat-delta text-danger';

  document.getElementById('sim-res-waste-delta').textContent = `-${cfTarget.estimated_waste_savings_pct || 0}%`;
}

function initCounterfactualSimulator() {
  const sliderSpeed = document.getElementById('slider-sim-speed');
  const sliderHum = document.getElementById('slider-sim-humidity');
  const sliderMaint = document.getElementById('slider-sim-maint');
  const sliderTemp = document.getElementById('slider-sim-temp');

  let debounceTimer = null;

  function onSliderChange() {
    if (sliderSpeed) document.getElementById('lbl-sim-speed').textContent = `${sliderSpeed.value} RPM`;
    if (sliderHum) document.getElementById('lbl-sim-humidity').textContent = `${sliderHum.value}% RH`;
    if (sliderMaint) document.getElementById('lbl-sim-maint').textContent = `${sliderMaint.value} Days`;
    if (sliderTemp) document.getElementById('lbl-sim-temp').textContent = `${sliderTemp.value}°C`;

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(runCounterfactualSimulation, 150);
  }

  sliderSpeed?.addEventListener('input', onSliderChange);
  sliderHum?.addEventListener('input', onSliderChange);
  sliderMaint?.addEventListener('input', onSliderChange);
  sliderTemp?.addEventListener('input', onSliderChange);

  // Auto-Optimize button
  document.getElementById('btn-apply-optimal-cf')?.addEventListener('click', () => {
    if (!state.activeRcaDiag || !state.activeRcaDiag.counterfactual_target) {
      showToast('No active diagnosis available.', 'warning');
      return;
    }
    const target = state.activeRcaDiag.counterfactual_target;
    if (sliderSpeed && target.recommended_speed) sliderSpeed.value = target.recommended_speed;
    if (sliderHum && target.recommended_humidity) sliderHum.value = target.recommended_humidity;
    if (sliderMaint && target.recommended_maintenance_age !== undefined) sliderMaint.value = target.recommended_maintenance_age;
    if (sliderTemp) sliderTemp.value = 24.0;

    onSliderChange();
    showToast('AI-recommended setpoints applied to simulator!', 'success');
  });

  // Reset button
  document.getElementById('btn-reset-cf')?.addEventListener('click', () => {
    if (state.activeRcaBatch) {
      initBatchInSimulator(state.activeRcaBatch, state.activeRcaDiag);
      showToast('Simulator reset to recorded batch telemetry.', 'info');
    }
  });
}

async function runCounterfactualSimulation() {
  if (!state.activeRcaBatch) return;

  const modified = {
    production_speed: parseFloat(document.getElementById('slider-sim-speed').value),
    humidity: parseFloat(document.getElementById('slider-sim-humidity').value),
    maintenance_age_days: parseInt(document.getElementById('slider-sim-maint').value),
    temperature: parseFloat(document.getElementById('slider-sim-temp').value)
  };

  try {
    const res = await fetch('/api/root-cause/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        batch: state.activeRcaBatch,
        modified_params: modified
      })
    });

    if (!res.ok) return;
    const sim = await res.json();

    // Update Simulation Scorecards
    document.getElementById('sim-res-risk-score').textContent = `${sim.simulated_risk_score}`;
    document.getElementById('sim-res-waste-pct').textContent = `${sim.simulated_waste_percentage}%`;
    document.getElementById('sim-res-kg-saved').textContent = `${sim.estimated_kg_saved} kg`;
    document.getElementById('sim-res-pct-saved').textContent = `-${sim.waste_reduction_pct}% waste reduction`;

    const initialRisk = state.activeRcaDiag ? state.activeRcaDiag.current_risk_score : sim.initial_risk_score;
    const riskDelta = Math.round(sim.simulated_risk_score - initialRisk);
    const deltaEl = document.getElementById('sim-res-risk-delta');
    deltaEl.textContent = `${riskDelta <= 0 ? '' : '+'}${riskDelta} pts`;
    deltaEl.className = riskDelta <= 0 ? 'sim-stat-delta text-normal' : 'sim-stat-delta text-danger';

    document.getElementById('sim-res-waste-delta').textContent = `-${sim.waste_reduction_pct}%`;

  } catch (err) {
    console.error('Error running counterfactual simulation:', err);
  }
}


// ------------------------------------------------------------
// 3D DIGITAL TWIN & PROTOTYPE MODEL ENGINE (THREE.JS)
// ------------------------------------------------------------

const COMPONENT_DATA = {
  motor: {
    name: 'Main Drive Motor & Gearbox',
    category: 'Drive Transmission',
    desc: '7.5 kW synchronous induction motor driving main crankshaft, sley rockshaft, and harness shedding motion.',
    temp: 42.8,
    wear: 74,
    vib: 3.8,
    lube: 'Degraded',
    rec: 'Service rotor bearings and lubricate drive gears within 4 operating days to avoid heat expansion waste.'
  },
  harness: {
    name: 'Harness & Heald Frames (4-Shed)',
    category: 'Weaving Shedding',
    desc: 'High-speed aluminum heald frames with spring return, oscillating at up to 1200 picks/min to form the warp shed.',
    temp: 34.2,
    wear: 62,
    vib: 2.9,
    lube: 'Nominal',
    rec: 'Inspect wire heddle eyelets for yarn abrasion grooves during upcoming shift changeover.'
  },
  reed: {
    name: 'Sley & Reed Beater',
    category: 'Beat-Up Mechanism',
    desc: 'Oscillating sley arm and fine stainless-steel reed comb packing weft threads into the woven fabric fell.',
    temp: 38.5,
    wear: 58,
    vib: 4.1,
    lube: 'Nominal',
    rec: 'Check reed alignment and pneumatic air-jet timing to prevent yarn fraying.'
  },
  warpBeam: {
    name: 'Warp Supply Beam Roller',
    category: 'Yarn Feeding',
    desc: 'High-capacity warp beam cylinder with dual circular flanges holding up to 8,000 meters of continuous warp yarn.',
    temp: 26.4,
    wear: 22,
    vib: 1.2,
    lube: 'Optimal',
    rec: 'Tension brake calibrations are optimal; maintain standard beam loading protocols.'
  },
  tensioner: {
    name: 'Back-Rest & Dynamic Tension Bar',
    category: 'Tension Regulation',
    desc: 'Spring-dampened rocker bar with electronic load cells stabilizing warp tension under intermittent shedding strokes.',
    temp: 28.1,
    wear: 45,
    vib: 2.1,
    lube: 'Optimal',
    rec: 'Calibrate load-cell strain gauges every 30 operating days.'
  },
  clothRoll: {
    name: 'Cloth Take-Up & Winding Beam',
    category: 'Fabric Take-Up',
    desc: 'Sand-coated grip roller and continuous cloth batching beam winding high-density woven textile rolls.',
    temp: 27.0,
    wear: 18,
    vib: 1.0,
    lube: 'Optimal',
    rec: 'Surface grip friction within certified ISO 9001 quality parameters.'
  },
  rapier: {
    name: 'Rapier Weft Insertion System',
    category: 'Weft Insertion',
    desc: 'Flexible carbon-composite rapier tape and micro-gripper head transporting weft threads across the fabric width.',
    temp: 36.8,
    wear: 68,
    vib: 3.5,
    lube: 'Degraded',
    rec: 'Clean carbon guide tracks and replace worn rapier gripper tips to prevent weft insertion stoppages.'
  },
  beacon: {
    name: '3-Tier Industrial Telemetry Beacon',
    category: 'Supervisory Control',
    desc: 'Visual optical signal stack relaying real-time machine risk state, motor thermal warnings, and operator alerts.',
    temp: 24.0,
    wear: 5,
    vib: 0.2,
    lube: 'N/A',
    rec: 'SCADA telemetry uplink 100% synchronized with TexPulse AI cloud hub.'
  }
};

const FABRIC_3D_PALETTE = {
  Silk: { color: 0xFCD34D, roughness: 0.25, metalness: 0.4, name: 'Silk (Gold Satin)' },
  Cotton: { color: 0xF8FAFC, roughness: 0.85, metalness: 0.05, name: 'Cotton (Natural White)' },
  Wool: { color: 0x334155, roughness: 0.95, metalness: 0.0, name: 'Wool (Charcoal Twill)' },
  Polyester: { color: 0x06B6D4, roughness: 0.35, metalness: 0.2, name: 'Polyester (Cyan Poly)' },
  Linen: { color: 0xD6C7A1, roughness: 0.90, metalness: 0.0, name: 'Linen (Rustic Beige)' },
  Viscose: { color: 0x10B981, roughness: 0.40, metalness: 0.25, name: 'Viscose (Emerald Rayon)' },
  Nylon: { color: 0x1E3A8A, roughness: 0.30, metalness: 0.35, name: 'Nylon (Navy Ripstop)' }
};

function init3DDigitalTwin() {
  // Mode Buttons
  document.querySelectorAll('.btn-mode-pill').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-mode-pill').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const mode = btn.getAttribute('data-mode');
      set3DViewMode(mode);
    });
  });

  // Camera Presets
  document.querySelectorAll('.btn-cam-preset').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.btn-cam-preset').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const preset = btn.getAttribute('data-cam');
      set3DCameraPreset(preset);
    });
  });

  // Machine Selector
  document.getElementById('dt-machine-selector')?.addEventListener('change', (e) => {
    updateMachineDigitalTwin(e.target.value);
  });

  // Fabric Selector
  document.getElementById('dt-fabric-selector')?.addEventListener('change', (e) => {
    updateFabricMaterial(e.target.value);
  });

  // Speed Slider
  document.getElementById('dt-slider-speed')?.addEventListener('input', (e) => {
    const rpm = parseInt(e.target.value);
    state.digitalTwin.speedRpm = rpm;
    document.getElementById('dt-lbl-speed-slider').textContent = `${rpm} RPM`;
    document.getElementById('dt-hud-rpm-badge').textContent = `${rpm} RPM`;
    const picksHz = (rpm / 60).toFixed(1);
    document.getElementById('dt-hud-picks-rate').textContent = `${rpm} picks/min (${picksHz} Hz)`;
  });

  // Explosion Distance Slider
  document.getElementById('dt-slider-explosion')?.addEventListener('input', (e) => {
    const val = parseInt(e.target.value);
    state.digitalTwin.explosionDistance = val / 100;
    document.getElementById('dt-lbl-explosion').textContent = `${val}%`;
    if (state.digitalTwin.viewMode === 'exploded') {
      applyExplosionOffsets(state.digitalTwin.explosionDistance);
    }
  });

  // Play / Pause Motion
  document.getElementById('dt-btn-toggle-motion')?.addEventListener('click', () => {
    state.digitalTwin.isPlaying = !state.digitalTwin.isPlaying;
    const btn = document.getElementById('dt-btn-toggle-motion');
    const icon = document.getElementById('dt-icon-playpause');
    const lbl = document.getElementById('dt-lbl-playpause');
    if (state.digitalTwin.isPlaying) {
      icon.className = 'fa-solid fa-pause';
      lbl.textContent = 'Pause';
      btn.className = 'btn btn-xs btn-outline-cyan';
    } else {
      icon.className = 'fa-solid fa-play';
      lbl.textContent = 'Resume';
      btn.className = 'btn btn-xs btn-primary';
    }
  });

  // Vibration Toggle
  document.getElementById('dt-toggle-vibration')?.addEventListener('change', (e) => {
    state.digitalTwin.vibrationEnabled = e.target.checked;
  });

  // Particles Toggle
  document.getElementById('dt-toggle-particles')?.addEventListener('change', (e) => {
    state.digitalTwin.particlesEnabled = e.target.checked;
    if (state.digitalTwin.particles) {
      state.digitalTwin.particles.visible = e.target.checked;
    }
  });

  // Jump to RCA Button
  document.getElementById('btn-dt-goto-rca')?.addEventListener('click', () => {
    const mach = state.digitalTwin.targetMachineId || 'M02';
    if (window.loadMachineBatchesToRca) {
      window.loadMachineBatchesToRca(mach);
    }
  });
}

function load3DModelTab() {
  const container = document.getElementById('three-viewport');
  if (!container) return;

  if (!state.digitalTwin.isInitialized) {
    buildThreeScene(container);
    state.digitalTwin.isInitialized = true;
  } else {
    onWindowResize3D();
  }

  // Sync with selected machine
  const selector = document.getElementById('dt-machine-selector');
  if (selector) {
    updateMachineDigitalTwin(selector.value);
  }
}

function buildThreeScene(container) {
  if (typeof THREE === 'undefined') {
    console.error('Three.js is not loaded yet');
    container.innerHTML = '<div class="flex-center h-100 text-muted">Loading 3D Engine...</div>';
    return;
  }

  const width = container.clientWidth || 800;
  const height = container.clientHeight || 600;

  // 1. Scene
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x0a0f1d);
  scene.fog = new THREE.FogExp2(0x0a0f1d, 0.035);
  state.digitalTwin.scene = scene;

  // 2. Camera
  const camera = new THREE.PerspectiveCamera(42, width / height, 0.1, 100);
  camera.position.set(5.5, 4.2, 6.8);
  state.digitalTwin.camera = camera;

  // 3. Renderer
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setSize(width, height);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.15;
  container.innerHTML = '';
  container.appendChild(renderer.domElement);
  state.digitalTwin.renderer = renderer;

  // 4. OrbitControls
  if (typeof THREE.OrbitControls !== 'undefined') {
    const controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.05; // don't go below floor
    controls.minDistance = 2.0;
    controls.maxDistance = 18.0;
    controls.target.set(0, 1.2, 0);
    state.digitalTwin.controls = controls;
  }

  // 5. Lighting
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
  scene.add(ambientLight);

  const mainLight = new THREE.DirectionalLight(0xffffff, 1.2);
  mainLight.position.set(6, 10, 8);
  mainLight.castShadow = true;
  mainLight.shadow.mapSize.width = 1024;
  mainLight.shadow.mapSize.height = 1024;
  scene.add(mainLight);

  const cyanRimLight = new THREE.DirectionalLight(0x06B6D4, 0.9);
  cyanRimLight.position.set(-6, 5, -6);
  scene.add(cyanRimLight);

  const purpleFillLight = new THREE.PointLight(0xA855F7, 0.6, 12);
  purpleFillLight.position.set(0, 3, -3);
  scene.add(purpleFillLight);

  // 6. Floor Ground Grid
  const gridHelper = new THREE.GridHelper(16, 32, 0x06B6D4, 0x1E293B);
  gridHelper.position.y = -0.01;
  scene.add(gridHelper);

  const floorGeo = new THREE.PlaneGeometry(24, 24);
  const floorMat = new THREE.MeshStandardMaterial({
    color: 0x070B14,
    roughness: 0.85,
    metalness: 0.2
  });
  const floor = new THREE.Mesh(floorGeo, floorMat);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.02;
  floor.receiveShadow = true;
  scene.add(floor);

  // 7. Raycaster for Part Inspection
  state.digitalTwin.raycaster = new THREE.Raycaster();
  state.digitalTwin.mouse = new THREE.Vector2();

  renderer.domElement.addEventListener('click', on3DPointerClick);
  window.addEventListener('resize', onWindowResize3D);

  // 8. Build Procedural Textile Loom Model
  constructLoomModel(scene);

  // 9. Construct Defect Particle System
  constructParticleStream(scene);

  // 10. Start Animation Loop
  animate3D();
}

function constructLoomModel(scene) {
  const parts = state.digitalTwin.parts;
  const groups = state.digitalTwin.groups;

  // Master Root Group
  const loomRoot = new THREE.Group();
  scene.add(loomRoot);
  groups['loomRoot'] = loomRoot;

  // Common Materials
  const matCastIron = new THREE.MeshStandardMaterial({ color: 0x1E293B, roughness: 0.6, metalness: 0.8 });
  const matChassisBlue = new THREE.MeshStandardMaterial({ color: 0x0F172A, roughness: 0.5, metalness: 0.7 });
  const matSteel = new THREE.MeshStandardMaterial({ color: 0xCBD5E1, roughness: 0.25, metalness: 0.9 });
  const matBronze = new THREE.MeshStandardMaterial({ color: 0xD97706, roughness: 0.35, metalness: 0.85 });
  const matMotor = new THREE.MeshStandardMaterial({ color: 0x0284C7, roughness: 0.4, metalness: 0.6 });
  const matRubber = new THREE.MeshStandardMaterial({ color: 0x111827, roughness: 0.9, metalness: 0.1 });
  const matSafety = new THREE.MeshStandardMaterial({ color: 0xF59E0B, roughness: 0.4, metalness: 0.3 });
  const matCloth = new THREE.MeshStandardMaterial({ color: 0xFCD34D, roughness: 0.3, metalness: 0.35 });
  const matYarn = new THREE.MeshStandardMaterial({ color: 0xF1F5F9, roughness: 0.8, metalness: 0.1 });
  const matAlu = new THREE.MeshStandardMaterial({ color: 0x94A3B8, roughness: 0.3, metalness: 0.85 });

  state.digitalTwin.materials['cloth'] = matCloth;
  state.digitalTwin.materials['matCastIron'] = matCastIron;
  state.digitalTwin.materials['matSteel'] = matSteel;
  state.digitalTwin.materials['matMotor'] = matMotor;

  // -------------------------------------------------------------
  // A. BASE CHASSIS & SIDE FRAMES
  // -------------------------------------------------------------
  const groupChassis = new THREE.Group();
  groupChassis.userData = { explodedOffset: new THREE.Vector3(0, 0, 0), partId: 'chassis' };
  loomRoot.add(groupChassis);
  groups['chassis'] = groupChassis;

  // Left Side Frame Plate
  const sidePlateGeo = new THREE.BoxGeometry(0.2, 2.4, 3.2);
  const leftPlate = new THREE.Mesh(sidePlateGeo, matChassisBlue);
  leftPlate.position.set(-2.0, 1.2, 0);
  leftPlate.castShadow = true;
  leftPlate.receiveShadow = true;
  groupChassis.add(leftPlate);

  // Right Side Frame Plate
  const rightPlate = new THREE.Mesh(sidePlateGeo, matChassisBlue);
  rightPlate.position.set(2.0, 1.2, 0);
  rightPlate.castShadow = true;
  rightPlate.receiveShadow = true;
  groupChassis.add(rightPlate);

  // Base Rails & Plinths
  const baseRailGeo = new THREE.BoxGeometry(4.4, 0.25, 0.4);
  const frontRail = new THREE.Mesh(baseRailGeo, matCastIron);
  frontRail.position.set(0, 0.125, 1.4);
  groupChassis.add(frontRail);

  const backRail = new THREE.Mesh(baseRailGeo, matCastIron);
  backRail.position.set(0, 0.125, -1.4);
  groupChassis.add(backRail);

  // Top Overhead Gantry Bar
  const gantryGeo = new THREE.BoxGeometry(4.2, 0.15, 0.25);
  const topGantry = new THREE.Mesh(gantryGeo, matSteel);
  topGantry.position.set(0, 2.35, 0);
  groupChassis.add(topGantry);

  // Safety Hazard Bar
  const safetyBarGeo = new THREE.CylinderGeometry(0.04, 0.04, 4.2, 16);
  const safetyBar = new THREE.Mesh(safetyBarGeo, matSafety);
  safetyBar.rotation.z = Math.PI / 2;
  safetyBar.position.set(0, 1.0, 1.6);
  groupChassis.add(safetyBar);

  // -------------------------------------------------------------
  // B. MAIN DRIVE MOTOR & TRANSMISSION (LEFT SIDE)
  // -------------------------------------------------------------
  const groupMotor = new THREE.Group();
  groupMotor.userData = { explodedOffset: new THREE.Vector3(-1.8, 0, 0), partId: 'motor' };
  loomRoot.add(groupMotor);
  groups['motor'] = groupMotor;

  // Motor Housing (Cylinder)
  const motorGeo = new THREE.CylinderGeometry(0.38, 0.38, 0.9, 24);
  const motorMesh = new THREE.Mesh(motorGeo, matMotor);
  motorMesh.rotation.z = Math.PI / 2;
  motorMesh.position.set(-2.5, 0.6, -0.6);
  motorMesh.castShadow = true;
  motorMesh.userData = { partId: 'motor', name: 'Main AC Drive Motor' };
  groupMotor.add(motorMesh);
  parts['motorBody'] = motorMesh;

  // Motor Cooling Fins
  for (let i = 0; i < 6; i++) {
    const finGeo = new THREE.TorusGeometry(0.42, 0.02, 8, 24);
    const finMesh = new THREE.Mesh(finGeo, matCastIron);
    finMesh.rotation.y = Math.PI / 2;
    finMesh.position.set(-2.8 + i * 0.12, 0.6, -0.6);
    groupMotor.add(finMesh);
  }

  // Motor Output Pulley
  const pulleyGeo = new THREE.CylinderGeometry(0.22, 0.22, 0.12, 24);
  const drivePulley = new THREE.Mesh(pulleyGeo, matSteel);
  drivePulley.rotation.z = Math.PI / 2;
  drivePulley.position.set(-2.02, 0.6, -0.6);
  groupMotor.add(drivePulley);
  parts['drivePulley'] = drivePulley;

  // Crankshaft Driven Pulley (Flywheel)
  const flywheelGeo = new THREE.CylinderGeometry(0.48, 0.48, 0.12, 32);
  const flywheel = new THREE.Mesh(flywheelGeo, matBronze);
  flywheel.rotation.z = Math.PI / 2;
  flywheel.position.set(-2.02, 1.3, -0.2);
  groupMotor.add(flywheel);
  parts['flywheel'] = flywheel;

  // V-Belt (Tensioned between pulleys)
  const beltGeo = new THREE.BoxGeometry(0.08, 0.8, 0.5);
  const beltMesh = new THREE.Mesh(beltGeo, matRubber);
  beltMesh.position.set(-2.02, 0.95, -0.4);
  groupMotor.add(beltMesh);

  // -------------------------------------------------------------
  // C. WARP SUPPLY BEAM (REAR)
  // -------------------------------------------------------------
  const groupWarp = new THREE.Group();
  groupWarp.userData = { explodedOffset: new THREE.Vector3(0, 0, -1.8), partId: 'warpBeam' };
  loomRoot.add(groupWarp);
  groups['warpBeam'] = groupWarp;

  // Main Warp Beam Core Cylinder
  const warpCoreGeo = new THREE.CylinderGeometry(0.45, 0.45, 3.6, 32);
  const warpCore = new THREE.Mesh(warpCoreGeo, matYarn);
  warpCore.rotation.z = Math.PI / 2;
  warpCore.position.set(0, 0.7, -1.2);
  warpCore.castShadow = true;
  warpCore.userData = { partId: 'warpBeam', name: 'Warp Supply Beam' };
  groupWarp.add(warpCore);
  parts['warpCore'] = warpCore;

  // Flanges (Left & Right)
  const flangeGeo = new THREE.CylinderGeometry(0.65, 0.65, 0.08, 32);
  const leftFlange = new THREE.Mesh(flangeGeo, matCastIron);
  leftFlange.rotation.z = Math.PI / 2;
  leftFlange.position.set(-1.8, 0.7, -1.2);
  groupWarp.add(leftFlange);

  const rightFlange = new THREE.Mesh(flangeGeo, matCastIron);
  rightFlange.rotation.z = Math.PI / 2;
  rightFlange.position.set(1.8, 0.7, -1.2);
  groupWarp.add(rightFlange);

  // -------------------------------------------------------------
  // D. BACK-REST & TENSION ROLLER
  // -------------------------------------------------------------
  const groupTension = new THREE.Group();
  groupTension.userData = { explodedOffset: new THREE.Vector3(0, 0.8, -1.0), partId: 'tensioner' };
  loomRoot.add(groupTension);
  groups['tensioner'] = groupTension;

  const tensionBarGeo = new THREE.CylinderGeometry(0.1, 0.1, 3.8, 24);
  const tensionBar = new THREE.Mesh(tensionBarGeo, matSteel);
  tensionBar.rotation.z = Math.PI / 2;
  tensionBar.position.set(0, 1.45, -0.9);
  tensionBar.userData = { partId: 'tensioner', name: 'Back-Rest Tension Bar' };
  groupTension.add(tensionBar);
  parts['tensionBar'] = tensionBar;

  // Tension Springs
  const springGeo = new THREE.CylinderGeometry(0.04, 0.04, 0.35, 12);
  const leftSpring = new THREE.Mesh(springGeo, matBronze);
  leftSpring.position.set(-1.85, 1.25, -0.9);
  groupTension.add(leftSpring);

  const rightSpring = new THREE.Mesh(springGeo, matBronze);
  rightSpring.position.set(1.85, 1.25, -0.9);
  groupTension.add(rightSpring);

  // -------------------------------------------------------------
  // E. 4-FRAME HARNESS & HEALDS (SHEDDING ZONE)
  // -------------------------------------------------------------
  const groupHarness = new THREE.Group();
  groupHarness.userData = { explodedOffset: new THREE.Vector3(0, 1.8, 0), partId: 'harness' };
  loomRoot.add(groupHarness);
  groups['harness'] = groupHarness;

  const healdFrames = [];
  const frameGeo = new THREE.BoxGeometry(3.6, 0.9, 0.05);
  const heddleWireGeo = new THREE.BoxGeometry(3.5, 0.75, 0.02);

  for (let f = 0; f < 4; f++) {
    const frameGroup = new THREE.Group();
    const zPos = -0.3 + f * 0.14;
    frameGroup.position.set(0, 1.35, zPos);

    // Frame Border
    const frameBorder = new THREE.Mesh(frameGeo, matAlu);
    frameBorder.castShadow = true;
    frameBorder.userData = { partId: 'harness', name: `Heald Frame ${f + 1}` };
    frameGroup.add(frameBorder);

    // Wire Heddle Screen
    const heddleScreen = new THREE.Mesh(heddleWireGeo, matSteel);
    frameGroup.add(heddleScreen);

    groupHarness.add(frameGroup);
    healdFrames.push(frameGroup);
  }
  parts['healdFrames'] = healdFrames;

  // -------------------------------------------------------------
  // F. SLEY BED & REED BEATER
  // -------------------------------------------------------------
  const groupReed = new THREE.Group();
  groupReed.userData = { explodedOffset: new THREE.Vector3(0, 0.8, 0.8), partId: 'reed' };
  loomRoot.add(groupReed);
  groups['reed'] = groupReed;

  const sleyArmGeo = new THREE.BoxGeometry(3.7, 0.2, 0.3);
  const sleyArm = new THREE.Mesh(sleyArmGeo, matCastIron);
  sleyArm.position.set(0, 1.15, 0.4);
  groupReed.add(sleyArm);

  const reedCombGeo = new THREE.BoxGeometry(3.6, 0.6, 0.04);
  const reedComb = new THREE.Mesh(reedCombGeo, matSteel);
  reedComb.position.set(0, 1.45, 0.4);
  reedComb.castShadow = true;
  reedComb.userData = { partId: 'reed', name: 'Sley & Reed Comb Beater' };
  groupReed.add(reedComb);
  parts['reedComb'] = reedComb;

  // -------------------------------------------------------------
  // G. RAPIER WEFT INSERTION ARMS
  // -------------------------------------------------------------
  const groupRapier = new THREE.Group();
  groupRapier.userData = { explodedOffset: new THREE.Vector3(1.8, 0, 0.6), partId: 'rapier' };
  loomRoot.add(groupRapier);
  groups['rapier'] = groupRapier;

  // Left Rapier Tape Guide
  const rapierTapeGeo = new THREE.BoxGeometry(1.8, 0.04, 0.08);
  const leftRapier = new THREE.Mesh(rapierTapeGeo, matAlu);
  leftRapier.position.set(-1.2, 1.25, 0.42);
  leftRapier.userData = { partId: 'rapier', name: 'Rapier Weft Carrier' };
  groupRapier.add(leftRapier);
  parts['leftRapier'] = leftRapier;

  const rightRapier = new THREE.Mesh(rapierTapeGeo, matAlu);
  rightRapier.position.set(1.2, 1.25, 0.42);
  groupRapier.add(rightRapier);
  parts['rightRapier'] = rightRapier;

  // -------------------------------------------------------------
  // H. WOVEN CLOTH & TAKE-UP BEAM (FRONT)
  // -------------------------------------------------------------
  const groupCloth = new THREE.Group();
  groupCloth.userData = { explodedOffset: new THREE.Vector3(0, 0, 1.8), partId: 'clothRoll' };
  loomRoot.add(groupCloth);
  groups['clothRoll'] = groupCloth;

  // Front Cloth Winding Roll
  const clothRollGeo = new THREE.CylinderGeometry(0.35, 0.35, 3.6, 32);
  const clothRollMesh = new THREE.Mesh(clothRollGeo, matCloth);
  clothRollMesh.rotation.z = Math.PI / 2;
  clothRollMesh.position.set(0, 0.65, 1.15);
  clothRollMesh.castShadow = true;
  clothRollMesh.userData = { partId: 'clothRoll', name: 'Woven Cloth Roll' };
  groupCloth.add(clothRollMesh);
  parts['clothRollMesh'] = clothRollMesh;

  // Woven Fabric Surface Plane (Spans from reed to front roll)
  const fabricPlaneGeo = new THREE.PlaneGeometry(3.5, 0.85);
  const fabricPlane = new THREE.Mesh(fabricPlaneGeo, matCloth);
  fabricPlane.rotation.x = -Math.PI / 2 - 0.25;
  fabricPlane.position.set(0, 1.15, 0.75);
  groupCloth.add(fabricPlane);
  parts['fabricPlane'] = fabricPlane;

  // -------------------------------------------------------------
  // I. 3-TIER STATUS BEACON TOWER
  // -------------------------------------------------------------
  const groupBeacon = new THREE.Group();
  groupBeacon.userData = { explodedOffset: new THREE.Vector3(1.8, 1.5, -1.2), partId: 'beacon' };
  loomRoot.add(groupBeacon);
  groups['beacon'] = groupBeacon;

  // Pole
  const poleGeo = new THREE.CylinderGeometry(0.03, 0.03, 1.2, 16);
  const pole = new THREE.Mesh(poleGeo, matCastIron);
  pole.position.set(1.9, 2.5, -1.1);
  groupBeacon.add(pole);

  // Red, Amber, Green Lights
  const lightGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.12, 16);
  
  const matRed = new THREE.MeshStandardMaterial({ color: 0xEF4444, emissive: 0xEF4444, emissiveIntensity: 0.2 });
  const redLight = new THREE.Mesh(lightGeo, matRed);
  redLight.position.set(1.9, 3.25, -1.1);
  redLight.userData = { partId: 'beacon', name: 'Signal Beacon Tower' };
  groupBeacon.add(redLight);
  parts['beaconRed'] = redLight;

  const matAmber = new THREE.MeshStandardMaterial({ color: 0xF59E0B, emissive: 0xF59E0B, emissiveIntensity: 0.8 });
  const amberLight = new THREE.Mesh(lightGeo, matAmber);
  amberLight.position.set(1.9, 3.10, -1.1);
  amberLight.userData = { partId: 'beacon', name: 'Signal Beacon Tower' };
  groupBeacon.add(amberLight);
  parts['beaconAmber'] = amberLight;

  const matGreen = new THREE.MeshStandardMaterial({ color: 0x10B981, emissive: 0x10B981, emissiveIntensity: 0.2 });
  const greenLight = new THREE.Mesh(lightGeo, matGreen);
  greenLight.position.set(1.9, 2.95, -1.1);
  greenLight.userData = { partId: 'beacon', name: 'Signal Beacon Tower' };
  groupBeacon.add(greenLight);
  parts['beaconGreen'] = greenLight;
}

function constructParticleStream(scene) {
  const particleCount = 120;
  const geometry = new THREE.BufferGeometry();
  const positions = new Float32Array(particleCount * 3);
  const velocities = [];

  for (let i = 0; i < particleCount; i++) {
    positions[i * 3 + 0] = (Math.random() - 0.5) * 3.2;
    positions[i * 3 + 1] = 1.1 + Math.random() * 0.6;
    positions[i * 3 + 2] = 0.2 + (Math.random() - 0.5) * 0.8;

    velocities.push({
      x: (Math.random() - 0.5) * 0.02,
      y: 0.01 + Math.random() * 0.025,
      z: 0.01 + Math.random() * 0.02,
      origY: 1.1
    });
  }

  geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));

  const material = new THREE.PointsMaterial({
    color: 0xEF4444,
    size: 0.06,
    transparent: true,
    opacity: 0.75,
    blending: THREE.AdditiveBlending
  });

  const particles = new THREE.Points(geometry, material);
  scene.add(particles);
  state.digitalTwin.particles = particles;
  particles.userData = { velocities: velocities };
}

let kinematicAngle = 0;

function animate3D() {
  state.digitalTwin.animationId = requestAnimationFrame(animate3D);

  const dtState = state.digitalTwin;
  const now = performance.now();
  const delta = (now - dtState.lastFrameTime) / 1000;
  dtState.lastFrameTime = now;

  // FPS Counter
  dtState.frameCount++;
  if (now - dtState.fpsUpdateTime > 500) {
    const fps = Math.round((dtState.frameCount * 1000) / (now - dtState.fpsUpdateTime));
    dtState.fps = fps;
    dtState.frameCount = 0;
    dtState.fpsUpdateTime = now;
    const fpsEl = document.getElementById('dt-hud-fps');
    if (fpsEl) fpsEl.textContent = `${fps} FPS`;
  }

  // 1. Mechanical Kinematics
  if (dtState.isPlaying && dtState.parts) {
    const speedMultiplier = dtState.speedRpm / 60; // revolutions per second
    kinematicAngle += delta * speedMultiplier * Math.PI * 2;

    const parts = dtState.parts;

    // Rotate Pulleys & Motor
    if (parts.drivePulley) parts.drivePulley.rotation.x += delta * speedMultiplier * Math.PI * 2;
    if (parts.flywheel) parts.flywheel.rotation.x += delta * speedMultiplier * Math.PI;

    // Rotate Rollers
    if (parts.warpCore) parts.warpCore.rotation.x += delta * 0.15;
    if (parts.clothRollMesh) parts.clothRollMesh.rotation.x += delta * 0.15;

    // Heald Frames Shedding Motion (Sinusoidal vertical stroke)
    if (parts.healdFrames && parts.healdFrames.length === 4) {
      const stroke = 0.16;
      parts.healdFrames[0].position.y = 1.35 + Math.sin(kinematicAngle) * stroke;
      parts.healdFrames[1].position.y = 1.35 - Math.sin(kinematicAngle) * stroke;
      parts.healdFrames[2].position.y = 1.35 + Math.cos(kinematicAngle) * stroke;
      parts.healdFrames[3].position.y = 1.35 - Math.cos(kinematicAngle) * stroke;
    }

    // Reed Beater Reciprocation
    if (parts.reedComb) {
      parts.reedComb.position.z = 0.4 + Math.sin(kinematicAngle) * 0.08;
    }

    // Rapier Shuttle Traverse
    if (parts.leftRapier && parts.rightRapier) {
      const traverse = Math.sin(kinematicAngle * 2) * 0.9;
      parts.leftRapier.position.x = -1.2 + traverse;
      parts.rightRapier.position.x = 1.2 - traverse;
    }

    // Vibration Jitter
    if (dtState.vibrationEnabled && dtState.groups['loomRoot']) {
      const vibIntensity = (dtState.speedRpm / 1200) * 0.006;
      dtState.groups['loomRoot'].position.y = (Math.random() - 0.5) * vibIntensity;
      dtState.groups['loomRoot'].position.x = (Math.random() - 0.5) * vibIntensity * 0.5;
    } else if (dtState.groups['loomRoot']) {
      dtState.groups['loomRoot'].position.set(0, 0, 0);
    }
  }

  // 2. Animate Defect Particles
  if (dtState.particles && dtState.particles.visible) {
    const pos = dtState.particles.geometry.attributes.position.array;
    const vels = dtState.particles.userData.velocities;
    for (let i = 0; i < vels.length; i++) {
      pos[i * 3 + 0] += vels[i].x;
      pos[i * 3 + 1] += vels[i].y;
      pos[i * 3 + 2] += vels[i].z;

      // Reset when floating too far
      if (pos[i * 3 + 1] > 2.8) {
        pos[i * 3 + 0] = (Math.random() - 0.5) * 3.2;
        pos[i * 3 + 1] = vels[i].origY;
        pos[i * 3 + 2] = 0.2 + (Math.random() - 0.5) * 0.8;
      }
    }
    dtState.particles.geometry.attributes.position.needsUpdate = true;
  }

  // 3. Update Controls & Render
  if (dtState.controls) dtState.controls.update();
  if (dtState.renderer && dtState.scene && dtState.camera) {
    dtState.renderer.render(dtState.scene, dtState.camera);
  }
}

function set3DViewMode(mode) {
  state.digitalTwin.viewMode = mode;
  const groups = state.digitalTwin.groups;
  const expControl = document.getElementById('dt-exploded-control-group');

  if (mode === 'exploded') {
    expControl?.classList.remove('hidden');
    applyExplosionOffsets(state.digitalTwin.explosionDistance);
  } else {
    expControl?.classList.add('hidden');
    applyExplosionOffsets(0);
  }

  // Traverse and update materials
  if (state.digitalTwin.scene) {
    state.digitalTwin.scene.traverse((obj) => {
      if (obj.isMesh && obj.userData && obj.userData.partId) {
        const partId = obj.userData.partId;
        applyMaterialForMode(obj, mode, partId);
      }
    });
  }
}

function applyMaterialForMode(mesh, mode, partId) {
  if (mode === 'realistic') {
    if (partId === 'motor') mesh.material = state.digitalTwin.materials['matMotor'];
    else if (partId === 'clothRoll') mesh.material = state.digitalTwin.materials['cloth'];
    else if (partId === 'warpBeam') mesh.material = new THREE.MeshStandardMaterial({ color: 0xF1F5F9, roughness: 0.8 });
    else mesh.material.wireframe = false;
  } else if (mode === 'thermal') {
    mesh.material.wireframe = false;
    if (partId === 'motor') {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0xEF4444, emissive: 0xEF4444, emissiveIntensity: 0.6 });
    } else if (partId === 'rapier' || partId === 'reed') {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0xF59E0B, emissive: 0xF59E0B, emissiveIntensity: 0.4 });
    } else if (partId === 'harness') {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0xEAB308, emissive: 0xEAB308, emissiveIntensity: 0.2 });
    } else {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0x0284C7, roughness: 0.6 });
    }
  } else if (mode === 'stress') {
    mesh.material.wireframe = false;
    if (partId === 'harness' || partId === 'rapier') {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0xEC4899, emissive: 0xEC4899, emissiveIntensity: 0.5 });
    } else if (partId === 'motor' || partId === 'tensioner') {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0xF97316, emissive: 0xF97316, emissiveIntensity: 0.3 });
    } else {
      mesh.material = new THREE.MeshStandardMaterial({ color: 0x0E7490, roughness: 0.5 });
    }
  } else if (mode === 'wireframe') {
    mesh.material = new THREE.MeshStandardMaterial({
      color: 0x06B6D4,
      wireframe: true,
      transparent: true,
      opacity: 0.7
    });
  }
}

function applyExplosionOffsets(distance) {
  const groups = state.digitalTwin.groups;
  for (const [key, grp] of Object.entries(groups)) {
    if (grp.userData && grp.userData.explodedOffset) {
      const baseOffset = grp.userData.explodedOffset;
      grp.position.x = baseOffset.x * distance * 1.5;
      grp.position.y = baseOffset.y * distance * 1.5;
      grp.position.z = baseOffset.z * distance * 1.5;
    }
  }
}

function set3DCameraPreset(preset) {
  state.digitalTwin.cameraPreset = preset;
  const cam = state.digitalTwin.camera;
  const ctrl = state.digitalTwin.controls;
  if (!cam || !ctrl) return;

  const presets = {
    overview: { pos: [5.5, 4.2, 6.8], target: [0, 1.2, 0] },
    weaving: { pos: [0.2, 2.2, 2.4], target: [0, 1.35, 0.2] },
    motor: { pos: [-3.6, 1.4, -0.6], target: [-2.2, 0.8, -0.5] },
    rollers: { pos: [0.0, 3.2, -4.2], target: [0, 1.0, -0.5] },
    top: { pos: [0.0, 9.5, 0.1], target: [0, 1.0, 0] },
    reset: { pos: [5.5, 4.2, 6.8], target: [0, 1.2, 0] }
  };

  const p = presets[preset] || presets.overview;
  
  // Smoothly move camera
  cam.position.set(p.pos[0], p.pos[1], p.pos[2]);
  ctrl.target.set(p.target[0], p.target[1], p.target[2]);
  ctrl.update();
}

function on3DPointerClick(event) {
  const rect = state.digitalTwin.renderer.domElement.getBoundingClientRect();
  state.digitalTwin.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  state.digitalTwin.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  state.digitalTwin.raycaster.setFromCamera(state.digitalTwin.mouse, state.digitalTwin.camera);
  const intersects = state.digitalTwin.raycaster.intersectObjects(state.digitalTwin.scene.children, true);

  for (let hit of intersects) {
    if (hit.object.userData && hit.object.userData.partId) {
      const partKey = hit.object.userData.partId;
      inspect3DComponent(partKey);
      break;
    }
  }
}

function inspect3DComponent(partKey) {
  const comp = COMPONENT_DATA[partKey] || COMPONENT_DATA.motor;
  state.digitalTwin.activeComponent = partKey;

  document.getElementById('dt-part-category-badge').textContent = comp.category;
  document.getElementById('dt-part-name').textContent = comp.name;
  document.getElementById('dt-part-desc').textContent = comp.desc;
  document.getElementById('dt-part-temp').textContent = `${comp.temp}°C`;
  document.getElementById('dt-part-wear').textContent = `${comp.wear}%`;
  document.getElementById('dt-part-vib').textContent = `${comp.vib} mm/s`;
  document.getElementById('dt-part-lube').textContent = comp.lube;
  document.getElementById('dt-part-rec').textContent = comp.rec;

  const tempFill = document.getElementById('dt-part-temp-fill');
  if (tempFill) {
    tempFill.style.width = `${Math.min(100, (comp.temp / 60) * 100)}%`;
    tempFill.style.background = comp.temp > 40 ? 'var(--risk-danger)' : (comp.temp > 32 ? 'var(--risk-warning)' : 'var(--risk-normal)');
  }

  const wearFill = document.getElementById('dt-part-wear-fill');
  if (wearFill) {
    wearFill.style.width = `${comp.wear}%`;
    wearFill.style.background = comp.wear > 70 ? 'var(--risk-danger)' : (comp.wear > 50 ? 'var(--risk-warning)' : 'var(--risk-normal)');
  }
}

function updateMachineDigitalTwin(machineId) {
  state.digitalTwin.targetMachineId = machineId;
  document.getElementById('dt-hud-machine-id').textContent = `${machineId} - Weaving Unit`;
  document.getElementById('dt-btn-mach-id').textContent = machineId;

  const redBeacon = document.getElementById('dt-beacon-red');
  const amberBeacon = document.getElementById('dt-beacon-amber');
  const greenBeacon = document.getElementById('dt-beacon-green');
  const statusText = document.getElementById('dt-hud-status-text');
  const riskBadge = document.getElementById('dt-mach-risk-badge');

  // Specific telemetry configs per machine
  if (machineId === 'M02') {
    redBeacon?.classList.remove('active');
    amberBeacon?.classList.add('active');
    greenBeacon?.classList.remove('active');
    statusText.textContent = 'ELEVATED BEARING WEAR';
    statusText.style.color = 'var(--risk-warning)';
    riskBadge.textContent = 'HIGH RISK (6.5% Waste)';
    riskBadge.className = 'badge badge-danger';
    document.getElementById('dt-mach-age').textContent = '6.2 Years';
    document.getElementById('dt-mach-maint').textContent = '78 Days (Overdue)';
    document.getElementById('dt-mach-failure').textContent = 'Mechanical Wear & Friction';
  } else if (machineId === 'M08' || machineId === 'M10') {
    redBeacon?.classList.remove('active');
    amberBeacon?.classList.remove('active');
    greenBeacon?.classList.add('active');
    statusText.textContent = 'NOMINAL HEALTH & CALIBRATION';
    statusText.style.color = 'var(--risk-normal)';
    riskBadge.textContent = 'OPTIMAL (3.2% Waste)';
    riskBadge.className = 'badge badge-normal';
    document.getElementById('dt-mach-age').textContent = '1.5 Years';
    document.getElementById('dt-mach-maint').textContent = '14 Days (Good)';
    document.getElementById('dt-mach-failure').textContent = 'None (Within Bounds)';
  } else {
    redBeacon?.classList.remove('active');
    amberBeacon?.classList.remove('active');
    greenBeacon?.classList.add('active');
    statusText.textContent = 'OPERATIONAL (STANDARD)';
    statusText.style.color = 'var(--cyan)';
    riskBadge.textContent = 'MODERATE RISK (4.8% Waste)';
    riskBadge.className = 'badge badge-subtle';
    document.getElementById('dt-mach-age').textContent = '3.8 Years';
    document.getElementById('dt-mach-maint').textContent = '35 Days (Nominal)';
    document.getElementById('dt-mach-failure').textContent = 'Speed Stress';
  }
}

function updateFabricMaterial(fabricType) {
  state.digitalTwin.targetFabric = fabricType;
  const cfg = FABRIC_3D_PALETTE[fabricType] || FABRIC_3D_PALETTE.Silk;

  if (state.digitalTwin.materials['cloth']) {
    state.digitalTwin.materials['cloth'].color.setHex(cfg.color);
    state.digitalTwin.materials['cloth'].roughness = cfg.roughness;
    state.digitalTwin.materials['cloth'].metalness = cfg.metalness;
  }
}

function onWindowResize3D() {
  const container = document.getElementById('three-viewport');
  const renderer = state.digitalTwin.renderer;
  const camera = state.digitalTwin.camera;

  if (!container || !renderer || !camera) return;

  const width = container.clientWidth;
  const height = container.clientHeight;

  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
}

window.load3DModelTab = load3DModelTab;
window.set3DViewMode = set3DViewMode;
window.set3DCameraPreset = set3DCameraPreset;
window.inspect3DComponent = inspect3DComponent;


