(function () {
    const dataElement = document.getElementById('dashboard-data');
    if (!dataElement) return;

    const dashboardData = JSON.parse(dataElement.textContent);
    const colors = ['#4BC0C0', '#FFCE56', '#FF6384', '#FFFFFF', '#36A2EB', '#8B4513', '#FF9F40', '#9966FF', '#C9CBCF'];
    const monthlyExpenseTotalElement = document.getElementById('monthlyExpenseTotal');
    let categoryChart = null;
    let cashFlowChart = null;
    let categoryLabels = dashboardData.expenses.labels;
    let categoryData = dashboardData.expenses.data;

    function formatBRL(value) {
        return Number(value || 0).toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        });
    }

    function isDarkTheme() {
        return document.documentElement.getAttribute('data-bs-theme') === 'dark';
    }

    function resolveColor(varName, darkFallback, lightFallback) {
        const value = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
        return value || (isDarkTheme() ? darkFallback : lightFallback);
    }

    function chartAxisColors() {
        return {
            tick: resolveColor('--bs-body-color', 'rgba(255, 255, 255, 0.87)', '#212529'),
            grid: isDarkTheme() ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)',
            border: isDarkTheme() ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)',
        };
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

        const axisColors = chartAxisColors();
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
                        labels: {
                            color: axisColors.tick,
                        },
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

    function buildCashFlowChart() {
        const cashFlowCtx = document.getElementById('cashFlowChart').getContext('2d');
        const axisColors = chartAxisColors();

        if (cashFlowChart) {
            cashFlowChart.destroy();
        }

        cashFlowChart = new Chart(cashFlowCtx, {
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
                        labels: {
                            color: axisColors.tick,
                        },
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: axisColors.tick,
                        },
                        grid: {
                            color: axisColors.grid,
                            borderColor: axisColors.border,
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: axisColors.tick,
                            callback: function(value) {
                                return 'R$ ' + value.toFixed(2);
                            }
                        },
                        grid: {
                            color: axisColors.grid,
                            borderColor: axisColors.border,
                        }
                    }
                }
            }
        });
    }

    updateCategoryChart(categoryLabels, categoryData);
    buildCashFlowChart();

    // Re-renders the charts when the user toggles light/dark mode.
    new MutationObserver(function () {
        if (categoryChart) {
            updateCategoryChart(categoryLabels, categoryData);
        }
        if (cashFlowChart) {
            buildCashFlowChart();
        }
    }).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme'],
    });

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
                        categoryLabels = data.labels;
                        categoryData = data.data;
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
