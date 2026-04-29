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

    // Wire up the sticky action bar buttons
    _bindTouchActionBar();

    // Machine config panel (localStorage-backed)
    if (typeof initMachineConfigPanel === 'function') initMachineConfigPanel();

    // Auto-size inputs/selects if field-sizing:content is unsupported (Firefox < 128)
    if (!CSS.supports('field-sizing', 'content')) {
        _autoSizeAllFields();
    }
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
            const form = document.querySelector('#arguments');
            if (!form) return;
            for (const [key, value] of Object.entries(data)) {
                const el = form.querySelector(`[name="${CSS.escape(key)}"]`);
                if (!el) continue;
                if (el.type === 'checkbox') {
                    el.checked = (value === true || value === 'true' || value === '1' || value === 'on');
                } else {
                    el.value = value;
                }
                el.dispatchEvent(new Event('change'));
            }
        } catch (_) {
            alert('Invalid JSON file.');
        }
    };
    reader.readAsText(file);
    input.value = '';
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
