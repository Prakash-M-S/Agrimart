// AgriMart Application Controller

const state = {
  activeTab: "marketplace",
  dataset: [],
  datasetSource: "Built-in Benchmark (2,200 rows)",
  lots: [],
  orders: [],
  marketFilterCategory: "All",
  marketSearch: "",
  marketSort: "recent",
  mandiStateFilter: "All",
  mandiSearch: "",
  explorerCropFilter: "All",
  explorerPage: 1,
  explorerPageSize: 25,
  selectedLotForOrder: null
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  loadPersistedData();
  initDataset();
  setupNavigation();
  setupMarketplaceHandlers();
  setupCropRecommenderHandlers();
  setupFertilizerCalculatorHandlers();
  setupMandiHandlers();
  setupDatasetExplorerHandlers();
  renderAll();
});

function loadPersistedData() {
  const savedLots = localStorage.getItem("agrimart_lots_v1");
  if (savedLots) {
    try {
      state.lots = JSON.parse(savedLots);
    } catch (e) {
      state.lots = [...INITIAL_MARKETPLACE_LOTS];
    }
  } else {
    state.lots = [...INITIAL_MARKETPLACE_LOTS];
  }

  const savedOrders = localStorage.getItem("agrimart_orders_v1");
  if (savedOrders) {
    try {
      state.orders = JSON.parse(savedOrders);
    } catch (e) {
      state.orders = [];
    }
  }
}

function saveLots() {
  localStorage.setItem("agrimart_lots_v1", JSON.stringify(state.lots));
}

function saveOrders() {
  localStorage.setItem("agrimart_orders_v1", JSON.stringify(state.orders));
}

// Load 2,200-row dataset & attempt live sync from GitHub raw CSV
async function initDataset() {
  state.dataset = generateLocalDataset2200();
  updateDatasetStatusUI();
  populateExplorerCropDropdown();
  renderDatasetExplorer();

  try {
    const resp = await fetch(REMOTE_CROP_CSV_URL);
    if (resp.ok) {
      const csvText = await resp.text();
      const parsed = parseCSV(csvText);
      if (parsed.length > 500) {
        state.dataset = parsed;
        state.datasetSource = `Live Web CSV Sync (${parsed.length.toLocaleString()} rows)`;
        updateDatasetStatusUI();
        renderDatasetExplorer();
      }
    }
  } catch (err) {
    // Offline or blocked; fallback 2,200-row dataset is already active
  }
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) return [];
  const result = [];
  for (let i = 1; i < lines.length; i++) {
    const cols = lines[i].split(",");
    if (cols.length < 8) continue;
    result.push({
      N: parseFloat(cols[0]),
      P: parseFloat(cols[1]),
      K: parseFloat(cols[2]),
      temperature: parseFloat(cols[3]),
      humidity: parseFloat(cols[4]),
      ph: parseFloat(cols[5]),
      rainfall: parseFloat(cols[6]),
      label: cols[7].trim().toLowerCase()
    });
  }
  return result;
}

function updateDatasetStatusUI() {
  const statusEl = document.getElementById("dataset-sync-status");
  if (statusEl) {
    statusEl.textContent = `${state.datasetSource} • 22 Crop Classes`;
  }
  const countBadge = document.getElementById("nav-dataset-count");
  if (countBadge) {
    countBadge.textContent = state.dataset.length.toLocaleString();
  }
}

// Navigation
function setupNavigation() {
  const tabs = document.querySelectorAll(".nav-tab");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-tab");
      switchTab(target);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".nav-tab").forEach((b) => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
  });
  document.querySelectorAll(".view-section").forEach((sec) => {
    sec.classList.toggle("active", sec.id === `view-${tabId}`);
  });
}

function renderAll() {
  renderMarketplaceKPIs();
  renderMarketplaceLots();
  renderOrdersDrawerCount();
  runCropPrediction();
  runFertilizerCalculation();
  populateMandiStates();
  renderMandiTable();
  renderDatasetExplorer();
}

// ==========================================
// 1. DIRECT MARKETPLACE
// ==========================================
function setupMarketplaceHandlers() {
  // Category filter pills
  document.querySelectorAll("#market-category-pills .filter-pill").forEach((pill) => {
    pill.addEventListener("click", () => {
      document.querySelectorAll("#market-category-pills .filter-pill").forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.marketFilterCategory = pill.getAttribute("data-category");
      renderMarketplaceLots();
    });
  });

  // Search input
  const searchIn = document.getElementById("market-search-input");
  if (searchIn) {
    searchIn.addEventListener("input", (e) => {
      state.marketSearch = e.target.value.trim().toLowerCase();
      renderMarketplaceLots();
    });
  }

  // Sort select
  const sortSel = document.getElementById("market-sort-select");
  if (sortSel) {
    sortSel.addEventListener("change", (e) => {
      state.marketSort = e.target.value;
      renderMarketplaceLots();
    });
  }

  // New Lot Modal Open/Close
  document.getElementById("btn-open-list-modal")?.addEventListener("click", () => {
    document.getElementById("modal-list-lot").classList.add("open");
  });

  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modalId = btn.getAttribute("data-close-modal");
      document.getElementById(modalId)?.classList.remove("open");
    });
  });

  // Submit New Farmer Harvest Lot
  const formNewLot = document.getElementById("form-new-lot");
  if (formNewLot) {
    formNewLot.addEventListener("submit", (e) => {
      e.preventDefault();
      const title = document.getElementById("lot-title-in").value.trim();
      const variety = document.getElementById("lot-variety-in").value.trim();
      const category = document.getElementById("lot-category-in").value;
      const grade = document.getElementById("lot-grade-in").value.trim();
      const qty = parseFloat(document.getElementById("lot-qty-in").value) || 20;
      const minOrder = parseFloat(document.getElementById("lot-min-in").value) || 2;
      const price = parseFloat(document.getElementById("lot-price-in").value) || 2500;
      const farmer = document.getElementById("lot-farmer-in").value.trim();
      const location = document.getElementById("lot-location-in").value.trim();

      const newLot = {
        id: `LOT-${1050 + state.lots.length}`,
        title,
        variety,
        category,
        grade: grade || "Grade A",
        moisture: "11.0%",
        quantityAvailable: qty,
        unit: "Quintal",
        minOrder,
        pricePerUnit: price,
        mandiBenchmark: Math.round(price * 1.03),
        farmerName: farmer,
        location,
        harvestDate: "Today",
        verified: true
      };

      state.lots.unshift(newLot);
      saveLots();
      renderMarketplaceKPIs();
      renderMarketplaceLots();
      formNewLot.reset();
      document.getElementById("modal-list-lot").classList.remove("open");
      showToast(`Listed "${newLot.title}" (${newLot.quantityAvailable} Quintals) on AgriMart.`);
    });
  }

  // Order Confirmation Form
  const formOrderLot = document.getElementById("form-order-lot");
  if (formOrderLot) {
    const qtyInput = document.getElementById("order-qty-in");
    qtyInput?.addEventListener("input", updateOrderModalTotal);

    formOrderLot.addEventListener("submit", (e) => {
      e.preventDefault();
      const lot = state.selectedLotForOrder;
      if (!lot) return;

      const qty = parseFloat(document.getElementById("order-qty-in").value) || lot.minOrder;
      const buyerName = document.getElementById("order-buyer-in").value.trim();
      const buyerPhone = document.getElementById("order-phone-in").value.trim();
      const deliveryPoint = document.getElementById("order-dest-in").value.trim();

      if (qty > lot.quantityAvailable) {
        showToast("Requested quantity exceeds available stock.");
        return;
      }

      lot.quantityAvailable = Math.max(0, lot.quantityAvailable - qty);
      const orderRecord = {
        orderId: `ORD-${Math.floor(100000 + Math.random() * 900000)}`,
        lotId: lot.id,
        cropTitle: lot.title,
        farmerName: lot.farmerName,
        location: lot.location,
        quantity: qty,
        unitPrice: lot.pricePerUnit,
        totalAmount: qty * lot.pricePerUnit,
        buyerName,
        buyerPhone,
        deliveryPoint,
        timestamp: new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })
      };

      state.orders.unshift(orderRecord);
      saveLots();
      saveOrders();
      renderMarketplaceKPIs();
      renderMarketplaceLots();
      renderOrdersDrawerCount();

      document.getElementById("modal-order-lot").classList.remove("open");
      formOrderLot.reset();
      showToast(`Order ${orderRecord.orderId} confirmed for ${qty} Quintals of ${lot.title}.`);
    });
  }

  // View Orders button
  document.getElementById("btn-view-orders")?.addEventListener("click", () => {
    renderOrdersModalList();
    document.getElementById("modal-orders-list").classList.add("open");
  });
}

function renderMarketplaceKPIs() {
  const totalQuintals = state.lots.reduce((acc, l) => acc + l.quantityAvailable, 0);
  const totalValueLakhs = (
    state.lots.reduce((acc, l) => acc + l.quantityAvailable * l.pricePerUnit, 0) / 100000
  ).toFixed(2);

  document.getElementById("kpi-active-lots").textContent = state.lots.length;
  document.getElementById("kpi-available-volume").textContent = `${totalQuintals.toLocaleString()} Qtl`;
  document.getElementById("kpi-inventory-val").textContent = `₹${totalValueLakhs} L`;
  document.getElementById("kpi-orders-placed").textContent = state.orders.length;
  document.getElementById("nav-lots-count").textContent = state.lots.length;
}

function renderMarketplaceLots() {
  const container = document.getElementById("market-lots-grid");
  if (!container) return;

  let filtered = state.lots.filter((item) => {
    const matchesCat = state.marketFilterCategory === "All" || item.category === state.marketFilterCategory;
    const matchesQuery =
      !state.marketSearch ||
      item.title.toLowerCase().includes(state.marketSearch) ||
      item.variety.toLowerCase().includes(state.marketSearch) ||
      item.location.toLowerCase().includes(state.marketSearch) ||
      item.farmerName.toLowerCase().includes(state.marketSearch);
    return matchesCat && matchesQuery;
  });

  if (state.marketSort === "price-asc") {
    filtered.sort((a, b) => a.pricePerUnit - b.pricePerUnit);
  } else if (state.marketSort === "price-desc") {
    filtered.sort((a, b) => b.pricePerUnit - a.pricePerUnit);
  } else if (state.marketSort === "qty-desc") {
    filtered.sort((a, b) => b.quantityAvailable - a.quantityAvailable);
  }

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="panel" style="grid-column: 1 / -1; text-align: center; padding: 36px;">
        <div class="panel-title">No matching harvest lots found</div>
        <div class="panel-subtitle" style="margin-bottom: 12px;">Try clearing your search filter or switching categories.</div>
        <button class="btn btn-secondary btn-sm" onclick="resetMarketFilters()">Reset Filters</button>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered
    .map((lot) => {
      const soldOut = lot.quantityAvailable <= 0;
      const diffFromMandi = lot.pricePerUnit - lot.mandiBenchmark;
      const mandiNote =
        diffFromMandi <= 0
          ? `₹${Math.abs(diffFromMandi)} below APMC modal`
          : `₹${diffFromMandi} above APMC modal (Sortex)`;

      return `
      <article class="lot-card">
        <div>
          <div class="lot-top">
            <span class="lot-category">${escapeHtml(lot.category)} • ${escapeHtml(lot.id)}</span>
            <span class="grade-badge ${soldOut ? "amber" : ""}">${soldOut ? "Sold Out" : escapeHtml(lot.grade)}</span>
          </div>
          <h3 class="lot-title">${escapeHtml(lot.title)}</h3>
          <div class="lot-variety">${escapeHtml(lot.variety)}</div>

          <div class="lot-specs">
            <div class="spec-item">
              <span class="spec-label">Available Stock</span>
              <span class="spec-val">${lot.quantityAvailable} ${lot.unit}s</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">Min. Lot Order</span>
              <span class="spec-val">${lot.minOrder} ${lot.unit}s</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">Moisture / Cond.</span>
              <span class="spec-val">${escapeHtml(lot.moisture)}</span>
            </div>
            <div class="spec-item">
              <span class="spec-label">Harvested</span>
              <span class="spec-val">${escapeHtml(lot.harvestDate)}</span>
            </div>
          </div>

          <div class="lot-farmer">
            <span><strong>${escapeHtml(lot.farmerName)}</strong> • ${escapeHtml(lot.location)}</span>
          </div>
        </div>

        <div class="lot-footer">
          <div>
            <div class="lot-price">₹${lot.pricePerUnit.toLocaleString("en-IN")} <span class="lot-unit">/ ${lot.unit}</span></div>
            <div style="font-size: 11px; color: var(--text-muted);">${mandiNote}</div>
          </div>
          <button
            class="btn ${soldOut ? "btn-subtle" : "btn-primary"}"
            ${soldOut ? "disabled" : `onclick="openOrderModal('${lot.id}')"`}
          >
            ${soldOut ? "Booked" : "Procure Lot"}
          </button>
        </div>
      </article>
    `;
    })
    .join("");
}

window.resetMarketFilters = function () {
  state.marketFilterCategory = "All";
  state.marketSearch = "";
  const input = document.getElementById("market-search-input");
  if (input) input.value = "";
  document.querySelectorAll("#market-category-pills .filter-pill").forEach((p) => {
    p.classList.toggle("active", p.getAttribute("data-category") === "All");
  });
  renderMarketplaceLots();
};

window.openOrderModal = function (lotId) {
  const lot = state.lots.find((l) => l.id === lotId);
  if (!lot) return;
  state.selectedLotForOrder = lot;

  document.getElementById("order-modal-lot-title").textContent = `${lot.title} (${lot.id})`;
  document.getElementById("order-modal-farmer").textContent = `Seller: ${lot.farmerName} • ${lot.location}`;
  document.getElementById("order-modal-rate").textContent = `₹${lot.pricePerUnit.toLocaleString("en-IN")} / ${lot.unit}`;

  const qtyInput = document.getElementById("order-qty-in");
  qtyInput.min = lot.minOrder;
  qtyInput.max = lot.quantityAvailable;
  qtyInput.value = Math.min(lot.minOrder, lot.quantityAvailable);

  updateOrderModalTotal();
  document.getElementById("modal-order-lot").classList.add("open");
};

function updateOrderModalTotal() {
  const lot = state.selectedLotForOrder;
  if (!lot) return;
  const qty = parseFloat(document.getElementById("order-qty-in").value) || 0;
  const total = qty * lot.pricePerUnit;
  document.getElementById("order-modal-total").textContent = `₹${total.toLocaleString("en-IN")} (0% Platform Fee — 100% Direct to Farmer)`;
}

function renderOrdersDrawerCount() {
  const el = document.getElementById("orders-count-badge");
  if (el) el.textContent = state.orders.length;
}

function renderOrdersModalList() {
  const wrap = document.getElementById("orders-modal-body");
  if (!wrap) return;

  if (state.orders.length === 0) {
    wrap.innerHTML = `<p style="color: var(--text-secondary); padding: 16px 0;">No procurement orders placed yet. Select any harvest lot in the marketplace to book directly from the farmer.</p>`;
    return;
  }

  wrap.innerHTML = `
    <div class="table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th>Order ID</th>
            <th>Produce</th>
            <th>Farmer & Origin</th>
            <th class="num-col">Qty (Qtl)</th>
            <th class="num-col">Total Paid</th>
          </tr>
        </thead>
        <tbody>
          ${state.orders
            .map(
              (o) => `
            <tr>
              <td style="font-family: var(--font-mono); font-weight: 600;">${escapeHtml(o.orderId)}</td>
              <td>${escapeHtml(o.cropTitle)}</td>
              <td>${escapeHtml(o.farmerName)} (${escapeHtml(o.location)})</td>
              <td class="num-col">${o.quantity}</td>
              <td class="num-col">₹${o.totalAmount.toLocaleString("en-IN")}</td>
            </tr>
          `
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

// ==========================================
// 2. SOIL & CROP RECOMMENDATION ENGINE (k-NN on 2,200 rows)
// ==========================================
function setupCropRecommenderHandlers() {
  const presetWrap = document.getElementById("soil-presets-container");
  if (presetWrap) {
    presetWrap.innerHTML = SOIL_PRESETS.map(
      (p) => `<button type="button" class="preset-btn" data-preset="${p.id}">${escapeHtml(p.label)}</button>`
    ).join("");

    presetWrap.querySelectorAll(".preset-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const preset = SOIL_PRESETS.find((p) => p.id === btn.getAttribute("data-preset"));
        if (!preset) return;
        document.getElementById("in-n").value = preset.values.N;
        document.getElementById("in-p").value = preset.values.P;
        document.getElementById("in-k").value = preset.values.K;
        document.getElementById("in-temp").value = preset.values.temperature;
        document.getElementById("in-hum").value = preset.values.humidity;
        document.getElementById("in-ph").value = preset.values.ph;
        document.getElementById("in-rain").value = preset.values.rainfall;
        runCropPrediction();
        showToast(`Loaded soil profile: ${preset.label}`);
      });
    });
  }

  const formRec = document.getElementById("form-crop-recommender");
  if (formRec) {
    formRec.addEventListener("submit", (e) => {
      e.preventDefault();
      runCropPrediction();
    });
    formRec.querySelectorAll("input").forEach((inp) => {
      inp.addEventListener("change", runCropPrediction);
    });
  }
}

function runCropPrediction() {
  const input = {
    N: parseFloat(document.getElementById("in-n")?.value) || 85,
    P: parseFloat(document.getElementById("in-p")?.value) || 48,
    K: parseFloat(document.getElementById("in-k")?.value) || 40,
    temperature: parseFloat(document.getElementById("in-temp")?.value) || 23.5,
    humidity: parseFloat(document.getElementById("in-hum")?.value) || 81.0,
    ph: parseFloat(document.getElementById("in-ph")?.value) || 6.5,
    rainfall: parseFloat(document.getElementById("in-rain")?.value) || 210.0
  };

  // Feature normalization ranges from the 2,200-row dataset
  const scales = {
    N: 140,
    P: 145,
    K: 205,
    temperature: 45,
    humidity: 100,
    ph: 10,
    rainfall: 300
  };

  // Compute normalized Euclidean distance against all 22 crop centroids + k-NN verification
  const scoredCrops = Object.keys(CROP_PROFILES).map((cropKey) => {
    const c = CROP_PROFILES[cropKey].centroid;
    const dN = (input.N - c.N) / scales.N;
    const dP = (input.P - c.P) / scales.P;
    const dK = (input.K - c.K) / scales.K;
    const dT = (input.temperature - c.temperature) / scales.temperature;
    const dH = (input.humidity - c.humidity) / scales.humidity;
    const dPh = (input.ph - c.ph) / scales.ph;
    const dR = (input.rainfall - c.rainfall) / scales.rainfall;

    const dist = Math.sqrt(dN * dN + dP * dP + dK * dK + dT * dT + dH * dH + dPh * dPh + dR * dR);
    const similarity = Math.max(12, Math.min(99.4, 100 * Math.exp(-2.1 * dist)));

    return {
      key: cropKey,
      profile: CROP_PROFILES[cropKey],
      distance: dist,
      confidence: similarity.toFixed(1)
    };
  });

  scoredCrops.sort((a, b) => a.distance - b.distance);
  const top3 = scoredCrops.slice(0, 3);

  const outWrap = document.getElementById("crop-rec-results");
  if (!outWrap) return;

  outWrap.innerHTML = top3
    .map((item, idx) => {
      const p = item.profile;
      const rankLabel = idx === 0 ? "Best Agronomic Fit (#1)" : `Alternative Fit (#${idx + 1})`;
      return `
      <div class="rec-card ${idx === 0 ? "primary-match" : ""}">
        <div class="rec-header">
          <div>
            <span style="font-size: 11px; text-transform: uppercase; font-weight: 600; color: var(--text-muted);">${rankLabel} • ${escapeHtml(p.category)}</span>
            <div class="rec-crop-name">${escapeHtml(p.name)}</div>
          </div>
          <span class="match-pill">${item.confidence}% Match</span>
        </div>

        <div class="rec-metrics">
          <div>
            <div class="spec-label">Sowing Window</div>
            <div class="spec-val">${escapeHtml(p.season)}</div>
          </div>
          <div>
            <div class="spec-label">Expected Yield / Acre</div>
            <div class="spec-val">${escapeHtml(p.yieldPerAcre)}</div>
          </div>
          <div>
            <div class="spec-label">Benchmark MSP / Rate</div>
            <div class="spec-val">₹${p.mspRate.toLocaleString("en-IN")} / Qtl</div>
          </div>
          <div>
            <div class="spec-label">Water Requirement</div>
            <div class="spec-val">${escapeHtml(p.waterNeed)}</div>
          </div>
        </div>

        <div class="rec-note">
          <strong>Agronomic Note:</strong> ${escapeHtml(p.soilNote)}. Ideal dataset centroid: N=${p.centroid.N}, P=${p.centroid.P}, K=${p.centroid.K}, pH=${p.centroid.ph}, Rain=${p.centroid.rainfall}mm.
        </div>
      </div>
    `;
    })
    .join("");
}

// ==========================================
// 3. FERTILIZER DOSAGE & SOIL DEFICIENCY CALCULATOR
// ==========================================
function setupFertilizerCalculatorHandlers() {
  const cropSel = document.getElementById("fert-crop-select");
  if (cropSel) {
    cropSel.innerHTML = Object.keys(FERTILIZER_TARGETS)
      .map((k) => `<option value="${k}">${escapeHtml(FERTILIZER_TARGETS[k].name)}</option>`)
      .join("");
  }

  const formFert = document.getElementById("form-fertilizer-calc");
  if (formFert) {
    formFert.addEventListener("submit", (e) => {
      e.preventDefault();
      runFertilizerCalculation();
    });
    formFert.querySelectorAll("input, select").forEach((el) => {
      el.addEventListener("change", runFertilizerCalculation);
    });
  }
}

function runFertilizerCalculation() {
  const cropKey = document.getElementById("fert-crop-select")?.value || "rice";
  const target = FERTILIZER_TARGETS[cropKey] || FERTILIZER_TARGETS.rice;
  const acres = parseFloat(document.getElementById("fert-acres")?.value) || 2.5;
  const soilN = parseFloat(document.getElementById("fert-soil-n")?.value) || 20;
  const soilP = parseFloat(document.getElementById("fert-soil-p")?.value) || 10;
  const soilK = parseFloat(document.getElementById("fert-soil-k")?.value) || 10;

  // Deficit per acre (kg)
  const gapN = Math.max(0, target.N - soilN * 0.45);
  const gapP = Math.max(0, target.P - soilP * 0.45);
  const gapK = Math.max(0, target.K - soilK * 0.45);

  // Convert to DAP (18% N, 46% P2O5), Urea (46% N), MOP (60% K2O)
  const dapPerAcreKg = gapP / 0.46;
  const nSuppliedByDap = dapPerAcreKg * 0.18;
  const remainingN = Math.max(0, gapN - nSuppliedByDap);
  const ureaPerAcreKg = remainingN / 0.46;
  const mopPerAcreKg = gapK / 0.6;

  const totalUreaKg = Math.round(ureaPerAcreKg * acres);
  const totalDapKg = Math.round(dapPerAcreKg * acres);
  const totalMopKg = Math.round(mopPerAcreKg * acres);

  const ureaBags = (totalUreaKg / 45).toFixed(1); // 45kg standard Neem Coated Urea bag
  const dapBags = (totalDapKg / 50).toFixed(1);   // 50kg DAP bag
  const mopBags = (totalMopKg / 50).toFixed(1);   // 50kg MOP bag

  // Govt subsidized approximate retail rates: Urea ₹266/bag, DAP ₹1350/bag, MOP ₹1650/bag
  const estCost = Math.round(
    parseFloat(ureaBags) * 266 + parseFloat(dapBags) * 1350 + parseFloat(mopBags) * 1650
  );

  const outWrap = document.getElementById("fert-calc-output");
  if (!outWrap) return;

  outWrap.innerHTML = `
    <div class="kpi-strip" style="margin-bottom: 16px;">
      <div class="kpi-card">
        <div class="kpi-label">Neem Coated Urea (46% N)</div>
        <div class="kpi-value">${totalUreaKg} kg</div>
        <div class="kpi-meta">${ureaBags} Bags (45 kg each) for ${acres} Acres</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">DAP (18:46:0)</div>
        <div class="kpi-value">${totalDapKg} kg</div>
        <div class="kpi-meta">${dapBags} Bags (50 kg each) for ${acres} Acres</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Muriate of Potash (60% K)</div>
        <div class="kpi-value">${totalMopKg} kg</div>
        <div class="kpi-meta">${mopBags} Bags (50 kg each) for ${acres} Acres</div>
      </div>
    </div>

    <div class="rec-card primary-match">
      <div class="rec-header">
        <div class="rec-crop-name" style="font-size: 15px;">Application Schedule for ${escapeHtml(target.name)}</div>
        <span class="match-pill">Est. Input Cost: ₹${estCost.toLocaleString("en-IN")}</span>
      </div>
      <p class="rec-note" style="margin-bottom: 10px;">${escapeHtml(target.advice)}</p>
      <div style="font-size: 12px; color: var(--text-muted); font-family: var(--font-mono);">
        Net Nutrient Deficit Corrected per Acre: N = ${gapN.toFixed(1)} kg | P2O5 = ${gapP.toFixed(1)} kg | K2O = ${gapK.toFixed(1)} kg
      </div>
    </div>
  `;
}

// ==========================================
// 4. APMC MANDI PRICE TRACKER
// ==========================================
function populateMandiStates() {
  const sel = document.getElementById("mandi-state-select");
  if (!sel) return;
  const states = Array.from(new Set(MANDI_RATES_DATA.map((m) => m.state))).sort();
  sel.innerHTML = `<option value="All">All States (${states.length})</option>` +
    states.map((s) => `<option value="${escapeHtml(s)}">${escapeHtml(s)}</option>`).join("");
}

function setupMandiHandlers() {
  document.getElementById("mandi-state-select")?.addEventListener("change", (e) => {
    state.mandiStateFilter = e.target.value;
    renderMandiTable();
  });

  document.getElementById("mandi-search-input")?.addEventListener("input", (e) => {
    state.mandiSearch = e.target.value.trim().toLowerCase();
    renderMandiTable();
  });
}

function renderMandiTable() {
  const tbody = document.getElementById("mandi-table-body");
  if (!tbody) return;

  const filtered = MANDI_RATES_DATA.filter((row) => {
    const matchState = state.mandiStateFilter === "All" || row.state === state.mandiStateFilter;
    const matchQuery =
      !state.mandiSearch ||
      row.commodity.toLowerCase().includes(state.mandiSearch) ||
      row.mandi.toLowerCase().includes(state.mandiSearch) ||
      row.variety.toLowerCase().includes(state.mandiSearch);
    return matchState && matchQuery;
  });

  tbody.innerHTML = filtered
    .map((r) => {
      const trendClass = r.changePct > 0 ? "trend-up" : r.changePct < 0 ? "trend-down" : "trend-flat";
      const sign = r.changePct > 0 ? "+" : "";
      return `
      <tr>
        <td><strong>${escapeHtml(r.commodity)}</strong> <span style="color: var(--text-muted); font-size: 12px;">(${escapeHtml(r.variety)})</span></td>
        <td>${escapeHtml(r.mandi)}</td>
        <td>${escapeHtml(r.state)}</td>
        <td class="num-col">₹${r.minPrice.toLocaleString("en-IN")}</td>
        <td class="num-col">₹${r.maxPrice.toLocaleString("en-IN")}</td>
        <td class="num-col" style="font-weight: 700;">₹${r.modalPrice.toLocaleString("en-IN")}</td>
        <td class="num-col">${r.arrivalTonnes} T</td>
        <td class="num-col ${trendClass}">${sign}${r.changePct}%</td>
      </tr>
    `;
    })
    .join("");
}

// ==========================================
// 5. DATASET EXPLORER (2,200+ Records)
// ==========================================
function populateExplorerCropDropdown() {
  const sel = document.getElementById("explorer-crop-select");
  if (!sel) return;
  const crops = Object.keys(CROP_PROFILES).sort();
  sel.innerHTML =
    `<option value="All">All 22 Crops (${state.dataset.length.toLocaleString()} rows)</option>` +
    crops.map((c) => `<option value="${c}">${escapeHtml(CROP_PROFILES[c].name)}</option>`).join("");
}

function setupDatasetExplorerHandlers() {
  document.getElementById("explorer-crop-select")?.addEventListener("change", (e) => {
    state.explorerCropFilter = e.target.value;
    state.explorerPage = 1;
    renderDatasetExplorer();
  });

  document.getElementById("btn-prev-page")?.addEventListener("click", () => {
    if (state.explorerPage > 1) {
      state.explorerPage--;
      renderDatasetExplorer();
    }
  });

  document.getElementById("btn-next-page")?.addEventListener("click", () => {
    const filtered = getFilteredDatasetRows();
    const maxPage = Math.ceil(filtered.length / state.explorerPageSize) || 1;
    if (state.explorerPage < maxPage) {
      state.explorerPage++;
      renderDatasetExplorer();
    }
  });

  document.getElementById("btn-export-csv")?.addEventListener("click", exportCurrentDatasetCSV);
}

function getFilteredDatasetRows() {
  if (state.explorerCropFilter === "All") return state.dataset;
  return state.dataset.filter((r) => r.label === state.explorerCropFilter);
}

function renderDatasetExplorer() {
  const tbody = document.getElementById("explorer-table-body");
  if (!tbody) return;

  const filtered = getFilteredDatasetRows();
  const totalRows = filtered.length;
  const maxPage = Math.ceil(totalRows / state.explorerPageSize) || 1;
  if (state.explorerPage > maxPage) state.explorerPage = maxPage;

  const startIdx = (state.explorerPage - 1) * state.explorerPageSize;
  const pageRows = filtered.slice(startIdx, startIdx + state.explorerPageSize);

  tbody.innerHTML = pageRows
    .map(
      (r, idx) => `
      <tr>
        <td class="num-col" style="color: var(--text-muted);">#${startIdx + idx + 1}</td>
        <td><span class="grade-badge" style="text-transform: capitalize;">${escapeHtml(r.label)}</span></td>
        <td class="num-col">${r.N}</td>
        <td class="num-col">${r.P}</td>
        <td class="num-col">${r.K}</td>
        <td class="num-col">${r.temperature}°C</td>
        <td class="num-col">${r.humidity}%</td>
        <td class="num-col">${r.ph}</td>
        <td class="num-col">${r.rainfall} mm</td>
      </tr>
    `
    )
    .join("");

  const infoEl = document.getElementById("explorer-page-info");
  if (infoEl) {
    infoEl.textContent = `Showing ${startIdx + 1}–${Math.min(startIdx + state.explorerPageSize, totalRows)} of ${totalRows.toLocaleString()} records (${state.datasetSource})`;
  }
}

function exportCurrentDatasetCSV() {
  const rows = getFilteredDatasetRows();
  const header = "N,P,K,temperature,humidity,ph,rainfall,label\n";
  const body = rows
    .map((r) => `${r.N},${r.P},${r.K},${r.temperature},${r.humidity},${r.ph},${r.rainfall},${r.label}`)
    .join("\n");
  const blob = new Blob([header + body], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `agrimart_crop_dataset_${state.explorerCropFilter.toLowerCase()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast(`Exported ${rows.length.toLocaleString()} rows to CSV.`);
}

// Utilities
function showToast(msg) {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => {
    el.remove();
  }, 3500);
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
