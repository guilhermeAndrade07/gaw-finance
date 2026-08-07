(function () {
  var KEY = 'gaw_theme';

  window.addEventListener('DOMContentLoaded', function () {
    var theme = localStorage.getItem(KEY);
    if (theme) {
      document.documentElement.setAttribute('data-bs-theme', theme);
    }

    var btn = document.getElementById('light-dark-mode');
    if (btn) {
      btn.addEventListener('click', function () {
        setTimeout(function () {
          var current = document.documentElement.getAttribute('data-bs-theme');
          if (current) {
            localStorage.setItem(KEY, current);
          }
        }, 50);
      });
    }
  });

  window.addEventListener('pageshow', function () {
    var theme = localStorage.getItem(KEY);
    if (theme) {
      document.documentElement.setAttribute('data-bs-theme', theme);
      try {
        var raw = sessionStorage.getItem('__ADMINOX_CONFIG__');
        if (raw) {
          var cfg = JSON.parse(raw);
          cfg.theme = theme;
          sessionStorage.setItem('__ADMINOX_CONFIG__', JSON.stringify(cfg));
        } else {
          sessionStorage.setItem('__ADMINOX_CONFIG__', JSON.stringify({ theme: theme }));
        }
      } catch (e) {}
    }
  });
})();