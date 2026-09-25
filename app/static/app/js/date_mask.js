(function () {
    document.querySelectorAll('.js-date-mask').forEach((input) => {
        input.addEventListener('input', (event) => {
            let value = event.target.value.replace(/\D/g, '').slice(0, 8);
            if (value.length > 4) {
                value = `${value.slice(0, 2)}/${value.slice(2, 4)}/${value.slice(4)}`;
            } else if (value.length > 2) {
                value = `${value.slice(0, 2)}/${value.slice(2)}`;
            }
            event.target.value = value;
        });
    });
})();
