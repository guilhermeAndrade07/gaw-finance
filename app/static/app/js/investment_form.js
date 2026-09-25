(function () {
    const assetTypeField = document.querySelector('[data-asset-type-field]');
    const fixedIncomeWrapper = document.querySelector('[data-fixed-income-wrapper]');
    if (!assetTypeField || !fixedIncomeWrapper) return;

    function toggleFixedIncomeFields() {
        fixedIncomeWrapper.style.display = assetTypeField.value === 'RENDA_FIXA' ? 'flex' : 'none';
    }

    assetTypeField.addEventListener('change', toggleFixedIncomeFields);
    toggleFixedIncomeFields();
})();
