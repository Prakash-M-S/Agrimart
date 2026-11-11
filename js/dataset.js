// AgriMart — Extensive Agricultural Datasets & Live Network Sync
// Sources:
// 1. ICAR / Kaggle Crop Recommendation Dataset (2,200 records across 22 crops)
//    Live URL: https://raw.githubusercontent.com/Gladiator07/Harvestify/master/Data-processed/crop_recommendation.csv
// 2. Soil & Fertilizer Advisory Dataset
//    Live URL: https://raw.githubusercontent.com/Gladiator07/Harvestify/master/Data-processed/fertilizer.csv
// 3. Agmarknet / APMC Mandi Benchmark Rates across Indian Agricultural Markets

const REMOTE_CROP_CSV_URL = "https://raw.githubusercontent.com/Gladiator07/Harvestify/master/Data-processed/crop_recommendation.csv";

// Agronomic profile and centroid parameters for all 22 standard crops in the dataset
const CROP_PROFILES = {
  rice: {
    name: "Rice (Paddy)",
    category: "Cereal",
    season: "Kharif (Jun – Nov)",
    yieldPerAcre: "22 – 28 Quintals",
    mspRate: 2300,
    waterNeed: "High (1200–1500 mm)",
    soilNote: "Clayey loam with good water retention",
    centroid: { N: 79.89, P: 47.58, K: 39.87, temperature: 23.69, humidity: 82.27, ph: 6.43, rainfall: 236.18 }
  },
  maize: {
    name: "Maize (Corn)",
    category: "Cereal",
    season: "Kharif / Rabi",
    yieldPerAcre: "18 – 24 Quintals",
    mspRate: 2225,
    waterNeed: "Moderate (500–800 mm)",
    soilNote: "Well-drained sandy loam to silty loam",
    centroid: { N: 77.76, P: 48.44, K: 19.79, temperature: 22.39, humidity: 65.09, ph: 6.25, rainfall: 84.77 }
  },
  chickpea: {
    name: "Chickpea (Chana)",
    category: "Pulse",
    season: "Rabi (Oct – Mar)",
    yieldPerAcre: "8 – 11 Quintals",
    mspRate: 5440,
    waterNeed: "Low (350–450 mm)",
    soilNote: "Sandy loam to black cotton soil, well-drained",
    centroid: { N: 40.09, P: 67.79, K: 79.92, temperature: 18.87, humidity: 16.86, ph: 7.34, rainfall: 80.06 }
  },
  kidneybeans: {
    name: "Kidney Beans (Rajma)",
    category: "Pulse",
    season: "Kharif / Rabi Hills",
    yieldPerAcre: "6 – 9 Quintals",
    mspRate: 6800,
    waterNeed: "Moderate (600–900 mm)",
    soilNote: "Slightly acidic to neutral loamy soil",
    centroid: { N: 20.75, P: 67.54, K: 20.05, temperature: 20.12, humidity: 21.61, ph: 5.75, rainfall: 105.92 }
  },
  pigeonpeas: {
    name: "Pigeon Peas (Tur / Arhar)",
    category: "Pulse",
    season: "Kharif (Jun – Dec)",
    yieldPerAcre: "7 – 10 Quintals",
    mspRate: 7550,
    waterNeed: "Low–Moderate (600–1000 mm)",
    soilNote: "Black cotton or loamy upland soil",
    centroid: { N: 20.73, P: 67.73, K: 20.29, temperature: 27.74, humidity: 48.06, ph: 5.79, rainfall: 149.46 }
  },
  mothbeans: {
    name: "Moth Beans (Matki)",
    category: "Pulse",
    season: "Kharif Arid",
    yieldPerAcre: "4 – 6 Quintals",
    mspRate: 6200,
    waterNeed: "Very Low (250–400 mm)",
    soilNote: "Dry sandy and arid soils",
    centroid: { N: 21.44, P: 48.01, K: 20.23, temperature: 28.19, humidity: 53.16, ph: 6.83, rainfall: 51.20 }
  },
  mungbean: {
    name: "Mung Bean (Moong)",
    category: "Pulse",
    season: "Kharif / Zaid",
    yieldPerAcre: "5 – 8 Quintals",
    mspRate: 8682,
    waterNeed: "Low (300–450 mm)",
    soilNote: "Deep well-drained loamy soil",
    centroid: { N: 20.99, P: 47.28, K: 19.88, temperature: 28.53, humidity: 85.50, ph: 6.72, rainfall: 48.40 }
  },
  blackgram: {
    name: "Black Gram (Urad)",
    category: "Pulse",
    season: "Kharif / Rabi South",
    yieldPerAcre: "6 – 8 Quintals",
    mspRate: 7400,
    waterNeed: "Moderate (500–700 mm)",
    soilNote: "Heavy clay loam to black soil",
    centroid: { N: 40.02, P: 67.47, K: 19.24, temperature: 29.97, humidity: 65.12, ph: 7.13, rainfall: 67.88 }
  },
  lentil: {
    name: "Lentil (Masoor)",
    category: "Pulse",
    season: "Rabi (Oct – Mar)",
    yieldPerAcre: "7 – 10 Quintals",
    mspRate: 6425,
    waterNeed: "Low (350–450 mm)",
    soilNote: "Alluvial and light loamy soil",
    centroid: { N: 18.77, P: 68.36, K: 19.41, temperature: 24.51, humidity: 64.80, ph: 6.93, rainfall: 45.68 }
  },
  pomegranate: {
    name: "Pomegranate (Bhagwa)",
    category: "Fruit",
    season: "Perennial (Ambe/Mrig Bahar)",
    yieldPerAcre: "55 – 70 Quintals",
    mspRate: 8500,
    waterNeed: "Drip Irrigation (500–700 mm)",
    soilNote: "Well-drained medium black to red calcareous soil",
    centroid: { N: 18.87, P: 18.75, K: 40.21, temperature: 21.84, humidity: 90.13, ph: 6.43, rainfall: 107.53 }
  },
  banana: {
    name: "Banana (Grand Naine)",
    category: "Fruit",
    season: "Year-round Plantation",
    yieldPerAcre: "180 – 240 Quintals",
    mspRate: 1850,
    waterNeed: "High (1200–1800 mm)",
    soilNote: "Rich, deep alluvial or volcanic loamy soil",
    centroid: { N: 100.23, P: 82.01, K: 50.05, temperature: 27.38, humidity: 80.36, ph: 5.98, rainfall: 104.63 }
  },
  mango: {
    name: "Mango (Alphonso / Dasheri)",
    category: "Fruit",
    season: "Perennial (Harvest Apr–Jul)",
    yieldPerAcre: "40 – 55 Quintals",
    mspRate: 6400,
    waterNeed: "Moderate (750–1250 mm)",
    soilNote: "Well-drained lateritic or alluvial loam",
    centroid: { N: 20.07, P: 27.18, K: 29.92, temperature: 31.21, humidity: 50.16, ph: 5.77, rainfall: 94.70 }
  },
  grapes: {
    name: "Grapes (Thompson Seedless)",
    category: "Fruit",
    season: "Perennial (Harvest Jan–Apr)",
    yieldPerAcre: "85 – 110 Quintals",
    mspRate: 5800,
    waterNeed: "Drip Managed (500–700 mm)",
    soilNote: "Well-drained gravelly loam, pH 6.0–7.0",
    centroid: { N: 23.18, P: 132.53, K: 200.11, temperature: 23.85, humidity: 81.88, ph: 6.03, rainfall: 69.61 }
  },
  watermelon: {
    name: "Watermelon (Sugar Baby)",
    category: "Fruit",
    season: "Zaid / Summer (Jan – May)",
    yieldPerAcre: "110 – 150 Quintals",
    mspRate: 1350,
    waterNeed: "Moderate (400–600 mm)",
    soilNote: "Sandy loam riverbed soils",
    centroid: { N: 99.42, P: 17.00, K: 50.22, temperature: 25.59, humidity: 85.16, ph: 6.50, rainfall: 50.79 }
  },
  muskmelon: {
    name: "Muskmelon (Kharbuja)",
    category: "Fruit",
    season: "Zaid / Summer (Feb – May)",
    yieldPerAcre: "65 – 85 Quintals",
    mspRate: 2400,
    waterNeed: "Low–Moderate (300–450 mm)",
    soilNote: "Warm, well-drained sandy loam",
    centroid: { N: 100.32, P: 17.72, K: 50.08, temperature: 28.66, humidity: 92.34, ph: 6.36, rainfall: 24.69 }
  },
  apple: {
    name: "Apple (Royal Delicious)",
    category: "Fruit",
    season: "Temperate (Harvest Aug–Oct)",
    yieldPerAcre: "60 – 85 Quintals",
    mspRate: 7800,
    waterNeed: "Moderate (1000–1250 mm)",
    soilNote: "Loamy hill soils rich in organic matter",
    centroid: { N: 20.80, P: 134.22, K: 199.89, temperature: 22.63, humidity: 92.33, ph: 5.93, rainfall: 112.65 }
  },
  orange: {
    name: "Orange (Nagpur Mandarin)",
    category: "Fruit",
    season: "Ambia / Mrig Bahar",
    yieldPerAcre: "55 – 75 Quintals",
    mspRate: 4200,
    waterNeed: "Moderate (900–1100 mm)",
    soilNote: "Medium black and well-drained loamy soil",
    centroid: { N: 19.58, P: 16.55, K: 10.01, temperature: 22.77, humidity: 92.17, ph: 7.02, rainfall: 110.47 }
  },
  papaya: {
    name: "Papaya (Red Lady 786)",
    category: "Fruit",
    season: "Year-round Tropical",
    yieldPerAcre: "160 – 210 Quintals",
    mspRate: 2100,
    waterNeed: "Moderate (1000–1400 mm)",
    soilNote: "Fertile, well-drained sandy loam (no waterlogging)",
    centroid: { N: 49.88, P: 59.05, K: 50.04, temperature: 33.72, humidity: 92.40, ph: 6.74, rainfall: 142.63 }
  },
  coconut: {
    name: "Coconut (West Coast Tall)",
    category: "Plantation",
    season: "Perennial Coastal",
    yieldPerAcre: "4500 – 6000 Nuts",
    mspRate: 3450,
    waterNeed: "High (1500–2200 mm)",
    soilNote: "Coastal sandy loam, laterite, and alluvial soils",
    centroid: { N: 21.98, P: 16.93, K: 30.59, temperature: 27.41, humidity: 94.84, ph: 5.98, rainfall: 175.69 }
  },
  cotton: {
    name: "Cotton (Long Staple Bt)",
    category: "Commercial",
    season: "Kharif (May – Nov)",
    yieldPerAcre: "10 – 15 Quintals",
    mspRate: 7521,
    waterNeed: "Moderate (600–900 mm)",
    soilNote: "Deep Black Regur / Cotton soil",
    centroid: { N: 117.77, P: 46.24, K: 19.56, temperature: 23.99, humidity: 79.84, ph: 6.91, rainfall: 80.40 }
  },
  jute: {
    name: "Jute (Golden Fibre TD-5)",
    category: "Commercial",
    season: "Kharif (Mar – Aug)",
    yieldPerAcre: "12 – 16 Quintals",
    mspRate: 5335,
    waterNeed: "High (1500–2000 mm)",
    soilNote: "New grey alluvial delta soil",
    centroid: { N: 78.40, P: 46.86, K: 39.99, temperature: 24.96, humidity: 79.64, ph: 6.73, rainfall: 174.79 }
  },
  coffee: {
    name: "Coffee (Arabica / Robusta)",
    category: "Plantation",
    season: "Perennial Shade Grown",
    yieldPerAcre: "6 – 9 Quintals (Clean)",
    mspRate: 16500,
    waterNeed: "High (1500–2200 mm)",
    soilNote: "Humus-rich well-drained hill forest loam",
    centroid: { N: 101.20, P: 28.74, K: 29.94, temperature: 25.54, humidity: 58.87, ph: 6.79, rainfall: 158.07 }
  }
};

// Soil Presets for Indian Agro-Climatic Zones
const SOIL_PRESETS = [
  {
    id: "punjab_alluvial",
    label: "Punjab Indo-Gangetic Alluvial",
    values: { N: 90, P: 46, K: 42, temperature: 22.8, humidity: 81.5, ph: 6.6, rainfall: 215 }
  },
  {
    id: "vidarbha_black",
    label: "Vidarbha Deep Black Cotton Soil",
    values: { N: 116, P: 45, K: 20, temperature: 24.5, humidity: 78.5, ph: 6.9, rainfall: 82 }
  },
  {
    id: "mp_malwa_rabi",
    label: "MP Malwa Plateau (Dry Rabi)",
    values: { N: 38, P: 68, K: 79, temperature: 18.5, humidity: 17.5, ph: 7.2, rainfall: 78 }
  },
  {
    id: "nashik_horticulture",
    label: "Nashik Gravelly Loam (Vineyard)",
    values: { N: 24, P: 132, K: 198, temperature: 24.2, humidity: 81.0, ph: 6.1, rainfall: 70 }
  },
  {
    id: "coorg_hill_loam",
    label: "Chikkamagaluru / Coorg Shade Loam",
    values: { N: 102, P: 29, K: 30, temperature: 25.2, humidity: 59.0, ph: 6.7, rainfall: 160 }
  },
  {
    id: "konkan_laterite",
    label: "Konkan / Malabar Coastal Laterite",
    values: { N: 22, P: 18, K: 31, temperature: 27.5, humidity: 94.0, ph: 6.0, rainfall: 185 }
  }
];

// Deterministic local generator for 2,200 rows matching exact Kaggle class distributions
// Used immediately on startup and seamlessly replaced/verified when remote GitHub CSV fetch finishes
function generateLocalDataset2200() {
  const rows = [];
  const keys = Object.keys(CROP_PROFILES);
  let seed = 4219;
  function pseudoRand() {
    seed = (seed * 16807) % 2147483647;
    return (seed - 1) / 2147483646;
  }
  function jitter(base, spread, decimals = 2) {
    const val = base + (pseudoRand() - 0.5) * 2 * spread;
    return Number(Math.max(0, val).toFixed(decimals));
  }

  keys.forEach((cropKey) => {
    const c = CROP_PROFILES[cropKey].centroid;
    for (let i = 0; i < 100; i++) {
      rows.push({
        N: jitter(c.N, 14, 0),
        P: jitter(c.P, 9, 0),
        K: jitter(c.K, 6, 0),
        temperature: jitter(c.temperature, 2.8, 2),
        humidity: jitter(c.humidity, 4.2, 2),
        ph: jitter(c.ph, 0.45, 2),
        rainfall: jitter(c.rainfall, 22.0, 2),
        label: cropKey
      });
    }
  });
  return rows;
}

// Initial Farmer Marketplace Listings
const INITIAL_MARKETPLACE_LOTS = [
  {
    id: "LOT-1041",
    title: "Sharbati Golden Wheat",
    variety: "HI-1544 Certified Seed Harvest",
    category: "Grains & Cereals",
    grade: "Grade A (Sortex)",
    moisture: "10.8%",
    quantityAvailable: 85,
    unit: "Quintal",
    minOrder: 5,
    pricePerUnit: 2780,
    mandiBenchmark: 2690,
    farmerName: "Rameshwar Patidar",
    location: "Sehore, Madhya Pradesh",
    harvestDate: "18 Oct 2026",
    verified: true
  },
  {
    id: "LOT-1042",
    title: "Pusa 1121 Basmati Paddy",
    variety: "Extra Long Slender Aromatic",
    category: "Grains & Cereals",
    grade: "Export Grade A",
    moisture: "12.2%",
    quantityAvailable: 140,
    unit: "Quintal",
    minOrder: 10,
    pricePerUnit: 4150,
    mandiBenchmark: 4220,
    farmerName: "Gurpreet Singh Gill",
    location: "Karnal, Haryana",
    harvestDate: "02 Nov 2026",
    verified: true
  },
  {
    id: "LOT-1043",
    title: "Desi Chickpea (Chana)",
    variety: "JG-11 Bold Unpolished",
    category: "Pulses & Legumes",
    grade: "FAQ Grade A",
    moisture: "9.5%",
    quantityAvailable: 48,
    unit: "Quintal",
    minOrder: 3,
    pricePerUnit: 5620,
    mandiBenchmark: 5540,
    farmerName: "Kailashoudhary",
    location: "Latur, Maharashtra",
    harvestDate: "24 Oct 2026",
    verified: true
  },
  {
    id: "LOT-1044",
    title: "Bhagwa Pomegranate",
    variety: "Deep Ruby Aril (250g+ Fruit Size)",
    category: "Fruits & Orchard",
    grade: "Grade A+ Crate",
    moisture: "Fresh",
    quantityAvailable: 32,
    unit: "Quintal",
    minOrder: 2,
    pricePerUnit: 8900,
    mandiBenchmark: 9200,
    farmerName: "Dattatray Deshmukh",
    location: "Solapur, Maharashtra",
    harvestDate: "07 Nov 2026",
    verified: true
  },
  {
    id: "LOT-1045",
    title: "Yellow Maize (Dry Shelled)",
    variety: "Poultry & Starch Mill Grade",
    category: "Grains & Cereals",
    grade: "Grade A",
    moisture: "11.4%",
    quantityAvailable: 210,
    unit: "Quintal",
    minOrder: 15,
    pricePerUnit: 2260,
    mandiBenchmark: 2240,
    farmerName: "Basavaraj Patil",
    location: "Haveri, Karnataka",
    harvestDate: "30 Oct 2026",
    verified: true
  },
  {
    id: "LOT-1046",
    title: "Shankar-6 Raw Cotton (Kapas)",
    variety: "29mm Staple Length, Low Trash",
    category: "Commercial Crops",
    grade: "FAQ Superior",
    moisture: "8.2%",
    quantityAvailable: 65,
    unit: "Quintal",
    minOrder: 5,
    pricePerUnit: 7450,
    mandiBenchmark: 7520,
    farmerName: "Hareshbhai Patel",
    location: "Rajkot, Gujarat",
    harvestDate: "04 Nov 2026",
    verified: true
  },
  {
    id: "LOT-1047",
    title: "Organic Tur / Arhar Whole",
    variety: "BSMR-736 Red Gram",
    category: "Pulses & Legumes",
    grade: "NPOP Organic",
    moisture: "9.9%",
    quantityAvailable: 36,
    unit: "Quintal",
    minOrder: 2,
    pricePerUnit: 7850,
    mandiBenchmark: 7700,
    farmerName: "Sukhdev Jadhav",
    location: "Akola, Maharashtra",
    harvestDate: "28 Oct 2026",
    verified: true
  },
  {
    id: "LOT-1048",
    title: "Coorg Arabica Parchment Coffee",
    variety: "Selection-795 Shade Grown",
    category: "Commercial Crops",
    grade: "Plantation A",
    moisture: "10.0%",
    quantityAvailable: 18,
    unit: "Quintal",
    minOrder: 1,
    pricePerUnit: 17200,
    mandiBenchmark: 17600,
    farmerName: "Bopanna K.M.",
    location: "Kodagu, Karnataka",
    harvestDate: "01 Nov 2026",
    verified: true
  },
  {
    id: "LOT-1049",
    title: "Lasalgaon Red Onion (Gavran)",
    variety: "Medium-Large 45–60mm Dry Skin",
    category: "Vegetables & Tubers",
    grade: "Grade A Storage",
    moisture: "Cured",
    quantityAvailable: 95,
    unit: "Quintal",
    minOrder: 5,
    pricePerUnit: 2940,
    mandiBenchmark: 3050,
    farmerName: "Nitin Pawar",
    location: "Nashik, Maharashtra",
    harvestDate: "06 Nov 2026",
    verified: true
  }
];

// Extensive APMC Mandi Benchmark Data (Agmarknet Format)
const MANDI_RATES_DATA = [
  { state: "Madhya Pradesh", mandi: "Sehore APMC", commodity: "Wheat", variety: "Sharbati", minPrice: 2580, maxPrice: 2940, modalPrice: 2760, arrivalTonnes: 412, changePct: +1.8 },
  { state: "Punjab", mandi: "Khanna Mandi", commodity: "Paddy (Dhan)", variety: "PR-126 Common", minPrice: 2280, maxPrice: 2345, modalPrice: 2320, arrivalTonnes: 1480, changePct: +0.6 },
  { state: "Haryana", mandi: "Karnal APMC", commodity: "Rice (Basmati)", variety: "Pusa 1121", minPrice: 3950, maxPrice: 4380, modalPrice: 4210, arrivalTonnes: 640, changePct: +2.4 },
  { state: "Maharashtra", mandi: "Lasalgaon APMC", commodity: "Onion", variety: "Red Gavran", minPrice: 2400, maxPrice: 3320, modalPrice: 2980, arrivalTonnes: 890, changePct: +4.1 },
  { state: "Maharashtra", mandi: "Latur APMC", commodity: "Pigeon Pea (Tur)", variety: "Red Whole", minPrice: 7250, maxPrice: 7920, modalPrice: 7680, arrivalTonnes: 275, changePct: -0.8 },
  { state: "Maharashtra", mandi: "Solapur APMC", commodity: "Pomegranate", variety: "Bhagwa Export", minPrice: 7400, maxPrice: 10200, modalPrice: 8950, arrivalTonnes: 145, changePct: +1.5 },
  { state: "Maharashtra", mandi: "Nashik APMC", commodity: "Grapes", variety: "Thompson Seedless", minPrice: 5100, maxPrice: 6400, modalPrice: 5750, arrivalTonnes: 190, changePct: +0.9 },
  { state: "Gujarat", mandi: "Rajkot Marketing Yard", commodity: "Cotton (Kapas)", variety: "Shankar-6 Long", minPrice: 7180, maxPrice: 7690, modalPrice: 7480, arrivalTonnes: 530, changePct: +1.2 },
  { state: "Gujarat", mandi: "Unjha APMC", commodity: "Cumin (Jeera)", variety: "Bold Machine Clean", minPrice: 23400, maxPrice: 26800, modalPrice: 25100, arrivalTonnes: 118, changePct: -1.4 },
  { state: "Karnataka", mandi: "Haveri APMC", commodity: "Maize", variety: "Yellow Hybrid", minPrice: 2110, maxPrice: 2340, modalPrice: 2245, arrivalTonnes: 610, changePct: +0.4 },
  { state: "Karnataka", mandi: "Madikeri (Kodagu)", commodity: "Coffee", variety: "Arabica Parchment", minPrice: 16800, maxPrice: 18100, modalPrice: 17450, arrivalTonnes: 68, changePct: +3.2 },
  { state: "Uttar Pradesh", mandi: "Agra Mandi", commodity: "Potato", variety: "Kufri Jyoti", minPrice: 1620, maxPrice: 1980, modalPrice: 1810, arrivalTonnes: 1120, changePct: -2.1 },
  { state: "Uttar Pradesh", mandi: "Hapur APMC", commodity: "Lentil (Masoor)", variety: "Small Bold", minPrice: 6180, maxPrice: 6590, modalPrice: 6410, arrivalTonnes: 195, changePct: +0.7 },
  { state: "Rajasthan", mandi: "Kota APMC", commodity: "Chickpea (Chana)", variety: "Desi Mill Grade", minPrice: 5290, maxPrice: 5680, modalPrice: 5510, arrivalTonnes: 490, changePct: +1.9 },
  { state: "Rajasthan", mandi: "Bikaner Mandi", commodity: "Mung Bean (Moong)", variety: "Green Shiny", minPrice: 8150, maxPrice: 8790, modalPrice: 8480, arrivalTonnes: 220, changePct: +1.1 },
  { state: "Rajasthan", mandi: "Alwar APMC", commodity: "Mustard Seed", variety: "Black 42% Oil", minPrice: 5450, maxPrice: 5890, modalPrice: 5690, arrivalTonnes: 540, changePct: +2.0 },
  { state: "Tamil Nadu", mandi: "Pollachi Market", commodity: "Coconut", variety: "Matured Dehusked", minPrice: 3150, maxPrice: 3680, modalPrice: 3420, arrivalTonnes: 310, changePct: +0.5 },
  { state: "Tamil Nadu", mandi: "Erode Regulated Market", commodity: "Banana", variety: "Grand Naine", minPrice: 1650, maxPrice: 2100, modalPrice: 1880, arrivalTonnes: 245, changePct: -0.4 },
  { state: "West Bengal", mandi: "Cooch Behar APMC", commodity: "Jute", variety: "TD-5 Raw Fibre", minPrice: 5120, maxPrice: 5490, modalPrice: 5330, arrivalTonnes: 390, changePct: +1.3 },
  { state: "Himachal Pradesh", mandi: "Shimla (Dhalli)", commodity: "Apple", variety: "Royal Delicious", minPrice: 6900, maxPrice: 8800, modalPrice: 7850, arrivalTonnes: 340, changePct: +2.6 }
];

// Fertilizer Nutrient Requirements per Crop (kg/acre standard target for N, P, K)
const FERTILIZER_TARGETS = {
  rice: { name: "Rice (Paddy)", N: 55, P: 25, K: 25, advice: "Apply 50% N and 100% P & K as basal dose before transplanting; split remaining N at active tillering and panicle initiation." },
  wheat: { name: "Wheat", N: 50, P: 25, K: 16, advice: "Drill full P and K + half N at sowing; broadcast remaining N at first crown root irrigation (21 DAS)." },
  maize: { name: "Maize (Corn)", N: 60, P: 30, K: 20, advice: "Band-place P and K at sowing; side-dress N in two splits at knee-high and tasseling stages." },
  cotton: { name: "Cotton (Bt)", N: 65, P: 32, K: 32, advice: "Black soils require foliar KNO3 spray during boll development to prevent reddening of leaves." },
  chickpea: { name: "Chickpea (Chana)", N: 12, P: 25, K: 12, advice: "Legume crop fixes atmospheric nitrogen; requires starter N dose and higher phosphorus (DAP/SSP) for root nodulation." },
  sugarcane: { name: "Sugarcane", N: 110, P: 45, K: 50, advice: "Heavy feeder; apply N in 3 equal splits at 45, 90, and 120 days after planting along with earthing-up." },
  potato: { name: "Potato", N: 65, P: 40, K: 50, advice: "Prefer Sulphate of Potash (SOP) or MOP at ridge formation for better tuber starch accumulation." },
  banana: { name: "Banana", N: 90, P: 35, K: 110, advice: "High potassium consumer; apply MOP in 4 split doses or via fertigation up to bunch emergence." },
  pomegranate: { name: "Pomegranate", N: 45, P: 30, K: 45, advice: "Combine FYM (15 kg/plant) with balanced NPK immediately after Bahar pruning." },
  coffee: { name: "Coffee", N: 50, P: 35, K: 50, advice: "Apply in pre-blossom (March) and post-monsoon (September) splits under shade canopy." }
};
