(function () {
    const dataElement = document.getElementById('dashboard-data');
    if (!dataElement) return;

    const dashboardData = JSON.parse(dataElement.textContent);
    const colors = ['#4BC0C0', '#FFCE56', '#FF6384', '#FFFFFF', '#36A2EB', '#8B4513', '#FF9F40', '#9966FF', '#C9CBCF'];
    const monthlyExpenseTotalElement = document.getElementById('monthlyExpenseTotal');
    let categoryChart = null;

    function formatBRL(value) {
        return Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function updateMonthlyExpenseTotal(data) {
        const total = (data || []).reduce((sum, currentValue) => sum + Number(currentValue || 0), 0);
        if (monthlyExpenseTotalElement) {
            monthlyExpenseTotalElement.textContent = `R$ ${formatBRL(total)}`;
        }
    }

    function updateCategoryChart(labels, data) {
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        updateMonthlyExpenseTotal(data);

        if (categoryChart) {
            categoryChart.destroy();
        }

        categoryChart = new Chart(categoryCtx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors.slice(0, labels.length),
                    borderColor: '#fff',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((context.parsed / total) * 100).toFixed(1);
                                return context.label + ': R$ ' + context.parsed.toFixed(2) + ' (' + percentage + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    const cashFlowCtx = document.getElementById('cashFlowChart').getContext('2d');
    new Chart(cashFlowCtx, {
        type: 'bar',
        data: {
            labels: dashboardData.cashFlow.labels,
            datasets: [
                {
                    label: 'Entradas',
                    data: dashboardData.cashFlow.inflows,
                    backgroundColor: '#28a745',
                    borderColor: '#1e7e34',
                    borderWidth: 2,
                },
                {
                    label: 'Saídas',
                    data: dashboardData.cashFlow.outflows,
                    backgroundColor: '#dc3545',
                    borderColor: '#bb2d3b',
                    borderWidth: 2,
                }
            ]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toFixed(2);
                        }
                    }
                }
            }
        }
    });

    updateCategoryChart(dashboardData.expenses.labels, dashboardData.expenses.data);

    const monthSelector = document.getElementById('monthSelector');
    if (monthSelector) {
        monthSelector.addEventListener('change', function(event) {
            const monthYear = event.target.value;
            const [year, month] = monthYear.split('-');
            let url = `/api/expenses-by-month/?month=${month}&year=${year}`;
            if (dashboardData.selectedBankId) {
                url += `&bank=${dashboardData.selectedBankId}`;
            }

            fetch(url)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateCategoryChart(data.labels, data.data);
                    } else {
                        console.error('Erro ao atualizar dados:', data.error);
                    }
                })
                .catch(error => console.error('Erro na requisicao:', error));
        });
    }

    const bankSelector = document.getElementById('bankSelector');
    if (bankSelector) {
        bankSelector.addEventListener('change', function(event) {
            const params = new URLSearchParams(window.location.search);
            const bankValue = event.target.value;
            if (bankValue) {
                params.set('bank', bankValue);
            } else {
                params.delete('bank');
            }
            window.location.search = params.toString();
        });
    }
})();
