/* ================================================================
   Boxes.py – Generator configuration page  (generator.js)
   ================================================================ */

/* Touch args page init */

/**
 * Called from the generator page onload.
 * numHide mirrors the same argument as initArgsPage().
 */
function initTouchArgs(numHide) {
    // Reuse the existing initArgsPage from self.js
    if (typeof initArgsPage === 'function') initArgsPage(numHide);

    // Wrap the global refreshPreview so bulk template loading can suppress it.
    _wrapRefreshPreview();

    // Wire preview_img load/error to remove the loading spinner.
    const img = document.getElementById('preview_img');
    if (img) {
        img.addEventListener('load',  _hidePreviewLoading);
        img.addEventListener('error', _hidePreviewLoading);
        img.addEventListener('load',  () => { if (previewFillEnabled) _loadInlinePreviewFill(img.src); });
        img.addEventListener('load',  _syncSlideMeIcon);
        img.addEventListener('load',  _updateAutoLabel);
    }

    // "Show fill" checkbox next to the zoom controls starts checked (default true).
    const fillToggle = document.getElementById('preview-fill-toggle');
    if (fillToggle) previewFillEnabled = fillToggle.checked;

    // Wire up the sticky action bar buttons
    _bindTouchActionBar();

    // Machine config panel (localStorage-backed)
    if (typeof initMachineConfigPanel === 'function') initMachineConfigPanel();

    // Auto-size inputs/selects if field-sizing:content is unsupported (Firefox < 128)
    if (!CSS.supports('field-sizing', 'content')) {
        _autoSizeAllFields();
    }
}

/* ----------------------------------------------------------------
   Preview "show fill" toggle
   ----------------------------------------------------------------
   The cut file itself is line-art only (no <path fill>, by design --
   laser software decides per color-layer whether to fill). This toggle
   is a preview-only aid: on the client we fetch the same preview svg as
   text, inline it into the page (an <img> can't have its inner <path>
   elements restyled), and set fill=stroke on paths whose stroke color
   matches the SOLID_FILL role so the on-screen preview looks filled.
   The downloaded/generated file is never touched. Defaults to on. */

let previewFillEnabled = true;

/* ----------------------------------------------------------------
   "Slide me" drag-out icon (sticky action bar, between Generate and
   Download)
   ----------------------------------------------------------------
   Only a real <img src="..."> is natively draggable out of the browser
   (onto a laser app / the desktop) in every browser -- when "Show fill" is
   on, the visible preview is an inline <svg> injected as markup (see the
   toggle above), which most browsers won't let you drag out as a file.
   This icon is always a plain <img> pointed at the same preview url, kept
   in sync on every preview reload, so dragging works regardless of the
   Show fill toggle. */

function _syncSlideMeIcon() {
    const img = document.getElementById('preview_img');
    const slideMe = document.getElementById('slide-me-icon');
    const wrap = document.getElementById('slide-me-wrap');
    if (!img || !slideMe || !wrap) return;
    slideMe.src = img.src;
    // The stylesheet default is display:none -- '' would just clear the
    // inline style and fall back to that, so an explicit visible value is
    // needed here, not ''. Toggle the wrapper (not the <img> itself) so the
    // "Grab me" label shown/hidden with it stays in sync.
    wrap.style.display = img.src.endsWith('/nothing.png') ? 'none' : 'inline-flex';
}

/* ----------------------------------------------------------------
   Live "auto label" (MiniatureWorkshop's Text_text field)
   ----------------------------------------------------------------
   While the Auto_label checkbox is on (default), the server always uses
   the auto-generated caption regardless of what's in the box (see
   MiniatureWorkshop._default_label()/render() in Python) -- this mirrors
   that same computation into the field's real value (not just a
   placeholder) after every preview recalculation, so the box always shows
   real, editable text instead of starting empty, and stays in sync as the
   character/pet selection changes. Once Auto_label is unchecked, this
   stops touching the field so manual edits are never overwritten.
   No-op on generators that don't have these fields. */

function _displayResourceName(stem) {
    if (!stem) return '';
    return stem.replace(/[-_]/g, ' ').replace(/\S+/g, w => w[0].toUpperCase() + w.slice(1).toLowerCase());
}

function _updateAutoLabel() {
    const textField = document.getElementById('Text_text');
    const autoCheckbox = document.getElementById('Auto_label');
    if (!textField || (autoCheckbox && !autoCheckbox.checked)) return;
    const selValue = (id) => {
        const el = document.getElementById(id);
        return (el && el.value && el.value !== 'none') ? el.value : '';
    };
    const characterName = _displayResourceName(selValue('Character_resource'));
    const petNames = ['Pet_resource', 'Pet2_resource']
        .map(selValue)
        .filter(Boolean)
        .map(_displayResourceName);
    let label = '';
    if (characterName && petNames.length) label = `${characterName} with ${petNames.join(' and ')}`;
    else if (characterName) label = characterName;
    else if (petNames.length) label = petNames.join(' and ');
    textField.value = label;
}

/** Keep both the <img> and the inline-svg preview at the same zoom level. */
function setPreviewZoom(scale) {
    const img = document.getElementById('preview_img');
    const inline = document.getElementById('preview_svg_inline');
    if (img) img.style.width = scale + '%';
    if (inline) inline.style.width = scale + '%';
}

function onPreviewFillToggleChange() {
    const cb = document.getElementById('preview-fill-toggle');
    previewFillEnabled = cb ? cb.checked : true;
    const img = document.getElementById('preview_img');
    const inline = document.getElementById('preview_svg_inline');
    if (!img || !inline) return;
    if (previewFillEnabled) {
        _loadInlinePreviewFill(img.src);
    } else {
        inline.style.display = 'none';
        inline.innerHTML = '';
        img.style.display = '';
    }
}

function _hexToRgbString(hex) {
    hex = hex.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgb(${r},${g},${b})`;
}

/** Fill in every path whose stroke matches the current SOLID_FILL color. */
function _applySolidFillPreview(svgEl) {
    const overrides = (typeof loadColorSettings === 'function') ? loadColorSettings() : {};
    const hex = overrides['SOLID_FILL'] ||
        (typeof DEFAULT_ROLE_COLORS !== 'undefined' ? DEFAULT_ROLE_COLORS['SOLID_FILL'] : null);
    if (!hex) return;
    const targets = new Set([hex.toLowerCase(), _hexToRgbString(hex)]);
    svgEl.querySelectorAll('path[stroke]').forEach(p => {
        const stroke = p.getAttribute('stroke');
        if (stroke && targets.has(stroke.toLowerCase())) {
            p.setAttribute('fill', stroke);
        }
    });
}

/** Fetch the preview svg as text and inline it so its paths can be restyled. */
function _loadInlinePreviewFill(url) {
    if (!url || !previewFillEnabled) return;
    fetch(url)
        .then(r => r.text())
        .then(text => {
            if (!previewFillEnabled) return; // toggled off while the fetch was in flight
            const img = document.getElementById('preview_img');
            const inline = document.getElementById('preview_svg_inline');
            if (!img || !inline) return;
            inline.innerHTML = text;
            const svgEl = inline.querySelector('svg');
            if (!svgEl) return;
            svgEl.removeAttribute('width');
            svgEl.removeAttribute('height');
            svgEl.style.width = '100%';
            svgEl.style.height = 'auto';
            svgEl.style.display = 'block';
            _applySolidFillPreview(svgEl);
            inline.style.width = img.style.width || '100%';
            inline.style.display = '';
            img.style.display = 'none';
        })
        .catch(() => {}); // e.g. the initial nothing.png placeholder isn't an svg -- ignore
}

/* ----------------------------------------------------------------
   Preview loading state
   ---------------------------------------------------------------- */

/** Wrap the global refreshPreview once so a suppress flag can mute it. */
function _wrapRefreshPreview() {
    if (window._refreshPreviewWrapped) return;
    const orig = window.refreshPreview;
    if (typeof orig !== 'function') return;
    window.refreshPreview = function () {
        if (window._suppressPreview) return;
        _showPreviewLoading();
        orig.call(this);
    };
    window._refreshPreviewWrapped = true;
}

/** Add the loading spinner overlay to the preview area. */
function _showPreviewLoading() {
    const preview = document.getElementById('preview');
    if (preview) preview.classList.add('is-loading');
}

/** Remove the loading spinner (called on img load or error). */
function _hidePreviewLoading() {
    const preview = document.getElementById('preview');
    if (preview) preview.classList.remove('is-loading');
}

/* Generator params JSON export / import */

function saveParamsAsJson() {
    const form = document.querySelector('#arguments');
    if (!form) return;
    const data = {};
    new FormData(form).forEach((value, key) => {
        if (key !== 'render' && key !== 'language') data[key] = value;
    });
    // Also capture unchecked checkboxes (FormData omits them)
    form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        if (!cb.checked) data[cb.name] = 'false';
    });
    const name = (window.location.pathname.split('/').pop() || 'generator').replace(/\W/g, '_');
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = name + '-params.json';
    a.click();
    URL.revokeObjectURL(a.href);
}

function loadParamsFromJson(input) {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            // Show spinner immediately, suppress per-field refreshes,
            // then fire a single refresh once all fields are set.
            _showPreviewLoading();
            window._suppressPreview = true;
            _applyParamsData(data);
            window._suppressPreview = false;
            if (typeof refreshPreview === 'function') refreshPreview();
        } catch (_) {
            alert('Invalid JSON file.');
        }
    };
    reader.readAsText(file);
    input.value = '';
}

/** Apply a plain {key: value} object to the #arguments form. */
function _applyParamsData(data) {
    const form = document.querySelector('#arguments');
    if (!form) return;
    for (const [key, value] of Object.entries(data)) {
        // BoolArg renders a hidden input + checkbox with the same name.
        // querySelector returns the hidden input first, so we must look for
        // the checkbox explicitly and prefer it when it exists.
        const cbEl = form.querySelector(`input[type="checkbox"][name="${CSS.escape(key)}"]`);
        const el   = cbEl || form.querySelector(`[name="${CSS.escape(key)}"]`);
        if (!el) continue;
        if (el.type === 'checkbox') {
            el.checked = (value === true || value === 'true' || value === '1' || value === 'on');
        } else {
            el.value = value;
        }
        el.dispatchEvent(new Event('change'));
    }
}

/**
 * Load a template preset by index from the server-inlined GENERATOR_TEMPLATES array.
 * Suppresses per-field refreshPreview calls, shows the spinner, then fires one refresh.
 */
function applyTemplatePreset(idx) {
    if (idx === '' || idx === null || idx === undefined) return;
    const tpl = (typeof GENERATOR_TEMPLATES !== 'undefined') && GENERATOR_TEMPLATES[parseInt(idx, 10)];
    if (!tpl) return;

    // Show spinner immediately
    _showPreviewLoading();

    // Suppress the per-field change→refreshPreview calls during bulk apply
    window._suppressPreview = true;
    _applyParamsData(tpl.data);
    window._suppressPreview = false;

    // Single refresh now that all fields are set
    if (typeof refreshPreview === 'function') refreshPreview();
}

function _bindTouchActionBar() {
    // Buttons in .touch-action-bar have data-render attribute
    document.querySelectorAll('.touch-action-btn[data-render]').forEach(btn => {
        btn.addEventListener('click', function() {
            const renderVal = this.dataset.render;
            const target    = this.dataset.target || '_blank';
            const form = document.querySelector('#arguments');
            if (!form) return;

            // URL button (render=0, _self): build URL client-side and append
            // #configuration so the hash is preserved across the page reload.
            if (renderVal === '0' && target === '_self') {
                if (typeof injectColorHiddenFields === 'function') injectColorHiddenFields(form);
                const params = new URLSearchParams(new FormData(form));
                params.set('render', '0');
                window.location.href = form.action + '?' + params.toString() + '#configuration';
                return;
            }

            // Temporarily set render + formtarget on a hidden input and submit
            let ri = form.querySelector('input[name="render"][data-touch]');
            if (!ri) {
                ri = document.createElement('input');
                ri.type = 'hidden';
                ri.name = 'render';
                ri.setAttribute('data-touch', '1');
                form.appendChild(ri);
            }
            ri.value = renderVal;
            const prevTarget = form.target;
            form.target = target;

            // Inject color overrides (from self.js)
            if (typeof injectColorHiddenFields === 'function') injectColorHiddenFields(form);

            form.submit();
            form.target = prevTarget;
        });
    });
}
