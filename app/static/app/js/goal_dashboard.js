(function () {
    const dataElement = document.getElementById('goal-dashboard-data');
    if (!dataElement) return;

    let currentData = JSON.parse(dataElement.textContent);
    let goalChart = null;

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

    function colorForPercentage(pct) {
        if (pct > 100) return '#dc3545';
        if (pct >= 70) return '#ffc107';
        return '#28a745';
    }

    function renderGoalChart(labels, percentages) {
        const ctx = document.getElementById('goalChart').getContext('2d');
        const backgroundColors = percentages.map(pct => colorForPercentage(pct));
        const axisColors = chartAxisColors();

        if (goalChart) {
            goalChart.destroy();
        }

        goalChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Progresso (%)',
                    data: percentages,
                    backgroundColor: backgroundColors,
                    borderColor: backgroundColors,
                    borderWidth: 1,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const idx = context.dataIndex;
                                const spentVal = currentData.spent[idx] || 0;
                                const goalVal = currentData.goals[idx] || 0;
                                const pct = context.parsed.x.toFixed(1);
                                return `Gasto: R$ ${formatBRL(spentVal)} / Meta: R$ ${formatBRL(goalVal)} (${pct}%)`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: 100,
                        ticks: {
                            color: axisColors.tick,
                            callback: function(value) { return value + '%'; }
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

    function renderGoalDetails(data) {
        const details = document.getElementById('goalDetails');
        details.replaceChildren();

        if (!data.labels || data.labels.length === 0) {
            const empty = document.createElement('p');
            empty.className = 'text-muted text-center';
            empty.textContent = 'Nenhuma meta definida para este periodo.';
            details.appendChild(empty);
            return;
        }

        const list = document.createElement('div');
        list.className = 'list-group list-group-flush';

        for (let i = 0; i < data.labels.length; i++) {
            const item = document.createElement('div');
            item.className = 'list-group-item px-0';

            const itemHeader = document.createElement('div');
            itemHeader.className = 'd-flex justify-content-between';

            const nameElement = document.createElement('span');
            nameElement.className = 'fw-medium';
            nameElement.textContent = data.labels[i];

            const percentageElement = document.createElement('span');
            percentageElement.className = 'badge';
            percentageElement.style.backgroundColor = colorForPercentage(data.percentages[i] || 0);
            percentageElement.style.color = '#000';
            percentageElement.textContent = `${(data.percentages[i] || 0).toFixed(1)}%`;

            const valuesElement = document.createElement('p');
            valuesElement.className = 'mb-0 text-muted small';
            valuesElement.textContent = `R$ ${formatBRL(data.spent[i] || 0)} de R$ ${formatBRL(data.goals[i] || 0)}`;

            itemHeader.append(nameElement, percentageElement);
            item.append(itemHeader, valuesElement);
            list.appendChild(item);
        }

        details.appendChild(list);
    }

    function appendTextCell(row, text) {
        const cell = document.createElement('td');
        cell.textContent = text;
        row.appendChild(cell);
        return cell;
    }

    function renderGoalTable(data) {
        const tableBody = document.getElementById('goalTableBody');
        tableBody.replaceChildren();

        if (!data.goal_ids || data.goal_ids.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.className = 'text-center text-muted';
            cell.textContent = 'Nenhuma meta para o periodo selecionado.';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }

        data.goal_ids.forEach((goalId, index) => {
            const row = document.createElement('tr');
            row.dataset.goalId = goalId;

            const categoryCell = document.createElement('td');
            const categoryName = document.createElement('h5');
            categoryName.className = 'm-0 fw-medium';
            categoryName.textContent = data.labels[index];
            categoryCell.appendChild(categoryName);
            row.appendChild(categoryCell);

            appendTextCell(row, `R$ ${formatBRL(data.goals[index] || 0)}`);
            appendTextCell(row, `R$ ${formatBRL(data.spent[index] || 0)}`);

            const progressCell = document.createElement('td');
            const progress = document.createElement('div');
            const percentage = Number(data.percentages[index] || 0);
            progress.className = 'progress-bar progress-bar-cell';
            progress.setAttribute('role', 'progressbar');
            progress.style.width = `${Math.min(percentage, 100)}%`;
            progress.style.color = '#000';
            progress.setAttribute('aria-valuenow', percentage);
            progress.setAttribute('aria-valuemin', '0');
            progress.setAttribute('aria-valuemax', '100');
            progress.textContent = `${percentage}%`;
            progress.style.backgroundColor = colorForPercentage(percentage);

            const progressWrapper = document.createElement('div');
            progressWrapper.className = 'progress';
            progressWrapper.style.height = '20px';
            progressWrapper.appendChild(progress);
            progressCell.appendChild(progressWrapper);
            row.appendChild(progressCell);

            const actionsCell = document.createElement('td');
            const updateLink = document.createElement('a');
            updateLink.href = `/goals/${encodeURIComponent(goalId)}/update/`;
            updateLink.className = 'table-action-btn';
            updateLink.title = 'Editar';
            const updateIcon = document.createElement('i');
            updateIcon.className = 'mdi mdi-pencil';
            updateLink.appendChild(updateIcon);

            const deleteLink = document.createElement('a');
            deleteLink.href = `/goals/${encodeURIComponent(goalId)}/delete/`;
            deleteLink.className = 'table-action-btn';
            deleteLink.title = 'Excluir';
            const deleteIcon = document.createElement('i');
            deleteIcon.className = 'mdi mdi-close';
            deleteLink.appendChild(deleteIcon);

            actionsCell.append(updateLink, deleteLink);
            row.appendChild(actionsCell);
            tableBody.appendChild(row);
        });
    }

    function updatePeriodLabel(label) {
        document.querySelectorAll('.goal-period-label').forEach(element => {
            element.textContent = label;
        });
    }

    renderGoalChart(currentData.labels, currentData.percentages);
    renderGoalDetails(currentData);
    renderGoalTable(currentData);

    // Re-renders the chart when the user toggles light/dark mode.
    new MutationObserver(function () {
        if (goalChart) {
            renderGoalChart(currentData.labels, currentData.percentages);
        }
    }).observe(document.documentElement, {
        attributes: true,
        attributeFilter: ['data-bs-theme'],
    });

    const monthSelector = document.getElementById('goalMonthSelector');
    if (monthSelector) {
        monthSelector.addEventListener('change', function(event) {
            const monthYear = event.target.value;
            const [year, month] = monthYear.split('-');

            fetch(`/api/goal-progress/?month=${month}&year=${year}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        currentData = data;
                        renderGoalChart(data.labels, data.percentages);
                        renderGoalDetails(data);
                        renderGoalTable(data);
                        updatePeriodLabel(event.target.options[event.target.selectedIndex].textContent.trim());
                    } else {
                        console.error('Erro ao atualizar metas:', data.error);
                    }
                })
                .catch(error => console.error('Erro na requisicao:', error));
        });
    }
})();
