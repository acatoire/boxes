/* Sheet presets and per-part measurement used by the sheet-fit estimate.
   Loaded before self.js; the globals below are shared with it. */

/** Standard sheet sizes (landscape, mm) */
const SHEET_PRESETS = [
    {label: '30 \u00d7 30 cm', w: 300, h: 300},
    {label: 'A3', w: 420, h: 297},
    {label: 'A4', w: 297, h: 210},
    {label: 'A5', w: 210, h: 148},
    {label: 'A6', w: 148, h: 105},
];

let _svgParts = [];
const PACKING_EFFICIENCY = 0.85;  // usable share of a sheet when nesting parts

/** Bounding box (mm) of every top-level part group (<g id="p-N">) of the SVG. */
function _measureSvgParts(svgText) {
    const doc = new DOMParser().parseFromString(svgText, 'image/svg+xml');
    const src = doc.documentElement;
    if (!src || src.nodeName.toLowerCase() !== 'svg') return [];
    const host = document.createElement('div');
    host.style.cssText = 'position:absolute;left:-99999px;top:0;visibility:hidden;pointer-events:none;';
    const svg = document.importNode(src, true);
    host.appendChild(svg);
    document.body.appendChild(host);
    const parts = [];
    try {
        // viewBox is in mm (1 user unit = 1 mm), so bbox values are mm.
        svg.querySelectorAll(':scope > g[id^="p-"]').forEach(g => {
            try {
                const b = g.getBBox();
                if (b.width > 0 && b.height > 0) parts.push({id: g.id, w: b.width, h: b.height});
            } catch (_) { /* ignore unmeasurable group */ }
        });
    } finally {
        document.body.removeChild(host);
    }
    return parts;
}

function _renderPartsDetails() {
    const box = document.getElementById('parts-info-details');
    if (!box) return;
    const list = box.querySelector('.parts-info-list');
    const summary = box.querySelector('summary');
    if (!list || !summary || !_svgParts.length) {
        box.style.display = 'none';
        return;
    }
    const total = _svgParts.reduce((s, p) => s + p.w * p.h, 0);
    const cfg = loadMachineConfig();
    summary.textContent = `\ud83e\udde9 ${_svgParts.length} part${_svgParts.length > 1 ? 's' : ''}`
        + ` \u2022 ${(total / 1_000_000).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} m\u00b2`;
    const rows = _svgParts.map((p, i) =>
        `<tr><td>${i + 1}</td><td>${p.w.toFixed(1)} \u00d7 ${p.h.toFixed(1)} mm</td>`
        + `<td>${(p.w * p.h / 1_000_000).toFixed(3)} m\u00b2</td></tr>`).join('');
    list.innerHTML =
        `<div class="parts-info-sheet">\ud83d\udccf Sheet: ${cfg.w} \u00d7 ${cfg.h} mm`
        + ` (${(cfg.w * cfg.h / 1_000_000).toFixed(3)} m\u00b2 = 1m\u00b2/${Math.round(1_000_000 / (cfg.w * cfg.h))})</div>`
        + `<table><tbody>${rows}</tbody></table>`;
    box.style.display = '';
}

/** Per-part sheet estimate; returns {ok, text} or null when a part exceeds one sheet. */
function _partsSheetEstimate(mw, mh) {
    if (!_svgParts.length) return null;
    const allFit = _svgParts.every(p => (p.w <= mw && p.h <= mh) || (p.h <= mw && p.w <= mh));
    if (!allFit) return null;
    const area = _svgParts.reduce((s, p) => s + p.w * p.h, 0);
    const sheets = Math.max(1, Math.ceil(area / (mw * mh * PACKING_EFFICIENCY)));
    if (sheets === 1) return {ok: true, text: '\u2705 Fits on 1 sheet'};
    return {ok: false, text: `\u26a0\ufe0f Needs ~${sheets} sheets (estimated from ${_svgParts.length} parts)`};
}
/** Total area (m2) of all parts; falls back to the whole drawing area. */
function _usedAreaM2() {
    if (_svgParts.length) return _svgParts.reduce((s, p) => s + p.w * p.h, 0) / 1_000_000;
    return _svgDims ? (_svgDims.w * _svgDims.h) / 1_000_000 : 0;
}
/** Collapsible price list: selected material in the summary, every material inside. */
function _renderPriceDetails(price, selectedId, margin) {
    const fmt = v => v.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2});
    const area = _usedAreaM2();
    const priceOf = m => area * m.price_per_m2 * margin;
    const sel = MATERIALS.find(m => m.id === selectedId);
    if (!sel) {
        price.innerHTML = '';
        return;
    }
    const wasOpen = !!price.querySelector('details[open]');
    const rows = MATERIALS.map(m =>
        `<tr${m.id === sel.id ? ' class="price-selected"' : ''}><td>${m.label}</td>`
        + `<td>${fmt(priceOf(m))} \u20ac</td></tr>`).join('');
    price.innerHTML =
        `<details class="price-details"${wasOpen ? ' open' : ''}>`
        + `<summary>\ud83d\udcb6 ${sel.label} \u2022 ${fmt(priceOf(sel))} \u20ac</summary>`
        + `<div class="parts-info-list"><table><tbody>${rows}</tbody></table></div></details>`;
    price.style.display = 'flex';
}

/*** Machine page: radio-button views of the preset / material selects ***/
function _fmtEur(v) {
    return v.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2}) + ' \u20ac';
}
function _sheetFraction(w, h) {
    const area = w * h;
    if (!(area > 0)) return '';
    return `${(area / 1_000_000).toFixed(3)} m\u00b2 = 1m\u00b2/${Math.round(1_000_000 / area)}`;
}
function _radioRow(name, value, checked, label, side) {
    return `<label class="ms-radio"><input type="radio" name="${name}" value="${value}"${checked ? ' checked' : ''}>`
        + `<span class="ms-radio-label">${label}</span><span class="ms-radio-side">${side}</span></label>`;
}
function _renderPresetRadios() {
    const sel = document.getElementById('machine-preset');
    const box = document.getElementById('machine-preset-radios');
    if (!sel || !box) return;
    const cfg = loadMachineConfig();
    const mat = MATERIALS.find(m => m.id === cfg.material);
    const margin = parseFloat(cfg.margin_coef) || 1;
    const row = o => {
        const [w, h] = o.value ? o.value.split('x').map(Number) : [0, 0];
        let side = o.value ? _sheetFraction(w, h) : '';
        if (o.value && mat) {
            const before = (w * h / 1_000_000) * mat.price_per_m2;
            side += ' \u2022 ' + (margin === 1
                ? _fmtEur(before)
                : `${_fmtEur(before)} \u2192 ${_fmtEur(before * margin)}`);
        }
        return _radioRow('machine-preset-r', o.value, sel.value === o.value, o.textContent, side);
    };
    let html = '';
    for (const node of sel.children) {
        if (node.tagName === 'OPTGROUP') {
            html += `<div class="ms-radio-group">${node.label}</div>`;
            html += Array.from(node.children).map(row).join('');
        } else {
            html += row(node);
        }
    }
    box.innerHTML = html;
}
function _renderMaterialRadios() {
    const sel = document.getElementById('machine-material');
    const box = document.getElementById('machine-material-radios');
    if (!sel || !box) return;
    const cfg = loadMachineConfig();
    let html = _radioRow('machine-material-r', '', !cfg.material, 'Turn off material calculation', '');
    for (const m of MATERIALS) {
        html += _radioRow('machine-material-r', m.id, cfg.material === m.id, m.label,
            `${m.price_per_m2} \u20ac/m\u00b2`);
    }
    box.innerHTML = html;
}
function initMachineRadios() {
    const presetSel = document.getElementById('machine-preset');
    const matSel = document.getElementById('machine-material');
    const presetBox = document.getElementById('machine-preset-radios');
    const matBox = document.getElementById('machine-material-radios');
    if (!presetSel || !presetBox) return;
    const refresh = () => { _renderPresetRadios(); _renderMaterialRadios(); };
    refresh();
    if (!presetBox.dataset.bound) {
        presetBox.dataset.bound = '1';
        presetBox.addEventListener('change', e => {
            presetSel.value = e.target.value;
            presetSel.dispatchEvent(new Event('change'));
            refresh();
        });
        if (matBox && matSel) {
            matBox.addEventListener('change', e => {
                matSel.value = e.target.value;
                matSel.dispatchEvent(new Event('change'));
                refresh();
            });
        }
        for (const id of ['machine-w', 'machine-h', 'machine-margin-coef']) {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', refresh);
        }
    }
}
