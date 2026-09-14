(function () {
  var KEY = 'gaw_theme';
  var html = document.documentElement;

  function isValidTheme(theme) {
    return theme === 'light' || theme === 'dark';
  }

  function syncAdminoxConfig(theme) {
    try {
      var raw = sessionStorage.getItem('__ADMINOX_CONFIG__');
      var config = raw ? JSON.parse(raw) : {};
      config.theme = theme;
      sessionStorage.setItem('__ADMINOX_CONFIG__', JSON.stringify(config));
    } catch (e) {}

    if (window.config && typeof window.config === 'object') {
      window.config.theme = theme;
    }
  }

  function applyStoredTheme() {
    var theme = localStorage.getItem(KEY);
    if (!isValidTheme(theme)) {
      return;
    }

    html.setAttribute('data-bs-theme', theme);
    syncAdminoxConfig(theme);
  }

  function toggleTheme(event) {
    event.preventDefault();
    event.stopImmediatePropagation();

    var current = html.getAttribute('data-bs-theme');
    var next = current === 'dark' ? 'light' : 'dark';

    html.setAttribute('data-bs-theme', next);
    localStorage.setItem(KEY, next);
    syncAdminoxConfig(next);

    if (window.defaultConfig && window.defaultConfig.theme) {
      window.defaultConfig.theme = next;
    }
  }

  applyStoredTheme();

  document.addEventListener('click', function (event) {
    var target = event.target.closest && event.target.closest('#light-dark-mode');
    if (target) {
      toggleTheme(event);
    }
  }, true);

  // Persist changes made by Adminox without racing its click handler.
  new MutationObserver(function () {
    var current = html.getAttribute('data-bs-theme');
    if (isValidTheme(current)) {
      localStorage.setItem(KEY, current);
      syncAdminoxConfig(current);
    }
  }).observe(html, { attributes: true, attributeFilter: ['data-bs-theme'] });

  window.addEventListener('pageshow', applyStoredTheme);
})();
