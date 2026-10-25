/*** Materials: editable and saved in the browser ***************************
 *
 * Needs the constant MATERIALS from self.js ("Machine configuration"). Load
 * this file after self.js (see genHTMLJS in home_legacy.py).
 * The built-in list stays as the default; edits are stored in localStorage.
 * MATERIALS is changed in place, so every function that reads it (for example
 * the price calculation) automatically sees the saved values.
 * The look follows machine.css (theme variables --th-*, .ms-reset-btn, .ms-btn).
 */

const MATERIALS_STORAGE_KEY = 'boxes-materials';
const DEFAULT_MATERIALS = MATERIALS.map(m => Object.assign({}, m));

/** 'en', 'de' or 'fr' to force a language; null = use <html lang>, else English. */
const MATERIAL_EDITOR_LANG = null;

const MATERIAL_EDITOR_TEXTS = {
    en: {
        title: 'Materials and prices',
        name: 'Name',
        price: 'Price',
        unit: '\u20ac/m\u00b2',
        add: '+ Material',
        reset: 'Default',
        resetConfirm: 'Restore the default materials? Your changes in this window are discarded until you save.',
        exportBtn: 'Export',
        importBtn: 'Import',
        importError: 'The file does not contain a valid list of materials.',
        cancel: 'Cancel',
        save: 'Save',
        remove: 'Remove',
        editTitle: 'Edit materials and prices',
        editButton: '\u270e Edit materials and prices',
        invalidRows: 'Please enter a name and a price (number, 0 or more) in row: ',
        storageError: 'Could not save in this browser (storage not available).',
    },
    de: {
        title: 'Materialien und Preise',
        name: 'Name',
        price: 'Preis',
        unit: '\u20ac/m\u00b2',
        add: '+ Material',
        reset: 'Standard',
        resetConfirm: 'Standard-Materialien wiederherstellen? Deine \u00c4nderungen in diesem Fenster gehen verloren, bis du speicherst.',
        exportBtn: 'Export',
        importBtn: 'Import',
        importError: 'Die Datei enth\u00e4lt keine g\u00fcltige Liste von Materialien.',
        cancel: 'Abbrechen',
        save: 'Speichern',
        remove: 'Entfernen',
        editTitle: 'Materialien und Preise bearbeiten',
        editButton: '\u270e Materialien und Preise bearbeiten',
        invalidRows: 'Bitte Name und Preis (Zahl, 0 oder mehr) eintragen in Zeile: ',
        storageError: 'Speichern im Browser nicht m\u00f6glich (Speicher nicht verf\u00fcgbar).',
    },
    fr: {
        title: 'Mat\u00e9riaux et prix',
        name: 'Nom',
        price: 'Prix',
        unit: '\u20ac/m\u00b2',
        add: '+ Mat\u00e9riau',
        reset: 'Par d\u00e9faut',
        resetConfirm: 'R\u00e9tablir les mat\u00e9riaux par d\u00e9faut ? Vos modifications dans cette fen\u00eatre sont perdues tant que vous n\u2019enregistrez pas.',
        exportBtn: 'Exporter',
        importBtn: 'Importer',
        importError: 'Le fichier ne contient pas de liste de mat\u00e9riaux valide.',
        cancel: 'Annuler',
        save: 'Enregistrer',
        remove: 'Supprimer',
        editTitle: 'Modifier les mat\u00e9riaux et les prix',
        editButton: '\u270e Modifier les mat\u00e9riaux et les prix',
        invalidRows: 'Veuillez saisir un nom et un prix (nombre, 0 ou plus) \u00e0 la ligne : ',
        storageError: 'Enregistrement impossible dans ce navigateur (stockage indisponible).',
    },
};

/** Texts in the language of the page. */
function _editorText() {
    const code = String(MATERIAL_EDITOR_LANG || document.documentElement.lang || 'en')
        .slice(0, 2).toLowerCase();
    return MATERIAL_EDITOR_TEXTS[code] || MATERIAL_EDITOR_TEXTS.en;
}

/** Return a cleaned copy of one material or null if it is not usable. */
function _cleanMaterial(m) {
    if (!m || typeof m !== 'object') return null;
    const id = String(m.id === undefined ? '' : m.id).trim();
    const label = String(m.label === undefined ? '' : m.label).trim();
    const price = Number(m.price_per_m2);
    if (!id || !label || !isFinite(price) || price < 0) return null;
    return Object.assign({}, m, {id: id, label: label, price_per_m2: price});
}

/** Clean a list and drop unusable entries and duplicate ids. */
function _cleanMaterialList(raw) {
    const seen = new Set();
    const list = [];
    for (const item of raw) {
        const m = _cleanMaterial(item);
        if (m && !seen.has(m.id)) {
            seen.add(m.id);
            list.push(m);
        }
    }
    return list;
}

/** Saved materials, or the defaults if nothing (valid) is saved. */
function loadMaterials() {
    try {
        const saved = JSON.parse(localStorage.getItem(MATERIALS_STORAGE_KEY) || 'null');
        if (Array.isArray(saved)) return _cleanMaterialList(saved);
    } catch (_) {
    }
    return DEFAULT_MATERIALS.map(m => Object.assign({}, m));
}

/** Replace the content of MATERIALS in place. */
function applyMaterials(list) {
    MATERIALS.splice(0, MATERIALS.length, ...list);
}

function persistMaterials(list) {
    try {
        localStorage.setItem(MATERIALS_STORAGE_KEY, JSON.stringify(list));
        return true;
    } catch (_) {
        return false;
    }
}

// Load the saved list as soon as this file runs (before the panel is built).
applyMaterials(loadMaterials());

/** Rebuild the options of the material select after an edit. */
function refreshMaterialSelect() {
    const sel = document.getElementById('machine-material');
    if (!sel) return;
    const unit = _editorText().unit;
    const before = sel.value;
    sel.innerHTML = '<option value="">Turn off material calculation</option>';
    for (const mat of MATERIALS) {
        const opt = document.createElement('option');
        opt.value = mat.id;
        opt.textContent = `${mat.label} (${mat.price_per_m2}${unit})`;
        sel.appendChild(opt);
    }
    const stillThere = MATERIALS.some(m => m.id === before);
    sel.value = stillThere ? before : '';
    if (before && !stillThere) {
        // The chosen material was removed: let the select's own handler save "off".
        sel.dispatchEvent(new Event('change'));
    } else if (typeof _updatePriceInfo === 'function') {
        _updatePriceInfo();
    }
}

function _slugify(text) {
    const s = String(text).toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '')
        .replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return s || 'material';
}

/** Add base (or base-2, base-3 ...) to used and return the free id. */
function _uniqueMaterialId(base, used) {
    let id = base;
    let n = 2;
    while (used.has(id)) {
        id = base + '-' + n;
        n++;
    }
    used.add(id);
    return id;
}

/*** Look (follows machine.css) *********************************************/

const _ME_INPUT_CSS = 'height:40px;box-sizing:border-box;border:1px solid #bbb;border-radius:8px;' +
    'padding:0 10px;font-size:1em;font-family:inherit;' +
    'background:var(--th-page-bg,Field);color:var(--th-text,FieldText);';
const _ME_ERROR_OUTLINE = '2px solid #c62828';

/** Button in the style of the page: secondary (.ms-reset-btn) or accent (.ms-btn-use). */
function _meButton(id, text, accent) {
    const b = document.createElement('button');
    b.type = 'button';
    if (id) b.id = id;
    b.className = accent ? 'ms-btn ms-btn-use' : 'ms-reset-btn';
    if (accent) b.style.height = '38px';
    b.textContent = text;
    return b;
}

/*** Editor dialog **********************************************************/

function _materialRow(mat) {
    const T = _editorText();
    const tr = document.createElement('tr');
    tr.dataset.id = mat.id || '';
    const tdName = document.createElement('td');
    const name = document.createElement('input');
    name.type = 'text';
    name.className = 'mat-label';
    name.style.cssText = _ME_INPUT_CSS + 'width:100%;';
    name.value = mat.label || '';
    tdName.appendChild(name);
    const tdPrice = document.createElement('td');
    tdPrice.style.whiteSpace = 'nowrap';
    const price = document.createElement('input');
    price.type = 'text';
    price.inputMode = 'decimal';
    price.className = 'mat-price';
    price.style.cssText = _ME_INPUT_CSS + 'width:6em;text-align:right;';
    price.value = (mat.price_per_m2 === undefined) ? '' : String(mat.price_per_m2);
    tdPrice.appendChild(price);
    const unit = document.createElement('span');
    unit.style.cssText = 'margin-left:6px;color:var(--th-text-muted,GrayText);font-size:.9em;';
    unit.textContent = T.unit;
    tdPrice.appendChild(unit);
    const tdDel = document.createElement('td');
    const del = _meButton('', '\u2715', false);
    del.title = T.remove;
    del.style.cssText = 'min-width:40px;height:40px;padding:0;';
    del.addEventListener('click', () => tr.remove());
    tdDel.appendChild(del);
    tr.append(tdName, tdPrice, tdDel);
    return tr;
}

function _fillMaterialRows(list) {
    const body = document.getElementById('material-editor-rows');
    body.innerHTML = '';
    for (const m of list) body.appendChild(_materialRow(m));
}

/** Read the rows. Returns {list} or {error}. Empty rows are ignored. */
function _collectMaterialRows() {
    const T = _editorText();
    const rows = document.querySelectorAll('#material-editor-rows tr');
    const items = [];
    const bad = [];
    rows.forEach((tr, i) => {
        const nameEl = tr.querySelector('.mat-label');
        const priceEl = tr.querySelector('.mat-price');
        const label = nameEl.value.trim();
        const priceText = priceEl.value.trim().replace(',', '.');
        if (!label && !priceText) return;
        const price = Number(priceText);
        const priceOk = priceText !== '' && isFinite(price) && price >= 0;
        nameEl.style.outline = label ? '' : _ME_ERROR_OUTLINE;
        priceEl.style.outline = priceOk ? '' : _ME_ERROR_OUTLINE;
        if (!label || !priceOk) {
            bad.push(i + 1);
            return;
        }
        items.push({id: tr.dataset.id, label: label, price: price});
    });
    if (bad.length) return {error: T.invalidRows + bad.join(', ')};
    const used = new Set(items.map(it => it.id).filter(Boolean));
    const list = items.map(it => {
        const id = it.id || _uniqueMaterialId(_slugify(it.label), used);
        const old = MATERIALS.find(m => m.id === id) || {};  // keep extra fields
        return Object.assign({}, old, {id: id, label: it.label, price_per_m2: it.price});
    });
    return {list: list};
}

function closeMaterialEditor() {
    const el = document.getElementById('material-editor');
    if (el) el.remove();
}

function openMaterialEditor() {
    const T = _editorText();
    closeMaterialEditor();

    const overlay = document.createElement('div');
    overlay.id = 'material-editor';
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:10000;' +
        'display:flex;align-items:center;justify-content:center;padding:12px;box-sizing:border-box;';
    overlay.addEventListener('click', e => {
        if (e.target === overlay) closeMaterialEditor();
    });

    const box = document.createElement('div');
    box.style.cssText = 'background:var(--th-container-bg,Canvas);color:var(--th-text,CanvasText);' +
        'border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.35);padding:18px 20px;' +
        'width:100%;max-width:36em;max-height:88vh;overflow:auto;box-sizing:border-box;' +
        'font-family:inherit;';
    overlay.appendChild(box);

    const title = document.createElement('div');
    title.textContent = T.title;
    title.style.cssText = 'font-weight:bold;margin:0 0 14px;';
    box.appendChild(title);

    const table = document.createElement('table');
    table.className = 'ms-mat-table';
    table.innerHTML = '<thead><tr><th></th><th></th><th></th></tr></thead>' +
        '<tbody id="material-editor-rows"></tbody>';
    const heads = table.querySelectorAll('th');
    heads[0].textContent = T.name;
    heads[1].textContent = T.price;
    for (const th of heads) {
        th.style.cssText = 'text-align:left;font-weight:normal;font-size:.85em;' +
            'color:var(--th-text-muted,GrayText);padding:0 10px 4px;';
    }
    box.appendChild(table);

    const addBtn = _meButton('mat-add', T.add, false);
    addBtn.style.marginTop = '12px';
    box.appendChild(addBtn);

    const msg = document.createElement('div');
    msg.id = 'material-editor-msg';
    msg.style.cssText = 'color:#c62828;min-height:1.3em;margin:10px 0 4px;font-size:.9em;';
    box.appendChild(msg);

    const footer = document.createElement('div');
    footer.style.cssText = 'display:flex;gap:10px;flex-wrap:wrap;justify-content:space-between;' +
        'margin-top:6px;';
    const left = document.createElement('span');
    left.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;';
    left.append(_meButton('mat-reset', T.reset, false),
        _meButton('mat-export', T.exportBtn, false),
        _meButton('mat-import', T.importBtn, false));
    const right = document.createElement('span');
    right.style.cssText = 'display:flex;gap:8px;flex-wrap:wrap;';
    right.append(_meButton('mat-cancel', T.cancel, false), _meButton('mat-save', T.save, true));
    footer.append(left, right);
    box.appendChild(footer);

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.id = 'mat-file';
    fileInput.accept = 'application/json,.json';
    fileInput.style.display = 'none';
    box.appendChild(fileInput);

    document.body.appendChild(overlay);
    _fillMaterialRows(MATERIALS);

    addBtn.addEventListener('click', () => {
        const row = _materialRow({});
        document.getElementById('material-editor-rows').appendChild(row);
        row.querySelector('.mat-label').focus();
    });

    box.querySelector('#mat-reset').addEventListener('click', () => {
        if (confirm(T.resetConfirm)) {
            _fillMaterialRows(DEFAULT_MATERIALS);
            msg.textContent = '';
        }
    });

    box.querySelector('#mat-export').addEventListener('click', () => {
        const res = _collectMaterialRows();
        if (res.error) {
            msg.textContent = res.error;
            return;
        }
        msg.textContent = '';
        const blob = new Blob([JSON.stringify(res.list, null, 2)], {type: 'application/json'});
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'boxes-materials.json';
        a.click();
        URL.revokeObjectURL(a.href);
    });

    box.querySelector('#mat-import').addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', () => {
        const file = fileInput.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = e => {
            try {
                const data = JSON.parse(e.target.result);
                if (!Array.isArray(data)) throw new Error('not a list');
                const list = _cleanMaterialList(data);
                if (!list.length && data.length) throw new Error('nothing usable');
                _fillMaterialRows(list);
                msg.textContent = '';
            } catch (_) {
                msg.textContent = T.importError;
            }
        };
        reader.readAsText(file);
        fileInput.value = '';
    });

    box.querySelector('#mat-cancel').addEventListener('click', closeMaterialEditor);

    box.querySelector('#mat-save').addEventListener('click', () => {
        const res = _collectMaterialRows();
        if (res.error) {
            msg.textContent = res.error;
            return;
        }
        if (!persistMaterials(res.list)) {
            msg.textContent = T.storageError;
            return;
        }
        applyMaterials(res.list);
        refreshMaterialSelect();
        closeMaterialEditor();
        // The touch machine page builds its radio list on load: reload to show the new list.
        if (document.getElementById('machine-material-radios')) location.reload();
    });

    const first = box.querySelector('.mat-label');
    if (first) first.focus();
}

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeMaterialEditor();
});

/** Put the edit button below the visible material list (touch machine page) or,
 *  if there is none, next to the material select. */
function initMaterialEditorButton() {
    if (document.getElementById('machine-material-edit')) return;
    const radios = document.getElementById('machine-material-radios');
    const sel = document.getElementById('machine-material');
    const anchor = radios || sel;
    if (!anchor) return;
    const T = _editorText();
    const btn = _meButton('machine-material-edit', radios ? T.editButton : '\u270e', false);
    btn.title = T.editTitle;
    btn.style.cssText = radios ? 'margin-top:12px;' : 'margin-left:6px;';
    btn.addEventListener('click', openMaterialEditor);
    anchor.insertAdjacentElement('afterend', btn);
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMaterialEditorButton);
} else {
    initMaterialEditorButton();
}
window.addEventListener('load', initMaterialEditorButton);  // in case the panel is built later
