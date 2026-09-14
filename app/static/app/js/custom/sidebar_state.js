(function () {
  var CONFIG_KEY = '__ADMINOX_CONFIG__';
  var html = document.documentElement;

  function isDesktop() {
    return window.innerWidth > 1199;
  }

  function isMobile() {
    return !isDesktop();
  }

  function readAdminoxConfig() {
    try {
      return JSON.parse(sessionStorage.getItem(CONFIG_KEY) || '{}');
    } catch (e) {
      return {};
    }
  }

  function persistDesktopSize(size) {
    if (size !== 'default' && size !== 'condensed') {
      return;
    }

    var config = readAdminoxConfig();
    config.sidenav = config.sidenav || {};
    config.sidenav.size = size;
    sessionStorage.setItem(CONFIG_KEY, JSON.stringify(config));

    if (window.config && window.config.sidenav) {
      window.config.sidenav.size = size;
    }
  }

  function removeBackdrop() {
    var backdrop = document.getElementById('custom-backdrop');
    if (backdrop) {
      backdrop.remove();
    }
    document.body.style.overflow = '';
    document.body.style.paddingRight = '';
  }

  function createBackdrop() {
    var existing = document.getElementById('custom-backdrop');
    if (existing) {
      return;
    }

    var backdrop = document.createElement('div');
    backdrop.id = 'custom-backdrop';
    backdrop.className = 'offcanvas-backdrop fade show';
    backdrop.addEventListener('click', closeMobileMenu);
    document.body.appendChild(backdrop);
    document.body.style.overflow = 'hidden';
  }

  function closeMobileMenu() {
    html.classList.remove('sidebar-enable');
    removeBackdrop();
  }

  function toggleMobileMenu(event) {
    event.preventDefault();
    event.stopImmediatePropagation();

    if (!isMobile()) {
      var currentSize = html.getAttribute('data-sidenav-size');
      var nextSize = currentSize === 'condensed' ? 'default' : 'condensed';

      closeMobileMenu();
      html.setAttribute('data-sidenav-size', nextSize);
      persistDesktopSize(nextSize);
      return;
    }

    // Adminox creates a new backdrop on every click. Own the mobile toggle
    // so opening and closing always leave a single, clean overlay state.
    if (html.classList.contains('sidebar-enable')) {
      closeMobileMenu();
    } else {
      createBackdrop();
      html.classList.add('sidebar-enable');
    }
  }

  document.addEventListener('click', function (event) {
    var target = event.target.closest && event.target.closest('.sidenav-toggle-button');
    if (target && target.matches('button.sidenav-toggle-button')) {
      toggleMobileMenu(event);
    }
  }, true);

  window.addEventListener('DOMContentLoaded', function () {
    if (isDesktop()) {
      var config = readAdminoxConfig();
      var size = config.sidenav && config.sidenav.size;
      if (size !== 'default' && size !== 'condensed') {
        size = 'default';
        persistDesktopSize(size);
      }
      html.setAttribute('data-sidenav-size', size);
    }

    window.addEventListener('resize', function () {
      if (isMobile()) {
        closeMobileMenu();
        return;
      }

      var config = readAdminoxConfig();
      var size = config.sidenav && config.sidenav.size;
      if (size !== 'default' && size !== 'condensed') {
        size = 'default';
        persistDesktopSize(size);
      }
      html.setAttribute('data-sidenav-size', size);
    });
  });
})();
