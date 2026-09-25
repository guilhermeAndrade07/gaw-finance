(function () {
    var t = localStorage.getItem('gaw_theme');
    if (t === 'light' || t === 'dark') {
        document.documentElement.setAttribute('data-bs-theme', t);
        try {
            var raw = sessionStorage.getItem('__ADMINOX_CONFIG__');
            if (raw) {
                var cfg = JSON.parse(raw);
                cfg.theme = t;
                sessionStorage.setItem('__ADMINOX_CONFIG__', JSON.stringify(cfg));
            } else {
                sessionStorage.setItem('__ADMINOX_CONFIG__', JSON.stringify({ theme: t }));
            }
        } catch (e) {}
    }
})();
