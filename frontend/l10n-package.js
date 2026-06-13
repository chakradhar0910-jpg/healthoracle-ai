// HealthOracle AI — Frontend Localization & Language Package Engine
// =================================================================

(function () {
    // ── 1. Fetch Interceptor for API Header Localization ──────────────────────
    const originalFetch = window.fetch;
    window.fetch = async function (input, init) {
        const langSelect = document.getElementById("lang-select");
        const currentLang = langSelect ? langSelect.value : "en";
        
        // Inject Accept-Language header to translate backend responses & AI outputs
        if (init) {
            init.headers = init.headers || {};
            if (init.headers instanceof Headers) {
                init.headers.set("Accept-Language", currentLang);
            } else if (Array.isArray(init.headers)) {
                const hasLang = init.headers.some(([k]) => k.toLowerCase() === "accept-language");
                if (!hasLang) {
                    init.headers.push(["Accept-Language", currentLang]);
                }
            } else {
                init.headers["Accept-Language"] = currentLang;
            }
        } else {
            init = {
                headers: {
                    "Accept-Language": currentLang
                }
            };
        }
        return originalFetch(input, init);
    };

    // Initialize global strings collection
    window.L10N_STRINGS = window.L10N_STRINGS || {};
    window.__l10n_translating = false;

    // Helper to escape regex special characters
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // Helper to load language scripts dynamically and bypass CORS issues
    function loadLanguagePackage(lang, callback) {
        if (lang === "en" || (window.L10N_STRINGS && window.L10N_STRINGS[lang])) {
            callback();
            return;
        }
        const script = document.createElement("script");
        script.src = `locales/${lang}.js`;
        script.onload = () => {
            callback();
        };
        script.onerror = () => {
            console.error(`Failed to load language package locales/${lang}.js. Falling back to English.`);
            callback();
        };
        document.head.appendChild(script);
    }

    // ── 2. DOM Translation Engine ─────────────────────────────────────────────
    function translateTextNode(node, lang) {
        const dict = window.L10N_STRINGS[lang] || {};
        const text = node.nodeValue;
        const trimmed = text.trim();
        if (trimmed.length === 0) return;

        // Capture original English text on first pass or if main app updated it
        if (!window.__l10n_translating && node.__origText === undefined) {
            node.__origText = text;
        }

        const orig = node.__origText !== undefined ? node.__origText : text;
        const origTrimmed = orig.trim();

        if (lang === "en") {
            node.nodeValue = orig;
        } else {
            let translated = dict[origTrimmed];
            if (!translated) {
                // Try finding matches or replacing tokens (e.g. dynamic values / percentages)
                for (const [key, val] of Object.entries(dict)) {
                    if (key.length > 2 && origTrimmed.includes(key)) {
                        translated = (translated || origTrimmed).replace(new RegExp(escapeRegExp(key), 'g'), val);
                    }
                }
            }

            if (translated) {
                node.nodeValue = orig.replace(origTrimmed, translated);
            } else {
                // Partial string replacement fallback for keys
                let processed = orig;
                let matched = false;
                for (const [key, val] of Object.entries(dict)) {
                    if (key.length > 2 && processed.includes(key)) {
                        processed = processed.replace(new RegExp(escapeRegExp(key), 'g'), val);
                        matched = true;
                    }
                }
                if (matched) {
                    node.nodeValue = processed;
                }
            }
        }
    }

    function translateElement(el, lang) {
        if (!el) return;
        const tagName = el.tagName ? el.tagName.toLowerCase() : "";
        if (tagName === "script" || tagName === "style" || tagName === "svg" || tagName === "path") return;

        const dict = window.L10N_STRINGS[lang] || {};

        // Translate inputs and textareas placeholders
        if (tagName === "input" || tagName === "textarea") {
            if (el.placeholder) {
                if (el.__origPlaceholder === undefined) {
                    el.__origPlaceholder = el.placeholder;
                }
                const orig = el.__origPlaceholder;
                el.placeholder = (lang === "en" ? orig : (dict[orig] || orig));
            }
        }

        // Translate title attributes
        if (el.title) {
            if (el.__origTitle === undefined) {
                el.__origTitle = el.title;
            }
            const orig = el.__origTitle;
            el.title = (lang === "en" ? orig : (dict[orig] || orig));
        }

        // Translate select option elements
        if (tagName === "option") {
            if (el.__origText === undefined) {
                el.__origText = el.textContent;
            }
            const orig = el.__origText;
            const origTrimmed = orig.trim();
            el.textContent = (lang === "en" ? orig : (dict[origTrimmed] || orig));
            return;
        }

        // Traverse child nodes
        for (let i = 0; i < el.childNodes.length; i++) {
            const node = el.childNodes[i];
            if (node.nodeType === Node.TEXT_NODE) {
                translateTextNode(node, lang);
            } else if (node.nodeType === Node.ELEMENT_NODE) {
                translateElement(node, lang);
            }
        }
    }

    // ── 3. Localization Manager API ───────────────────────────────────────────
    window.L10N_ENGINE = {
        currentLang: "en",
        setLanguage: function (lang) {
            loadLanguagePackage(lang, () => {
                this.currentLang = lang;
                this.translateDOM();
            });
        },
        translateDOM: function () {
            window.__l10n_translating = true;
            translateElement(document.body, this.currentLang);
            window.__l10n_translating = false;
        }
    };

    // ── 4. MutationObserver to translate dynamically rendered elements ───────
    const observer = new MutationObserver((mutations) => {
        const langSelect = document.getElementById("lang-select");
        const currentLang = langSelect ? langSelect.value : "en";
        if (currentLang === "en") return;

        observer.disconnect(); // Prevent infinite feedback loops

        mutations.forEach((mutation) => {
            if (mutation.type === "childList") {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        translateElement(node, currentLang);
                    } else if (node.nodeType === Node.TEXT_NODE) {
                        translateTextNode(node, currentLang);
                    }
                });
            } else if (mutation.type === "characterData") {
                // Dynamic text update from script.js
                translateTextNode(mutation.target, currentLang);
            }
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    });

    // ── 5. Initialization and Event Listeners ─────────────────────────────────
    document.addEventListener("DOMContentLoaded", () => {
        const langSelect = document.getElementById("lang-select");
        if (langSelect) {
            langSelect.addEventListener("change", (e) => {
                window.L10N_ENGINE.setLanguage(e.target.value);
            });

            // If a different language was restored or preselected on load
            if (langSelect.value !== "en") {
                window.L10N_ENGINE.setLanguage(langSelect.value);
            }
        }

        // Start observing DOM changes for dynamic translations
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    });
})();
