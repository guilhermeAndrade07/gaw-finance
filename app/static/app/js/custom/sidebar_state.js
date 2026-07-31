(function () {
  var KEY = 'gaw_sidenav_condensed';
  var html = document.documentElement;

  function isDesktop() {
    return window.innerWidth > 1199;
  }

  function applyStoredState() {
    if (isDesktop() && sessionStorage.getItem(KEY) === '1') {
      html.setAttribute('data-sidenav-size', 'condensed');
    }
  }

  window.addEventListener('DOMContentLoaded', function () {
    applyStoredState();

    var btn = document.querySelector('.sidenav-toggle-button');
    if (btn) {
      btn.addEventListener('click', function () {
        setTimeout(function () {
          var size = html.getAttribute('data-sidenav-size');
          if (size === 'condensed') {
            sessionStorage.setItem(KEY, '1');
          } else {
            sessionStorage.removeItem(KEY);
          }
        }, 50);
      });
    }
  });

  window.addEventListener('load', function () {
    applyStoredState();
  });

  window.addEventListener('resize', function () {
    if (!isDesktop()) {
      sessionStorage.removeItem(KEY);
    } else {
      applyStoredState();
    }
  });
})();