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

/* ── Hub init ────────────────────────────────────────────────────── */

function initTouchHub() {
    const pref = getUIModePreference();

    // Only auto-redirect to legacy when the server is in 'auto' mode AND the
    // user has explicitly chosen legacy (e.g. after clicking "Classic view").
    // If the user just clicked the "Touch mode" button the onclick already
    // wrote 'touch' into localStorage, so this branch won't trigger.
    // We also skip the redirect if the URL contains a forced 'touch' param.
    const params = new URLSearchParams(window.location.search);
    const forcedTouch = params.get('ui') === 'touch';
    if (pref === 'legacy' && !forcedTouch) {
        window.location.replace('Menu');
        return;
    }

    // Record that we're (back) in touch mode.
    setUIModePreference('touch');

    // Restore last active group.
    let lastGroup = null;
    try { lastGroup = localStorage.getItem(TH_GROUP_KEY); } catch(_) {}
    if (lastGroup !== null && document.querySelector(`.th-tab[data-group="${lastGroup}"]`)) {
        thSwitchTab(lastGroup);
    }
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

/* ── Classic mode: inject "Touch mode" button into linkbar ──────── */

/**
 * Called on any legacy page if the server was started with --ui-mode auto.
 * Injects a "Touch mode" button in the linkbar so the user can switch.
 */
function injectTouchModeButton() {
    const pref = getUIModePreference();
    if (pref === 'touch') {
        // Redirect to hub immediately if the user previously chose touch
        window.location.replace('TouchHub');
        return;
    }
    // Inject a button in the linkbar
    const ul = document.querySelector('.linkbar ul');
    if (!ul) return;
    const li = document.createElement('li');
    li.className = 'right';
    const btn = document.createElement('button');
    btn.textContent = '⬛ Touch mode';
    btn.title = 'Switch to tablet-optimised interface';
    btn.style.cssText = 'font-size:0.85em;padding:2px 10px;cursor:pointer;border:1px solid #999;border-radius:4px;background:#EFE8DA;';
    btn.addEventListener('click', thSwitchToTouch);
    li.appendChild(btn);
    ul.appendChild(li);
}
