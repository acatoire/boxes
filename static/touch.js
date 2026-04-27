/* ================================================================
   Boxes.py – Touch / Tablet UI  (touch.js)
   ================================================================ */

const UI_MODE_KEY   = 'boxes-ui-mode';
const TH_GROUP_KEY  = 'th-active-group';

/* ── Mode preference (localStorage) ─────────────────────────────── */

function getUIModePreference() {
    try { return localStorage.getItem(UI_MODE_KEY); } catch(_) { return null; }
}
function setUIModePreference(mode) {
    try { localStorage.setItem(UI_MODE_KEY, mode); } catch(_) {}
}

/** Switch to classic (legacy) mode: save pref and go to Menu. */
function thSwitchToLegacy() {
    setUIModePreference('legacy');
    window.location.href = 'Menu';
}

/** Switch to touch mode from any classic page. */
function thSwitchToTouch() {
    setUIModePreference('touch');
    window.location.href = 'TouchHub';
}

/* ── Category tab switching ──────────────────────────────────────── */

function thSwitchTab(groupId) {
    groupId = String(groupId);

    document.querySelectorAll('.th-tab').forEach(t => {
        const isActive = t.dataset.group === groupId;
        t.classList.toggle('active', isActive);
        t.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    document.querySelectorAll('.th-panel').forEach(p => {
        const isActive = p.dataset.group === groupId;
        p.classList.toggle('active', isActive);
        p.style.display = isActive ? 'block' : 'none';
    });

    try { localStorage.setItem(TH_GROUP_KEY, groupId); } catch(_) {}

    // Re-apply current search filter to newly visible panel
    const q = (document.getElementById('th-search') || {}).value || '';
    thApplySearch(q.trim().toLowerCase());

    // Scroll tab into view (horizontal tab bar)
    const activeTab = document.querySelector('.th-tab.active');
    if (activeTab) activeTab.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
}

/* ── Search / filter ─────────────────────────────────────────────── */

function thFilterSearch() {
    const q = (document.getElementById('th-search').value || '').trim().toLowerCase();
    thApplySearch(q);
}

function thApplySearch(q) {
    const activePanel = document.querySelector('.th-panel.active');
    if (!activePanel) return;

    let visible = 0;
    activePanel.querySelectorAll('.th-card').forEach(card => {
        const text = (card.textContent || '').toLowerCase();
        const show = !q || text.includes(q);
        card.style.display = show ? '' : 'none';
        if (show) visible++;
    });

    // Show / hide no-results placeholder
    let noRes = activePanel.querySelector('.th-no-results');
    if (q && visible === 0) {
        if (!noRes) {
            noRes = document.createElement('p');
            noRes.className = 'th-no-results';
            activePanel.appendChild(noRes);
        }
        noRes.textContent = 'No results for "' + q + '"';
    } else if (noRes) {
        noRes.remove();
    }
}

/* ── Category visibility (shared with self.js HIDDEN_CATS_KEY) ──── */

/**
 * Hide tabs and panels for categories the user has disabled.
 * Falls back gracefully if loadHiddenCategories (self.js) is unavailable.
 */
function applyHiddenCategoriesTouch() {
    const hidden = (typeof loadHiddenCategories === 'function')
        ? loadHiddenCategories()
        : new Set();

    document.querySelectorAll('.th-tab[data-group]').forEach(function(tab) {
        tab.style.display = hidden.has(tab.dataset.group) ? 'none' : '';
    });
    document.querySelectorAll('.th-panel[data-group]').forEach(function(panel) {
        if (hidden.has(panel.dataset.group)) {
            panel.style.display = 'none';
            panel.classList.remove('active');
        }
    });

    // If the currently-active tab is now hidden, jump to first visible one.
    const activeTab = document.querySelector('.th-tab.active');
    if (!activeTab || activeTab.style.display === 'none') {
        const first = document.querySelector('.th-tab[data-group]:not([style*="none"])');
        if (first) thSwitchTab(first.dataset.group);
    }
}

/* ── Hub init ────────────────────────────────────────────────────── */

function initTouchHub() {
    // Record that we're in touch mode.
    setUIModePreference('touch');

    // Restore last active group.
    let lastGroup = null;
    try { lastGroup = localStorage.getItem(TH_GROUP_KEY); } catch(_) {}
    if (lastGroup !== null && document.querySelector(`.th-tab[data-group="${lastGroup}"]`)) {
        thSwitchTab(lastGroup);
    }

    applyHiddenCategoriesTouch();
}

/* ── Touch args page init ────────────────────────────────────────── */

/**
 * Called from the touch args page onload.
 * numHide mirrors the same argument as initArgsPage().
 */
function initTouchArgs(numHide) {
    // Reuse the existing initArgsPage from self.js
    if (typeof initArgsPage === 'function') initArgsPage(numHide);

    // Wire up the sticky action bar buttons
    _bindTouchActionBar();

    // Auto-size inputs/selects if field-sizing:content is unsupported (Firefox < 128)
    if (!CSS.supports('field-sizing', 'content')) {
        _autoSizeAllFields();
    }
}

/* ── field-sizing fallback (Firefox / Safari) ────────────────────── */

const _sizeCanvas = document.createElement('canvas');

function _measureText(el, text) {
    const ctx = _sizeCanvas.getContext('2d');
    const cs  = getComputedStyle(el);
    ctx.font  = cs.fontSize + ' ' + cs.fontFamily;
    return ctx.measureText(text).width;
}

function _autoSizeField(el) {
    const MIN = 70;
    const PAD = el.tagName === 'SELECT' ? 44 : 24; // selects need extra room for native arrow
    let text = '';
    if (el.tagName === 'SELECT') {
        text = el.options[el.selectedIndex] ? el.options[el.selectedIndex].text : '';
    } else {
        text = el.value || el.placeholder || '';
    }
    const w = Math.max(MIN, Math.ceil(_measureText(el, text)) + PAD);
    el.style.width = w + 'px';
}

function _autoSizeAllFields() {
    const sel = 'body.touch-args table input[type="text"], body.touch-args table select';
    document.querySelectorAll(sel).forEach(el => {
        _autoSizeField(el);
        el.addEventListener('change', () => _autoSizeField(el));
        el.addEventListener('input',  () => _autoSizeField(el));
    });
}

function _bindTouchActionBar() {
    // Buttons in .touch-action-bar have data-render attribute
    document.querySelectorAll('.touch-action-btn[data-render]').forEach(btn => {
        btn.addEventListener('click', function() {
            const renderVal = this.dataset.render;
            const target    = this.dataset.target || '_blank';
            const form = document.querySelector('#arguments');
            if (!form) return;

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

/* Legacy-page "Touch mode" button injection removed.
   This script is not initialised on classic pages, so keeping an unused
   helper here only leaves a dead feature path behind. */
