/* ================================================================
   Boxes.py – Shop mode (shop.js)
   Loaded on every touch-mode page. Lets a shop be selected via the
   `?shop=<id>` URL parameter (persisted in localStorage), which then:
     - applies the shop's theme, machine config and color config
       (from static/shops/<id>.json) on top of the user's own settings
     - hides menu entries not relevant to a shop visitor
       (any element carrying [data-hide-on-shop])
     - lets touch.js switch the generator hub into a flat, unfiltered
       grid restricted to that shop's generators (see touch.js
       applyShopFilterTouch()).

   Shop selection precedence (highest first):
     1. `?shop=<id>` URL parameter (persisted once applied; `?shop=`
        with an empty value explicitly clears the active shop)
     2. Saved preference in localStorage (`boxes-shop`)
     3. No shop active (full generic UI)
   ================================================================ */

var SHOP_STORAGE_KEY = 'boxes-shop';
var SHOP_STATIC_BASE = (window.BOXES_STATIC_URL || 'static') + '/shops';

var _shopIndexPromise = null;

/** Return the `shop` value from the current URL's query string, or null if absent. */
function shopIdFromURL() {
    try {
        var params = new URLSearchParams(window.location.search);
        if (!params.has('shop')) return null;
        return params.get('shop') || '';
    } catch (_) {
        return null;
    }
}

/** Persist the active shop id ('' / null clears it). */
function saveShopId(id) {
    try {
        if (id) {
            localStorage.setItem(SHOP_STORAGE_KEY, id);
        } else {
            localStorage.removeItem(SHOP_STORAGE_KEY);
        }
    } catch (_) { /* ignore */ }
}

/** Return the saved shop id, or null if none saved. */
function loadShopId() {
    try {
        return localStorage.getItem(SHOP_STORAGE_KEY);
    } catch (_) {
        return null;
    }
}

/** Resolve the currently active shop id (or null when no shop is active). */
function getActiveShopId() {
    var urlShop = shopIdFromURL();
    if (urlShop !== null) return urlShop || null;
    return loadShopId() || null;
}

/** Fetch (and memoize) static/shops/index.json – the list of known shops. */
function loadShopIndex() {
    if (_shopIndexPromise) return _shopIndexPromise;
    _shopIndexPromise = fetch(SHOP_STATIC_BASE + '/index.json')
        .then(function (r) { return r.json(); })
        .catch(function () { return []; });
    return _shopIndexPromise;
}

/** Fetch a single shop's config JSON (theme + machine + colors). */
function loadShopConfig(id) {
    return fetch(SHOP_STATIC_BASE + '/' + encodeURIComponent(id) + '.json')
        .then(function (r) { return r.json(); })
        .catch(function () { return null; });
}

/** Apply a shop's theme/machine/colors config on top of current settings. */
function applyShopConfig(cfg) {
    if (!cfg) return;
    if (cfg.theme && typeof applyThemeByName === 'function') {
        applyThemeByName(cfg.theme, true);
    }
    if (cfg.machine) {
        try {
            var current = (typeof loadMachineConfig === 'function') ? loadMachineConfig() : {};
            var merged = Object.assign({}, current, cfg.machine);
            localStorage.setItem('boxes-machine-config', JSON.stringify(merged));
        } catch (_) { /* ignore */ }
    }
    if (cfg.colors) {
        try {
            var current2 = JSON.parse(localStorage.getItem('boxes-color-settings') || '{}');
            var merged2 = Object.assign({}, current2, cfg.colors);
            localStorage.setItem('boxes-color-settings', JSON.stringify(merged2));
        } catch (_) { /* ignore */ }
    }
}

/** Populate every `<select>` used as a shop picker (id starts with "shop-select"). */
function populateShopSelects() {
    var selects = document.querySelectorAll('select[id^="shop-select"]');
    if (!selects.length) return;
    loadShopIndex().then(function (shops) {
        var current = getActiveShopId() || '';
        var optHtml = '<option value="">\u2014 ' + 'No shop' + ' \u2014</option>';
        (shops || []).forEach(function (s) {
            var sel = s.id === current ? ' selected' : '';
            optHtml += '<option value="' + s.id + '"' + sel + '>' + (s.label || s.id) + '</option>';
        });
        selects.forEach(function (sel) { sel.innerHTML = optHtml; });
    });
}

/** onchange handler for a shop `<select>`: persist + navigate to the hub. */
function onShopChange(selectEl) {
    var id = selectEl.value;
    saveShopId(id || null);
    var params = new URLSearchParams(window.location.search);
    if (id) {
        params.set('shop', id);
    } else {
        params.delete('shop');
    }
    var qs = params.toString();
    window.location.href = 'TouchHub' + (qs ? '?' + qs : '');
}

/** Hide/show every element flagged [data-hide-on-shop] based on shop state. */
function applyShopMenuVisibility() {
    var active = getActiveShopId();
    document.querySelectorAll('[data-hide-on-shop]').forEach(function (el) {
        el.style.display = active ? 'none' : '';
    });
    if (document.body) document.body.classList.toggle('shop-active', !!active);
    return active;
}

/** Called on every touch page's DOMContentLoaded. */
function initShopSystem() {
    var active = applyShopMenuVisibility();
    populateShopSelects();
    if (active) {
        loadShopConfig(active).then(applyShopConfig);
    }
}

document.addEventListener('DOMContentLoaded', initShopSystem);

