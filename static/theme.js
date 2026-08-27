/* ================================================================
   Boxes.py – Theme switcher (theme.js)
   Loaded on every touch-mode page (hub, colors, categories, machine,
   generator/touch-args). Reads presets from static/themes.json and
   applies them as CSS custom properties on <html>, so touch.css /
   colors.css / categories.css / machine.css / generator.css and the
   shared self.css widgets all repaint instantly.

   Theme selection precedence (highest first):
     1. `?theme=<name>` URL parameter (persisted once applied)
     2. Saved preference in localStorage (`boxes-theme`)
     3. Default theme ("boxes")

   A small synchronous "cache" of the last-applied theme's CSS vars is
   also kept in localStorage (`boxes-theme-cache`) so an inline snippet
   emitted in <head> (see genHTMLThemeInit() in home_touch.py) can
   re-apply it *before* the stylesheets paint, avoiding a flash of the
   wrong theme while themes.json is being fetched.
   ================================================================ */

var THEME_STORAGE_KEY = 'boxes-theme';
var THEME_CACHE_KEY = 'boxes-theme-cache';
var THEME_DEFAULT = 'boxes';
var THEME_JSON_URL = (window.BOXES_STATIC_URL || 'static') + '/themes.json';

var _themesData = null;      /* populated once fetched */
var _themesPromise = null;

/** Read the raw cache blob (name + resolved theme object) from localStorage. */
function _readThemeCache() {
    try {
        return JSON.parse(localStorage.getItem(THEME_CACHE_KEY) || 'null');
    } catch (_) {
        return null;
    }
}

/** Persist the resolved theme (name + object) so it can be re-applied instantly next visit. */
function _writeThemeCache(name, theme) {
    try {
        localStorage.setItem(THEME_CACHE_KEY, JSON.stringify({ name: name, theme: theme }));
    } catch (_) { /* ignore quota / privacy-mode errors */ }
}

/** Persist just the chosen theme name (the user's explicit preference). */
function saveThemeName(name) {
    try {
        localStorage.setItem(THEME_STORAGE_KEY, name);
    } catch (_) { /* ignore */ }
}

/** Return the saved theme name, or null if none saved yet. */
function loadThemeName() {
    try {
        return localStorage.getItem(THEME_STORAGE_KEY);
    } catch (_) {
        return null;
    }
}

/** Return the `theme` value from the current URL's query string, or null. */
function themeNameFromURL() {
    try {
        var params = new URLSearchParams(window.location.search);
        return params.get('theme');
    } catch (_) {
        return null;
    }
}

/** Apply a resolved theme object's CSS vars + dark/glitter body classes. */
function applyThemeVars(theme) {
    if (!theme || !theme.vars) return;
    var root = document.documentElement;
    Object.keys(theme.vars).forEach(function (k) {
        root.style.setProperty(k, theme.vars[k]);
    });
    if (document.body) {
        document.body.classList.toggle('theme-dark', !!theme.dark);
        document.body.classList.toggle('theme-glitter', !!theme.glitter);
    }
    applyThemeBranding(theme);
}

/** Swap the header logo image + text to match the active theme, if present. */
function applyThemeBranding(theme) {
    if (!document.body) return;
    var staticUrl = window.BOXES_STATIC_URL || 'static';
    var logoImg = document.getElementById('th-logo-img');
    if (logoImg && theme.logo) {
        var newSrc = staticUrl + '/' + theme.logo;
        if (logoImg.getAttribute('src') !== newSrc) logoImg.setAttribute('src', newSrc);
    }
    if (theme.logoText) {
        document.querySelectorAll('.th-logo-text').forEach(function (el) {
            el.textContent = theme.logoText;
        });
    }
}

/** Called synchronously (inline, before CSS paints) to avoid a theme flash. */
function applyCachedThemeInstantly() {
    var cached = _readThemeCache();
    if (cached && cached.theme) applyThemeVars(cached.theme);
}

/** Fetch (and memoize) static/themes.json. Returns a Promise<object>. */
function loadThemesData() {
    if (_themesData) return Promise.resolve(_themesData);
    if (_themesPromise) return _themesPromise;
    _themesPromise = fetch(THEME_JSON_URL)
        .then(function (r) { return r.json(); })
        .then(function (data) {
            _themesData = data;
            return data;
        })
        .catch(function () {
            _themesData = {};
            return _themesData;
        });
    return _themesPromise;
}

/** Resolve + apply a theme by name, persist it, and update the URL param cache. */
function applyThemeByName(name, persist) {
    return loadThemesData().then(function (themes) {
        var theme = themes[name] || themes[THEME_DEFAULT];
        var resolvedName = themes[name] ? name : THEME_DEFAULT;
        applyThemeVars(theme);
        _writeThemeCache(resolvedName, theme);
        if (persist !== false) saveThemeName(resolvedName);
        return resolvedName;
    });
}

/** Return the currently active theme name (best known value without a fetch). */
function getCurrentThemeName() {
    var cached = _readThemeCache();
    if (cached && cached.name) return cached.name;
    return loadThemeName() || THEME_DEFAULT;
}

/** Populate a <select> element with <option> entries for every known theme. */
function populateThemeSelect(selectEl) {
    if (!selectEl) return;
    loadThemesData().then(function (themes) {
        var current = getCurrentThemeName();
        var html = Object.keys(themes).map(function (key) {
            var t = themes[key];
            var sel = key === current ? ' selected' : '';
            return '<option value="' + key + '"' + sel + '>' + (t.label || key) + '</option>';
        }).join('');
        selectEl.innerHTML = html;
    });
}

/** onchange handler for the theme <select> on the Colors page. */
function onThemeChange(selectEl) {
    var name = selectEl.value;
    applyThemeByName(name, true).then(function () {
        _flashThemeStatus();
        _updateThemeURLParam(name);
    });
}

function _flashThemeStatus() {
    var status = document.getElementById('theme-settings-status');
    if (status) {
        status.style.display = 'inline';
        clearTimeout(status._hideTimer);
        status._hideTimer = setTimeout(function () {
            status.style.display = 'none';
        }, 1500);
    }
}

/** Keep the URL's ?theme= param in sync (without reloading), so the page is shareable. */
function _updateThemeURLParam(name) {
    try {
        var url = new URL(window.location.href);
        url.searchParams.set('theme', name);
        window.history.replaceState(null, '', url.toString());
    } catch (_) { /* ignore */ }
}

/** Reset to the default "boxes" theme. */
function resetThemeSettings() {
    applyThemeByName(THEME_DEFAULT, true).then(function () {
        window.location.reload();
    });
}

/**
 * Called on every touch page's DOMContentLoaded to reconcile the theme:
 *   ?theme= URL param  >  saved preference  >  default.
 * A URL param always wins for this page view and is persisted for next time.
 */
function initThemeSystem() {
    var urlTheme = themeNameFromURL();
    if (urlTheme) {
        applyThemeByName(urlTheme, true);
        return;
    }
    var saved = loadThemeName();
    applyThemeByName(saved || THEME_DEFAULT, false);
}

document.addEventListener('DOMContentLoaded', initThemeSystem);

