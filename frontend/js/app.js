// ======================================================
// AI Powered Vehicle Valuation
// ======================================================

const API_URL = (() => {
    const origin = window.location.origin;
    if (origin.includes(':5500')) {
        return origin.replace(/:5500$/, ':8000');
    }
    if (origin.includes('-5500.app.github.dev')) {
        return origin.replace('-5500.app.github.dev', '-8000.app.github.dev');
    }
    return origin;
})();

const brandSelect = document.getElementById('oem');
const modelSelect = document.getElementById('model');
const variantSelect = document.getElementById('variant');
const fuelSelect = document.getElementById('fuel');
const transmissionSelect = document.getElementById('transmission');
const bodyInput = document.getElementById('body');
const priceOutput = document.getElementById('price');
const statusOutput = document.getElementById('status');
const historyList = document.getElementById('historyList');
const historyCount = document.getElementById('historyCount');
const clearHistoryBtn = document.getElementById('clearHistoryBtn');
const exportHistoryBtn = document.getElementById('exportHistoryBtn');
const printReportBtn = document.getElementById('printReportBtn');
const brandSearchInput = document.getElementById('brandSearch');
const historySearchInput = document.getElementById('historySearch');
const submitBtn = document.getElementById('submitBtn');
const analyzeImagesBtn = document.getElementById('analyzeImagesBtn');
const visionResultContainer = document.getElementById('visionResult');

const imageInputs = {
    main: document.getElementById('mainImage'),
};

let historyCache = [];
let brandOptions = [];
let modelOptions = [];
let lastPredictionPayload = null;
let lastPredictedPrice = null;

const ownerTypeSelect = document.getElementById('owner_type');
const cityInput = document.getElementById('City');
const stateInput = document.getElementById('state');
const premiumBrandInput = document.getElementById('premium_brand');
const kmInput = document.getElementById('km');
const carAgeInput = document.getElementById('car_age');
const damageDescriptionInput = document.getElementById('damage_description');
const damageCostOutput = document.getElementById('damageCost');
const confidenceOutput = document.getElementById('confidenceScore');
const suggestedPriceOutput = document.getElementById('suggestedPrice');

const setSelectOptions = (selectElement, options, placeholder) => {
    selectElement.innerHTML = `<option value="">${placeholder}</option>`;
    options.forEach((option) => {
        selectElement.innerHTML += `<option value="${option}">${option}</option>`;
    });
};

// Create a datalist for the brand search input to provide native autocomplete
const brandDatalist = document.createElement('datalist');
brandDatalist.id = 'brand-datalist';
document.body.appendChild(brandDatalist);
brandSearchInput.setAttribute('list', 'brand-datalist');

const updateBrandDatalist = (options) => {
    brandDatalist.innerHTML = '';
    options.forEach((opt) => {
        const el = document.createElement('option');
        el.value = opt;
        brandDatalist.appendChild(el);
    });
};

// Simple debounce helper
const debounce = (fn, wait = 250) => {
    let t = null;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), wait);
    };
};

const fetchBrandSuggestions = async (query) => {
    try {
        const url = `${API_URL}/brands${query ? `?search=${encodeURIComponent(query)}` : ''}`;
        const res = await fetch(url);
        if (!res.ok) return [];
        const data = await res.json();
        return Array.isArray(data) ? data : [];
    } catch (err) {
        console.warn('Brand suggestion fetch failed', err);
        return [];
    }
};

// --- Custom suggestion dropdown (prefix-based) ---
const suggestionBox = document.createElement('div');
suggestionBox.className = 'autocomplete-list hidden';
// insert after the brandSearch input's parent form-group
const brandWrapper = brandSearchInput.closest('.form-group') || brandSearchInput.parentElement;
brandWrapper.style.position = 'relative';
brandWrapper.appendChild(suggestionBox);

const clearSuggestions = () => {
    suggestionBox.innerHTML = '';
    suggestionBox.classList.add('hidden');
};

const renderSuggestions = (items, query) => {
    suggestionBox.innerHTML = '';
    if (!items || items.length === 0) {
        clearSuggestions();
        return;
    }

    const q = (query || '').toLowerCase();
    const filtered = items.filter((b) => b.toLowerCase().startsWith(q));
    if (filtered.length === 0) {
        clearSuggestions();
        return;
    }

    filtered.slice(0, 8).forEach((brand) => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        // highlight matched prefix
        const idx = brand.toLowerCase().indexOf(q);
        if (idx === 0 && q.length > 0) {
            const strong = `<strong>${brand.slice(0, q.length)}</strong>${brand.slice(q.length)}`;
            item.innerHTML = strong;
        } else {
            item.textContent = brand;
        }
        item.addEventListener('mousedown', async (ev) => {
            ev.preventDefault();
            brandSearchInput.value = brand;
            brandSelect.value = brand;
            clearSuggestions();
            await loadModels(brand);
        });
        suggestionBox.appendChild(item);
    });
    suggestionBox.classList.remove('hidden');
};

const clearVehicleFields = () => {
    setSelectOptions(modelSelect, [], 'Select Brand First');
    setSelectOptions(variantSelect, [], 'Select Model First');
    setSelectOptions(fuelSelect, [], 'Select Model First');
    setSelectOptions(transmissionSelect, [], 'Select Model First');
    fuelSelect.disabled = true;
    transmissionSelect.disabled = true;
    bodyInput.value = '';
    premiumBrandInput.value = '0';
};

const filterBrands = () => {
    const query = brandSearchInput.value.trim().toLowerCase();
    if (!query) {
        return brandOptions;
    }

    return brandOptions.filter((brand) => brand.toLowerCase().includes(query));
};

const filterModels = () => {
    const query = modelSearchInput.value.trim().toLowerCase();
    if (!query) {
        return modelOptions;
    }

    return modelOptions.filter((model) => model.toLowerCase().includes(query));
};

const buildUrl = (path, ...segments) => {
    return `${API_URL}${path}${segments.map(segment => `/${encodeURIComponent(segment)}`).join('')}`;
};

const loadBrands = async () => {
    brandSelect.innerHTML = `<option value="">Loading...</option>`;

    try {
        const response = await fetch(buildUrl('/brands'));
        if (!response.ok) {
            throw new Error(`API responded with status ${response.status}`);
        }

        brandOptions = await response.json();
        setSelectOptions(brandSelect, filterBrands(), 'Select Brand');
        updateBrandDatalist(brandOptions);
    } catch (error) {
        console.error(error);
        brandSelect.innerHTML = `<option value="">Unable to load brands</option>`;
        clearVehicleFields();
        alert('Unable to load brands. Please ensure the backend is running and the API URL is correct.');
    }
};

const loadModels = async (brand) => {
    if (!brand) {
        clearVehicleFields();
        return;
    }

    try {
        const response = await fetch(buildUrl('/models', brand));
        if (!response.ok) {
            throw new Error(`API responded with status ${response.status}`);
        }

        modelOptions = await response.json();
        setSelectOptions(modelSelect, filterModels(), 'Select Model');

        if (modelOptions.length > 0) {
            modelSelect.value = modelOptions[0];
            await loadVehicleDetails(brand, modelOptions[0]);
        }
    } catch (error) {
        console.error(error);
        clearVehicleFields();
        // Silently fail - user can retry
    }
};

const loadVehicleDetails = async (brand, model) => {
    if (!brand || !model) {
        setSelectOptions(variantSelect, [], 'Select Model First');
        setSelectOptions(fuelSelect, [], 'Select Model First');
        setSelectOptions(transmissionSelect, [], 'Select Model First');
        fuelSelect.disabled = true;
        transmissionSelect.disabled = true;
        bodyInput.value = '';
        premiumBrandInput.value = '0';
        return;
    }

    try {
        const response = await fetch(buildUrl('/vehicle', brand, model));
        if (!response.ok) {
            throw new Error(`API responded with status ${response.status}`);
        }

        const vehicle = await response.json();
        const variants = Array.isArray(vehicle.variants) ? vehicle.variants : [];
        const fuels = Array.isArray(vehicle.fuel) ? vehicle.fuel : [];
        const transmissions = Array.isArray(vehicle.transmission) ? vehicle.transmission : [];

        setSelectOptions(variantSelect, variants, 'Select Variant');
        setSelectOptions(fuelSelect, fuels, 'Select Fuel');
        setSelectOptions(transmissionSelect, transmissions, 'Select Transmission');
        fuelSelect.disabled = false;
        transmissionSelect.disabled = false;
        bodyInput.value = vehicle.body || '';
console.log("Premium Brand:", vehicle.premium_brand);

premiumBrandInput.value = vehicle.premium_brand || "No";
        if (variants.length > 0) {
            variantSelect.value = variants[0];
        }
        if (fuels.length > 0) {
            fuelSelect.value = fuels[0];
        }
        if (transmissions.length > 0) {
            transmissionSelect.value = transmissions[0];
        }
    } catch (error) {
        console.error(error);
        setSelectOptions(variantSelect, [], 'Select Model First');
        setSelectOptions(fuelSelect, [], 'Select Model First');
        setSelectOptions(transmissionSelect, [], 'Select Model First');
        fuelSelect.disabled = true;
        transmissionSelect.disabled = true;
        bodyInput.value = '';
        premiumBrandInput.value = '0';
        alert('Unable to load vehicle details for the selected model.');
    }
};

const formatDateTime = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    });
};

const loadHistory = async () => {
    try {
        const response = await fetch(buildUrl('/history'));
        if (!response.ok) {
            throw new Error(`History API responded with status ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.warn('Failed to load history', error);
        return [];
    }
};

const renderBrandChoices = () => {
    const filtered = filterBrands();
    setSelectOptions(brandSelect, filtered, 'Select Brand');
    if (!filtered.includes(brandSelect.value)) {
        brandSelect.value = '';
        clearVehicleFields();
    }
};

const renderModelChoices = () => {
    const filtered = filterModels();
    setSelectOptions(modelSelect, filtered, 'Select Model');
    if (!filtered.includes(modelSelect.value)) {
        modelSelect.value = '';
        setSelectOptions(variantSelect, [], 'Select Model First');
        setSelectOptions(fuelSelect, [], 'Select Model First');
        setSelectOptions(transmissionSelect, [], 'Select Model First');
        bodyInput.value = '';
        premiumBrandInput.value = '0';
    }
};

const buildVisionFormData = () => {
    const formData = new FormData();
    const mainInput = imageInputs.main;
    if (mainInput && mainInput.files && mainInput.files[0]) {
        formData.append('main', mainInput.files[0]);
    }
    return formData;
};

const renderVisionResult = (analysis) => {
    if (!visionResultContainer) return;
    const lines = [];
    if (analysis.detected_brand) lines.push(`<strong>Brand:</strong> ${analysis.detected_brand}`);
    if (analysis.detected_model) lines.push(`<strong>Model:</strong> ${analysis.detected_model}`);
    if (analysis.detected_body_type) lines.push(`<strong>Body Type:</strong> ${analysis.detected_body_type}`);
    if (analysis.detected_color) lines.push(`<strong>Color:</strong> ${analysis.detected_color}`);
    if (analysis.estimated_year) lines.push(`<strong>Estimated Year:</strong> ${analysis.estimated_year}`);
    if (analysis.vehicle_category) lines.push(`<strong>Category:</strong> ${analysis.vehicle_category}`);
    // REMOVED: Images processed line that was confusing
    // if (analysis.images && analysis.images.length) {
    //     lines.push(`<strong>Images processed:</strong> ${analysis.images.map((item) => item.slot).join(', ')}`);
    // }

    visionResultContainer.classList.remove('hidden');
    visionResultContainer.innerHTML = `
        <div class="vision-result-summary">
            ${lines.length ? lines.map((line) => `<p>${line}</p>`).join('') : '<p>⚠️ Could not detect vehicle details. Please try another image or fill the form manually.</p>'}
            ${analysis.detected_brand ? '<button id="autofillBtn" type="button" class="primary-button" style="margin-top: 15px;">Auto-fill Form</button>' : ''}
            <div id="autofillMessage" style="margin-top: 10px; padding: 10px; border-radius: 8px; display: none;"></div>
        </div>
    `;
    
    // Add click handler for auto-fill button
    if (analysis.detected_brand) {
        const autofillBtn = document.getElementById('autofillBtn');
        if (autofillBtn) {
            autofillBtn.addEventListener('click', async () => {
                const messageDiv = document.getElementById('autofillMessage');
                messageDiv.style.display = 'none';
                autofillBtn.disabled = true;
                autofillBtn.textContent = 'Auto-filling...';
                
                const result = await autofillVehicleFromVision(analysis);
                
                if (result.success) {
                    autofillBtn.textContent = 'Form Auto-filled ✓';
                    messageDiv.style.display = 'block';
                    messageDiv.style.background = '#d1fae5';
                    messageDiv.style.color = '#065f46';
                    messageDiv.innerHTML = `✅ ${result.message}`;
                } else {
                    autofillBtn.textContent = 'Auto-fill Form';
                    messageDiv.style.display = 'block';
                    messageDiv.style.background = '#fee2e2';
                    messageDiv.style.color = '#991b1b';
                    messageDiv.innerHTML = `⚠️ ${result.message}`;
                }
                
                setTimeout(() => {
                    autofillBtn.disabled = false;
                    if (result.success) {
                        autofillBtn.textContent = 'Auto-fill Form';
                    }
                }, 2000);
            });
        }
    }
};

const autofillVehicleFromVision = async (analysis) => {
    if (!analysis) return { success: false, message: 'No analysis data available.' };

    // Smart brand matching
    let matchedBrand = null;
    if (analysis.detected_brand) {
        const detectedLower = analysis.detected_brand.toLowerCase();
        matchedBrand = brandOptions.find(b => b.toLowerCase() === detectedLower);
        if (!matchedBrand) {
            matchedBrand = brandOptions.find(b => 
                b.toLowerCase().includes(detectedLower) || detectedLower.includes(b.toLowerCase())
            );
        }
    }

    if (!matchedBrand) {
        return { 
            success: false, 
            message: `Brand "${analysis.detected_brand}" not in database. Price prediction under development. Please select manually.` 
        };
    }

    brandSelect.value = matchedBrand;
    brandSearchInput.value = matchedBrand;
    await loadModels(matchedBrand);
    
    if (modelOptions.length === 0) {
        return { 
            success: false, 
            message: `No models for "${matchedBrand}". Price prediction under development.` 
        };
    }
    
    let matchedModel = null;
    if (analysis.detected_model) {
        const detectedModelLower = analysis.detected_model.toLowerCase();
        matchedModel = modelOptions.find(m => 
            m.toLowerCase().includes(detectedModelLower) || detectedModelLower.includes(m.toLowerCase())
        );
        
        if (!matchedModel) {
            return { 
                success: false, 
                message: `Model "${analysis.detected_model}" not in database. Available: ${modelOptions.join(', ')}. Please select manually.` 
            };
        }
    } else {
        matchedModel = modelOptions[0];
    }
    
    modelSelect.value = matchedModel;
    await loadVehicleDetails(matchedBrand, matchedModel);

    if (analysis.detected_body_type && bodyInput.value !== analysis.detected_body_type) {
        bodyInput.value = analysis.detected_body_type;
    }

    if (analysis.estimated_year && (!carAgeInput.value || Number(carAgeInput.value) <= 0)) {
        const year = Number(analysis.estimated_year);
        if (!Number.isNaN(year)) {
            const computedAge = new Date().getFullYear() - year;
            if (computedAge > 0 && computedAge < 50) {
                carAgeInput.value = computedAge;
            }
        }
    }
    
    return { 
        success: true, 
        message: `Form auto-filled! Brand: ${matchedBrand}, Model: ${matchedModel}. Please verify and add remaining details.` 
    };
};

const analyzeVehicleImages = async () => {
    if (!imageInputs.main || !imageInputs.main.files || !imageInputs.main.files[0]) {
        showStatus('Please upload a primary image before analysis.', true);
        return;
    }

    const formData = buildVisionFormData();
    analyzeImagesBtn.disabled = true;
    analyzeImagesBtn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite">⏳</span> Analyzing...';
    showStatus('🔍 Analyzing image with AWS Bedrock Nova Lite...');

    try {
        const response = await fetch(`${API_URL}/vision/analyze`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => null);
            const message = errorPayload?.detail || `Vision API responded with ${response.status}`;
            throw new Error(message);
        }

        const result = await response.json();
        renderVisionResult(result);
        showStatus('Vision analysis complete. Click "Auto-fill Form" button to populate the form.');
    } catch (error) {
        console.error('Vision analysis failed:', error);
        showStatus(error.message || 'Vision analysis failed.', true);
    } finally {
        analyzeImagesBtn.disabled = false;
        analyzeImagesBtn.textContent = 'Analyze Image';
    }
};

const analyzeDamage = async () => {
    const damageImageInput = document.getElementById('damageImage');
    if (!damageImageInput || !damageImageInput.files || !damageImageInput.files[0]) {
        showStatus('Please upload a damage image before analysis.', true);
        return;
    }

    const analyzeDamageBtn = document.getElementById('analyzeDamageBtn');
    const formData = new FormData();
    formData.append('image', damageImageInput.files[0]);
    
    analyzeDamageBtn.disabled = true;
    analyzeDamageBtn.innerHTML = '<span style="display:inline-block;animation:spin 1s linear infinite">⏳</span> Detecting...';
    showStatus('🔍 Detecting damage with AWS Bedrock Nova Lite...');

    try {
        const response = await fetch(`${API_URL}/vision/detect-damage`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const errorPayload = await response.json().catch(() => null);
            const message = errorPayload?.detail || `Damage detection failed with ${response.status}`;
            throw new Error(message);
        }

        const result = await response.json();
        renderDamageResult(result);
        showStatus('Damage detection complete. Review and accept to auto-fill damage description.');
    } catch (error) {
        console.error('Damage detection failed:', error);
        showStatus(error.message || 'Damage detection failed.', true);
    } finally {
        analyzeDamageBtn.disabled = false;
        analyzeDamageBtn.textContent = 'Detect Damage';
    }
};

const renderDamageResult = (result) => {
    const damageResultContainer = document.getElementById('damageResult');
    if (!damageResultContainer) return;

    const severityColors = {
        none: '#28a745',
        minor: '#ffc107',
        medium: '#fd7e14',
        major: '#dc3545'
    };

    const severityIcons = {
        none: '✅',
        minor: '⚠️',
        medium: '🔶',
        major: '🚨'
    };

    const color = severityColors[result.damage_severity] || '#6c757d';
    const icon = severityIcons[result.damage_severity] || '🔍';

    damageResultContainer.innerHTML = `
        <div style="padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid ${color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: ${color};">${icon} Damage Detection Result</h4>
                <span style="background: ${color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: bold;">
                    ${result.damage_severity.toUpperCase()}
                </span>
            </div>
            <div style="margin: 10px 0;">
                <strong>Status:</strong> ${result.has_damage ? 'Damage Detected' : 'No Damage Detected'}
            </div>
            <div style="margin: 10px 0;">
                <strong>Description:</strong><br>
                <span style="color: #495057;">${result.damage_description}</span>
            </div>
            ${result.damage_areas && result.damage_areas.length > 0 ? `
                <div style="margin: 10px 0;">
                    <strong>Affected Areas:</strong> ${result.damage_areas.join(', ')}
                </div>
            ` : ''}
            <div style="margin: 10px 0;">
                <strong>Confidence:</strong> ${result.confidence}%
            </div>
            <button onclick="acceptDamageDescription('${result.damage_description.replace(/'/g, "\\'")}', '${result.damage_severity}')" 
                    style="margin-top: 10px; padding: 8px 16px; background: ${color}; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: 500;">
                ✓ Accept & Auto-fill Damage Description
            </button>
        </div>
    `;
    damageResultContainer.classList.remove('hidden');
};

window.acceptDamageDescription = (description, severity) => {
    const damageDescriptionField = document.getElementById('damage_description');
    if (damageDescriptionField) {
        damageDescriptionField.value = description;
        damageDescriptionField.readOnly = false;
        showStatus(`✅ Damage description auto-filled (${severity}). You can edit if needed.`);
    }
};

const printCurrentReport = () => {
    if (!lastPredictionPayload || lastPredictedPrice == null) {
        alert('Run a valuation first to print a report.');
        return;
    }

    const reportHtml = `
        <html>
        <head>
            <title>Vehicle Valuation Report</title>
            <style>
                body { font-family: Inter, system-ui, sans-serif; margin: 32px; color: #111827; }
                h1 { font-size: 2rem; margin-bottom: 12px; }
                .section { margin-bottom: 20px; }
                .section strong { display: inline-block; width: 140px; color: #334155; }
                .value { font-weight: 700; color: #0f172a; }
                .price { font-size: 2rem; margin-top: 16px; color: #16a34a; }
            </style>
        </head>
        <body>
            <h1>Vehicle Valuation Report</h1>
            <div class="section">
                <p><strong>Brand:</strong> <span class="value">${lastPredictionPayload.oem}</span></p>
                <p><strong>Model:</strong> <span class="value">${lastPredictionPayload.model}</span></p>
                <p><strong>Variant:</strong> <span class="value">${lastPredictionPayload.variant}</span></p>
                <p><strong>Fuel:</strong> <span class="value">${lastPredictionPayload.fuel}</span></p>
                <p><strong>Transmission:</strong> <span class="value">${lastPredictionPayload.transmission}</span></p>
                <p><strong>Body:</strong> <span class="value">${lastPredictionPayload.body}</span></p>
            </div>
            <div class="section">
                <p><strong>Ownership:</strong> <span class="value">${lastPredictionPayload.owner_type}</span></p>
                <p><strong>Location:</strong> <span class="value">${lastPredictionPayload.City}, ${lastPredictionPayload.state}</span></p>
                <p><strong>Kilometers:</strong> <span class="value">${lastPredictionPayload.km} km</span></p>
                <p><strong>Car Age:</strong> <span class="value">${lastPredictionPayload.car_age} years</span></p>
                <p><strong>Premium Brand:</strong> <span class="value">${lastPredictionPayload.premium_brand}</span></p>
                <p><strong>Damage Notes:</strong> <span class="value">${lastPredictionPayload.damage_description || 'None'}</span></p>
            </div>
            <div class="section price">
                Estimated Market Price: <strong>₹ ${Number(lastPredictedPrice).toLocaleString('en-IN')}</strong>
            </div>
            <div class="section">
                <p><strong>Damage Cost:</strong> <span class="value">${damageCostOutput.textContent}</span></p>
                <p><strong>Confidence Score:</strong> <span class="value">${confidenceOutput.textContent}</span></p>
                <p><strong>Suggested Selling Price:</strong> <span class="value">${suggestedPriceOutput.textContent}</span></p>
            </div>
            <div class="section">
                <small>Generated on ${new Date().toLocaleString('en-IN')}</small>
            </div>
        </body>
        </html>
    `;

    const printWindow = window.open('', '_blank');
    if (!printWindow) {
        alert('Unable to open print window.');
        return;
    }
    printWindow.document.write(reportHtml);
    printWindow.document.close();
    printWindow.focus();
    printWindow.print();
};

const getFilteredHistory = (history) => {
    const searchTerm = historySearchInput.value.trim().toLowerCase();

    if (!searchTerm) {
        return history;
    }

    return history.filter((entry) => {
        return [
            entry.brand,
            entry.model,
            entry.variant,
            entry.fuel,
            entry.transmission,
            entry.body,
            entry.owner_type,
            entry.City,
            entry.state,
        ]
            .filter(Boolean)
            .some((value) => value.toString().toLowerCase().includes(searchTerm));
    });
};

const formatCurrency = (value) => {
    return `₹ ${Number(value).toLocaleString('en-IN')}`;
};

const updateHistoryMetrics = (history) => {
    const total = history.length;
    const averagePrice = total ? history.reduce((sum, item) => sum + Number(item.predicted_price), 0) / total : 0;
    const latestCity = total ? history[0].City : '--';

    historyCount.textContent = total;
    document.getElementById('historyAverage').textContent = total ? formatCurrency(averagePrice.toFixed(2)) : '₹ --';
    document.getElementById('historyRecentCity').textContent = latestCity || '--';
};

let showFullHistory = false;

const toggleFullHistory = () => {
    showFullHistory = !showFullHistory;
    renderHistory();
};

const renderHistory = async () => {
    historyCache = await loadHistory();
    const filteredHistory = getFilteredHistory(historyCache);
    updateHistoryMetrics(historyCache);
    historyCount.textContent = filteredHistory.length;
    historyList.innerHTML = '';

    if (filteredHistory.length === 0) {
        const empty = document.createElement('div');
        empty.className = 'history-empty';
        empty.textContent = 'No matching history records. Try another search term.';
        historyList.appendChild(empty);
        document.getElementById('viewAllHistoryBtn').style.display = 'none';
        return;
    }

    // Show only last 2 by default, or all if toggled
    const displayLimit = showFullHistory ? filteredHistory.length : 2;
    const displayHistory = filteredHistory.slice(0, displayLimit);
    
    // Show/hide "View All" button
    const viewAllBtn = document.getElementById('viewAllHistoryBtn');
    if (filteredHistory.length > 2) {
        viewAllBtn.style.display = 'block';
        viewAllBtn.querySelector('button').textContent = showFullHistory 
            ? '📋 Show Less' 
            : `📋 View All History (${filteredHistory.length} records)`;
    } else {
        viewAllBtn.style.display = 'none';
    }

    displayHistory.forEach((entry) => {
        const item = document.createElement('div');
        item.className = 'history-item';

        item.innerHTML = `
            <p><strong>${entry.brand} ${entry.model} - ${entry.variant}</strong></p>
            <p>Price: ${formatCurrency(entry.predicted_price)}</p>
            <p>Mileage: ${entry.km} km · Age: ${entry.car_age} yr · Owner: ${entry.owner_type}</p>
            <p>Location: ${entry.City}, ${entry.state}</p>
            <p>Fuel: ${entry.fuel} · Trans: ${entry.transmission} · Body: ${entry.body}</p>
            <time>${formatDateTime(entry.created_at)}</time>
        `;

        historyList.appendChild(item);
    });
};

const exportHistoryAsCsv = () => {
    const header = ['Brand', 'Model', 'Variant', 'Fuel', 'Transmission', 'Body', 'Owner Type', 'City', 'State', 'KM', 'Car Age', 'Premium Brand', 'Predicted Price', 'Created At'];
    const rows = historyCache.map((entry) => [
        entry.brand,
        entry.model,
        entry.variant,
        entry.fuel,
        entry.transmission,
        entry.body,
        entry.owner_type,
        entry.City,
        entry.state,
        entry.km,
        entry.car_age,
        entry.premium_brand,
        Number(entry.predicted_price).toFixed(2),
        entry.created_at,
    ]);

    const csvContent = [header, ...rows]
        .map((row) => row.map((value) => `"${String(value).replace(/"/g, '""')}"`).join(','))
        .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `vehicle_prediction_history_${new Date().toISOString().slice(0, 10)}.csv`;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

const refreshHistory = async () => {
    await renderHistory();
};

const clearHistory = async () => {
    try {
        const response = await fetch(buildUrl('/history'), { method: 'DELETE' });
        if (!response.ok) {
            throw new Error(`Clear history API responded with status ${response.status}`);
        }
    } catch (error) {
        console.error('Cannot clear history:', error);
    } finally {
        await renderHistory();
    }
};

brandSelect.addEventListener('change', async function () {
    const brand = this.value;
    await loadModels(brand);
});

modelSelect.addEventListener('change', async function () {
    const brand = brandSelect.value;
    const model = this.value;
    await loadVehicleDetails(brand, model);
});

const showStatus = (message, isError = false) => {
    statusOutput.textContent = message;
    statusOutput.style.color = isError ? '#d9534f' : '#2a7f62';
};

const generatePricingSummary = (result, transactionType, payload) => {
    const summaryDiv = document.getElementById('pricingSummary');
    const summaryContent = document.getElementById('summaryContent');
    
    const marketValue = result.predicted_price - result.damage_cost;
    let summaryHTML = '';
    
    if (transactionType === 'selling') {
        // Selling mode - no margin breakdown
        summaryHTML = `
            <strong>Selling Mode</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Base Market Value: ₹${result.predicted_price.toLocaleString('en-IN')}</li>
                ${result.damage_cost > 0 ? `<li>Damage Deduction: -₹${result.damage_cost.toLocaleString('en-IN')}</li>` : ''}
                <li>Final Selling Price: ₹${result.transaction_price.toLocaleString('en-IN')}</li>
            </ul>
            <p style="margin: 5px 0; color: #666; font-size: 13px;">💡 This is the fair market value you can expect when selling your car.</p>
        `;
    } else if (transactionType === 'buying_resale') {
        // Buying for resale - show margin breakdown
        const marginPercent = (result.profit_margin / marketValue * 100).toFixed(1);
        
        // Calculate margin factors
        const factors = [];
        if (payload.premium_brand === 1) factors.push('Premium brand (+5%)');
        if (result.predicted_price > 2000000) factors.push('High price range (+5%)');
        else if (result.predicted_price > 1000000) factors.push('Mid-premium range (+3%)');
        else if (result.predicted_price < 300000) factors.push('Budget range (-2%)');
        
        if (payload.car_age > 10) factors.push('Very old car (+5%)');
        else if (payload.car_age > 7) factors.push('Old car (+2%)');
        else if (payload.car_age < 3) factors.push('Nearly new (-2%)');
        
        if (payload.km > 100000) factors.push('High mileage (+2%)');
        
        if (payload.damage_description) {
            const dmg = payload.damage_description.toLowerCase();
            if (dmg.includes('major') || dmg.includes('accident')) factors.push('Major damage (+5%)');
            else if (dmg.includes('broken') || dmg.includes('collision')) factors.push('Medium damage (+3%)');
            else factors.push('Minor damage (+1%)');
        }
        
        const owner = payload.owner_type.toLowerCase();
        if (owner.includes('second')) factors.push('Second owner (+1%)');
        else if (owner.includes('third')) factors.push('Third owner (+2%)');
        else if (owner.includes('fourth')) factors.push('Fourth+ owner (+3%)');
        
        summaryHTML = `
            <strong>Buying for Resale - Margin Breakdown</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Market Value: ₹${marketValue.toLocaleString('en-IN')}</li>
                <li>Profit Margin: ${marginPercent}% (₹${result.profit_margin.toLocaleString('en-IN')})</li>
                <li>Max Buy Price: ₹${result.transaction_price.toLocaleString('en-IN')}</li>
            </ul>
            <strong style="font-size: 13px;">Margin Factors Applied:</strong>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 13px;">
                ${factors.length > 0 ? factors.map(f => `<li>${f}</li>`).join('') : '<li>Base margin: 10%</li>'}
            </ul>
            <p style="margin: 5px 0; color: #666; font-size: 13px;">💡 Higher risk factors = Higher margin to protect your investment.</p>
        `;
    } else if (transactionType === 'buying_personal') {
        // Buying personal - show fair range
        summaryHTML = `
            <strong>Buying for Personal Use</strong>
            <ul style="margin: 10px 0; padding-left: 20px;">
                <li>Market Value: ₹${marketValue.toLocaleString('en-IN')}</li>
                <li>Fair Buy Range: ₹${result.price_range_min.toLocaleString('en-IN')} - ₹${result.price_range_max.toLocaleString('en-IN')}</li>
                <li>Target Price: ₹${result.transaction_price.toLocaleString('en-IN')} (5% below market)</li>
            </ul>
            <strong style="font-size: 13px;">Negotiation Tips:</strong>
            <ul style="margin: 5px 0; padding-left: 20px; font-size: 13px;">
                <li>Start offer at lower end of range</li>
                <li>Don't pay more than upper limit</li>
                <li>Factor in repair costs if damaged</li>
            </ul>
            <p style="margin: 5px 0; color: #666; font-size: 13px;">💡 This range gives you negotiation power while staying fair.</p>
        `;
    }
    
    summaryContent.innerHTML = summaryHTML;
    summaryDiv.style.display = 'block';
};


const submitForm = async (event) => {
    event.preventDefault();

    const brand = brandSelect.value;
    const model = modelSelect.value;
    const variant = variantSelect.value;
    const fuel = fuelSelect.value;
    const transmission = transmissionSelect.value;
    const body = bodyInput.value;
    const km = Number(kmInput.value);
    const car_age = Number(carAgeInput.value);
    const owner_type = ownerTypeSelect.value;
    const City = cityInput.value.trim();
    const state = stateInput.value.trim();
    const premium_brand = premiumBrandInput.value === "Yes" ? 1 : 0;
    const transaction_type = document.getElementById('transaction_type').value;

    if (!brand || !model || !variant || !fuel || !transmission || !body) {
        showStatus('Please select brand and model first.', true);
        priceOutput.textContent = '₹ --';
        return;
    }

    if (!km || !car_age) {
        showStatus('Please enter valid mileage and car age.', true);
        priceOutput.textContent = '₹ --';
        return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Predicting...';
    priceOutput.textContent = 'Predicting...';
    showStatus('AI Model Running...');

    const payload = {
        oem: brand,
        model,
        variant,
        fuel,
        transmission,
        body,
        owner_type,
        City,
        state,
        km,
        car_age,
        premium_brand,
        damage_description: damageDescriptionInput.value.trim() || null,
        transaction_type: transaction_type,
    };

    try {
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            throw new Error(`Predict API responded with status ${response.status}`);
        }

        const result = await response.json();
        lastPredictionPayload = payload;
        lastPredictedPrice = result.predicted_price;
        
        // Update transaction badge
        const transactionBadge = document.getElementById('transactionBadge');
        const badgeText = {
            'selling': '🔴 Selling',
            'buying_resale': '🟢 Buy-Resale',
            'buying_personal': '🔵 Buy-Personal'
        };
        transactionBadge.textContent = badgeText[transaction_type] || 'Selling';
        
        // Update main price display
        const formattedPrice = `₹ ${Number(result.transaction_price).toLocaleString('en-IN')}`;
        
        // For buying_personal, show price range in main display
        if (transaction_type === 'buying_personal' && result.price_range_min && result.price_range_max) {
            priceOutput.textContent = `₹ ${Number(result.price_range_min).toLocaleString('en-IN')} - ₹ ${Number(result.price_range_max).toLocaleString('en-IN')}`;
        } else {
            priceOutput.textContent = formattedPrice;
        }
        
        // Update market value
        document.getElementById('marketValue').textContent = `₹ ${Number(result.predicted_price).toLocaleString('en-IN')}`;
        
        // Update damage cost
        damageCostOutput.textContent = result.damage_cost ? `₹ ${Number(result.damage_cost).toLocaleString('en-IN')}` : '₹ 0';
        
        // Update confidence
        confidenceOutput.textContent = `${result.confidence_score}%`;
        
        // Show/hide profit margin row
        const profitRow = document.getElementById('profitRow');
        const marginPercentRow = document.getElementById('marginPercentRow');
        if (transaction_type === 'buying_resale' && result.profit_margin) {
            profitRow.style.display = 'flex';
            marginPercentRow.style.display = 'flex';
            document.getElementById('profitMargin').textContent = `₹ ${Number(result.profit_margin).toLocaleString('en-IN')}`;
            
            // Calculate and display margin percentage
            const marketValue = result.predicted_price - result.damage_cost;
            const marginPercent = (result.profit_margin / marketValue * 100).toFixed(1);
            document.getElementById('marginPercent').textContent = `${marginPercent}%`;
        } else {
            profitRow.style.display = 'none';
            marginPercentRow.style.display = 'none';
        }
        
        // Show/hide price range row
        const priceRangeRow = document.getElementById('priceRangeRow');
        if ((transaction_type === 'buying_resale' || transaction_type === 'buying_personal') && result.price_range_min && result.price_range_max) {
            priceRangeRow.style.display = 'flex';
            document.getElementById('priceRange').textContent = `₹ ${Number(result.price_range_min).toLocaleString('en-IN')} to ₹ ${Number(result.price_range_max).toLocaleString('en-IN')}`;
        } else {
            priceRangeRow.style.display = 'none';
        }
        
        // Update final price label
        const finalPriceLabel = document.getElementById('finalPriceLabel');
        const labels = {
            'selling': 'Selling Price',
            'buying_resale': 'Max Buy Price',
            'buying_personal': 'Fair Market Price'
        };
        finalPriceLabel.textContent = labels[transaction_type] || 'Transaction Price';
        
        // Update suggested price
        suggestedPriceOutput.textContent = `₹ ${Number(result.transaction_price).toLocaleString('en-IN')}`;
        
        // Update Market Intelligence Section (NEW)
        updateMarketIntelligence(result);
        
        // Update status message
        const statusMessages = {
            'selling': 'Prediction Successful — selling price calculated.',
            'buying_resale': 'Prediction Successful — max buy price for 10% profit.',
            'buying_personal': 'Prediction Successful — fair market value calculated.'
        };
        showStatus(statusMessages[transaction_type] || 'Prediction Successful');
        
        // Generate pricing summary
        generatePricingSummary(result, transaction_type, payload);
        
        // Scroll to results section
        setTimeout(() => {
            document.querySelector('.result-card')?.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
        }, 100);
        
        await refreshHistory();
    } catch (error) {
        console.error(error);
        priceOutput.textContent = 'Prediction Failed';
        showStatus('API Error', true);
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Predict Vehicle Price';
    }
};

document.getElementById('valuationForm').addEventListener('submit', submitForm);
clearHistoryBtn.addEventListener('click', clearHistory);
exportHistoryBtn.addEventListener('click', exportHistoryAsCsv);
printReportBtn.addEventListener('click', printCurrentReport);
analyzeImagesBtn.addEventListener('click', analyzeVehicleImages);
// DAMAGE DETECTION DISABLED
// document.getElementById('analyzeDamageBtn').addEventListener('click', analyzeDamage);

// Function to update Market Intelligence display
function updateMarketIntelligence(result) {
    const marketIntelligenceDiv = document.getElementById('marketIntelligence');
    
    // Check if market data is available
    if (result.market_data_available) {
        marketIntelligenceDiv.style.display = 'block';
        
        // Update confidence badge
        const confidenceBadge = document.getElementById('marketConfidenceBadge');
        const confidenceText = {
            'high': '🟢 High Confidence',
            'medium': '🟡 Medium Confidence',
            'low': '🟠 Low Confidence',
            'very_low': '🔴 Very Low Confidence',
            'none': '⚪ No Data'
        };
        confidenceBadge.textContent = confidenceText[result.market_confidence] || 'Unknown';
        
        // Update ML Prediction
        document.getElementById('mlPrediction').textContent = 
            result.ml_prediction ? `₹ ${Number(result.ml_prediction).toLocaleString('en-IN')}` : '₹ --';
        
        // Update Market Average
        document.getElementById('marketAverage').textContent = 
            result.market_average ? `₹ ${Number(result.market_average).toLocaleString('en-IN')}` : 'N/A';
        
        // Update Market Median
        document.getElementById('marketMedian').textContent = 
            result.market_median ? `₹ ${Number(result.market_median).toLocaleString('en-IN')}` : 'N/A';
        
        // Update sample size
        const sampleSize = result.market_sample_size || 0;
        document.getElementById('marketSampleSize').innerHTML = 
            `<strong>📈 Based on ${sampleSize} similar car${sampleSize !== 1 ? 's' : ''}</strong> in the market (last 30 days)`;
        
        // Calculate and show adjustment
        if (result.ml_prediction && result.predicted_price) {
            const adjustment = result.predicted_price - result.ml_prediction;
            const adjustmentPercent = ((adjustment / result.ml_prediction) * 100).toFixed(2);
            const adjustmentText = adjustment > 0 ? 
                `<span style="color: #4ade80;">↗ Increased by ₹${Math.abs(adjustment).toLocaleString('en-IN')} (+${adjustmentPercent}%)</span>` :
                adjustment < 0 ?
                `<span style="color: #f87171;">↘ Decreased by ₹${Math.abs(adjustment).toLocaleString('en-IN')} (${adjustmentPercent}%)</span>` :
                `<span style="color: #fbbf24;">→ No adjustment (0%)</span>`;
            
            document.getElementById('marketAdjustment').innerHTML = 
                `<strong>Price Adjustment:</strong> ${adjustmentText} based on current market trends`;
        }
    } else {
        // No market data available
        marketIntelligenceDiv.style.display = 'block';
        document.getElementById('marketConfidenceBadge').textContent = '⚪ No Market Data';
        document.getElementById('mlPrediction').textContent = 
            result.ml_prediction ? `₹ ${Number(result.ml_prediction).toLocaleString('en-IN')}` : '₹ --';
        document.getElementById('marketAverage').textContent = 'N/A';
        document.getElementById('marketMedian').textContent = 'N/A';
        document.getElementById('marketSampleSize').innerHTML = 
            '<strong>ℹ️ No similar cars found in our database</strong>';
        document.getElementById('marketAdjustment').innerHTML = 
            'Price is based purely on ML model prediction. Consider checking multiple sources.';
    }
}

// Brand search with autocomplete
brandSearchInput.addEventListener('input', debounce(async (e) => {
    const q = e.target.value.trim();
    let suggestions = [];
    if (!q) {
        suggestions = brandOptions;
    } else {
        // Fetch suggestions from API
        suggestions = await fetchBrandSuggestions(q);
    }
    brandOptions = suggestions;
    setSelectOptions(brandSelect, suggestions, 'Select Brand');
    updateBrandDatalist(suggestions);
    renderSuggestions(suggestions, q);
}, 200));

brandSearchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        clearSuggestions();
    }
});

brandSearchInput.addEventListener('blur', () => {
    // Hide after a short delay to allow click handler to run
    setTimeout(() => clearSuggestions(), 150);
});

brandSearchInput.addEventListener('change', async (e) => {
    const chosen = e.target.value.trim();
    if (!chosen) return;
    if (!brandOptions.includes(chosen)) {
        const res = await fetchBrandSuggestions(chosen);
        brandOptions = res;
        setSelectOptions(brandSelect, brandOptions, 'Select Brand');
        updateBrandDatalist(brandOptions);
    }
    if (brandOptions.includes(chosen)) {
        brandSelect.value = chosen;
        modelSelect.disabled = false;
        await loadModels(chosen);
    }
});

// Model select - show message if brand not selected
modelSelect.addEventListener('focus', (e) => {
    if (!brandSelect.value) {
        alert('Please select a brand first');
        e.target.blur();
    }
});

historySearchInput.addEventListener('input', renderHistory);

loadBrands().then(renderHistory);
