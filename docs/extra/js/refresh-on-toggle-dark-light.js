
// Robust theme toggle handler for MkDocs Material palette radios.
(function() {
  const RELOAD_DELAY_MS = 60; // small debounce to allow palette state commit
  let scheduled = false;

  function handleThemeChange() {
    if (scheduled) return;
    scheduled = true;
    setTimeout(() => {
      // Try soft refresh first (custom hook if provided)
      try {
        if (typeof window.refreshTheme === 'function') {
          window.refreshTheme();
          scheduled = false;
          return;
        }
      } catch (_) { /* ignore */ }
      // Hard reload fallback
      location.reload();
    }, RELOAD_DELAY_MS);
  }

  function wireExisting() {
    const radios = document.querySelectorAll('input[id^="__palette_"][type="radio"]');
    radios.forEach(r => {
      if (!r.__themeWired) {
        r.addEventListener('change', handleThemeChange);
        r.__themeWired = true;
      }
    });
  }

  // Initial attempt after DOMContentLoaded
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', wireExisting);
  } else {
    wireExisting();
  }

  // Observe for late-added palette inputs (some features lazy-load)
  const observer = new MutationObserver(() => wireExisting());
  observer.observe(document.documentElement, { subtree: true, childList: true });
})();
