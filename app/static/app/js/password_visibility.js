(function () {
    var toggle = document.getElementById('togglePassword');
    var input = document.getElementById('password');
    var icon = document.getElementById('eyeIcon');
    if (!toggle || !input || !icon) return;

    toggle.addEventListener('click', function () {
        var isPassword = input.type === 'password';
        input.type = isPassword ? 'text' : 'password';
        icon.setAttribute('icon', isPassword ? 'mdi:eye-outline' : 'mdi:eye-off-outline');
        toggle.setAttribute('aria-pressed', String(isPassword));
        toggle.setAttribute('aria-label', isPassword ? 'Ocultar senha' : 'Mostrar senha');
        input.focus();
    });
})();
