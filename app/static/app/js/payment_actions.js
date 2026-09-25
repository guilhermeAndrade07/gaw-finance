(function () {
    const csrfMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfMeta ? csrfMeta.getAttribute('content') : '';

    const toNumber = (value) => {
        const parsed = Number.parseFloat(value);
        return Number.isNaN(parsed) ? 0 : parsed;
    };

    const formatBRL = (value) => {
        return value.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    };

    const updateMoneyElement = (element, value) => {
        if (!element) return;
        element.dataset.total = value.toFixed(2);
        element.textContent = `R$ ${formatBRL(value)}`;
    };

    document.querySelectorAll('.js-payment-paid-checkbox').forEach((checkbox) => {
        checkbox.addEventListener('change', async (event) => {
            const isChecked = event.target.checked;
            const wasChecked = !isChecked;
            const paymentId = event.target.dataset.paymentId;
            const row = document.getElementById(`payment-row-${paymentId}`);
            const totalElement = document.getElementById('payment-total');
            if (!paymentId || !row) return;

            event.target.disabled = true;

            try {
                const endpoint = isChecked
                    ? `/payment/${paymentId}/mark-paid/`
                    : `/payment/${paymentId}/mark-unpaid/`;

                const response = await fetch(endpoint, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });

                if (!response.ok) throw new Error('Erro ao atualizar compra.');

                const showingHidden = totalElement?.dataset.showingHidden === 'true';
                const currentTotal = toNumber(totalElement?.dataset.total);
                const rowValue = toNumber(row.dataset.value);
                const totalDelta = (showingHidden === isChecked) ? rowValue : -rowValue;
                updateMoneyElement(totalElement, Math.max(currentTotal + totalDelta, 0));

                const usedElement = document.getElementById('credit-used');
                const availableElement = document.getElementById('credit-available');
                if (row.dataset.hasCard === '1' && usedElement && availableElement) {
                    const creditDir = isChecked ? -1 : 1;
                    updateMoneyElement(usedElement, Math.max(toNumber(usedElement.dataset.total) + creditDir * rowValue, 0));
                    updateMoneyElement(availableElement, Math.max(toNumber(availableElement.dataset.total) - creditDir * rowValue, 0));
                }

                row.style.opacity = isChecked ? '0.5' : '';
                row.style.textDecoration = isChecked ? 'line-through' : '';
            } catch (error) {
                event.target.disabled = false;
                event.target.checked = wasChecked;
                window.alert('Não foi possível atualizar a compra. Tente novamente.');
            }
        });
    });

    document.querySelectorAll('.js-invoice-pay-btn').forEach((button) => {
        button.addEventListener('click', async (event) => {
            event.stopPropagation();
            const invoiceId = button.dataset.invoiceId;
            if (!invoiceId) return;
            if (!window.confirm('Confirmar o pagamento desta fatura? Todas as compras serão marcadas como pagas.')) return;

            try {
                const response = await fetch(`/invoices/${invoiceId}/pay/`, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });
                if (!response.ok) throw new Error('Erro ao pagar fatura.');
                window.location.reload();
            } catch (error) {
                window.alert('Não foi possível pagar a fatura. Tente novamente.');
            }
        });
    });

    document.querySelectorAll('[data-bs-toggle="collapse"]').forEach((header) => {
        const target = header.getAttribute('data-bs-target');
        const chevron = header.querySelector('.js-chevron');
        if (!target || !chevron) return;

        const targetElement = document.querySelector(target);
        if (!targetElement) return;

        targetElement.addEventListener('show.bs.collapse', () => {
            chevron.classList.replace('mdi-chevron-right', 'mdi-chevron-down');
        });
        targetElement.addEventListener('hide.bs.collapse', () => {
            chevron.classList.replace('mdi-chevron-down', 'mdi-chevron-right');
        });
    });
})();
