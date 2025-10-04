/* ==========================================================================
   Chart.js Integration for Dashboard Analytics
   Modern responsive charts with theme support
   ========================================================================== */

// Chart configuration with theme support
const chartConfig = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            position: 'top',
            labels: {
                usePointStyle: true,
                padding: 20,
                font: {
                    family: 'Segoe UI, sans-serif',
                    size: 12
                }
            }
        },
        tooltip: {
            backgroundColor: 'rgba(0, 0, 0, 0.8)',
            titleColor: '#fff',
            bodyColor: '#fff',
            borderColor: '#ddd',
            borderWidth: 1,
            cornerRadius: 8,
            displayColors: true
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            grid: {
                color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
                font: {
                    family: 'Segoe UI, sans-serif'
                }
            }
        },
        x: {
            grid: {
                color: 'rgba(0, 0, 0, 0.1)'
            },
            ticks: {
                font: {
                    family: 'Segoe UI, sans-serif'
                }
            }
        }
    }
};

// Theme-aware color schemes
const getChartColors = (theme = 'light') => {
    if (theme === 'dark') {
        return {
            primary: '#4fa8db',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            grid: 'rgba(255, 255, 255, 0.1)',
            text: '#ffffff'
        };
    }
    return {
        primary: '#3498db',
        success: '#28a745',
        warning: '#ffc107',
        danger: '#dc3545',
        info: '#17a2b8',
        grid: 'rgba(0, 0, 0, 0.1)',
        text: '#212529'
    };
};

// Initialize charts when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    
    // Listen for theme changes
    window.addEventListener('themeChanged', function(e) {
        updateChartsTheme(e.detail.theme);
    });
});

// Chart instances storage
const chartInstances = {};

function initializeCharts() {
    // Revenue Chart
    const revenueCtx = document.getElementById('revenueChart');
    if (revenueCtx) {
        chartInstances.revenue = createRevenueChart(revenueCtx);
    }
    
    // Appointments Chart
    const appointmentsCtx = document.getElementById('appointmentsChart');
    if (appointmentsCtx) {
        chartInstances.appointments = createAppointmentsChart(appointmentsCtx);
    }
    
    // Services Chart
    const servicesCtx = document.getElementById('servicesChart');
    if (servicesCtx) {
        chartInstances.services = createServicesChart(servicesCtx);
    }
    
    // Monthly Overview Chart
    const monthlyCtx = document.getElementById('monthlyChart');
    if (monthlyCtx) {
        chartInstances.monthly = createMonthlyChart(monthlyCtx);
    }
}

function createRevenueChart(ctx) {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const colors = getChartColors(currentTheme);
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun'],
            datasets: [{
                label: 'Receita (R$)',
                data: [1200, 1900, 3000, 5000, 2000, 3000],
                borderColor: colors.primary,
                backgroundColor: colors.primary + '20',
                borderWidth: 3,
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            ...chartConfig,
            plugins: {
                ...chartConfig.plugins,
                title: {
                    display: true,
                    text: 'Receita Mensal',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

function createAppointmentsChart(ctx) {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const colors = getChartColors(currentTheme);
    
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Confirmados', 'Pendentes', 'Cancelados', 'Concluídos'],
            datasets: [{
                data: [30, 15, 5, 50],
                backgroundColor: [
                    colors.success,
                    colors.warning,
                    colors.danger,
                    colors.primary
                ],
                borderWidth: 0,
                cutout: '60%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        usePointStyle: true
                    }
                },
                title: {
                    display: true,
                    text: 'Status dos Agendamentos',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

function createServicesChart(ctx) {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const colors = getChartColors(currentTheme);
    
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Corte', 'Barba', 'Sobrancelha', 'Hidratação', 'Coloração'],
            datasets: [{
                label: 'Agendamentos',
                data: [45, 25, 30, 20, 15],
                backgroundColor: [
                    colors.primary,
                    colors.success,
                    colors.warning,
                    colors.info,
                    colors.danger
                ],
                borderRadius: 4,
                borderSkipped: false
            }]
        },
        options: {
            ...chartConfig,
            plugins: {
                ...chartConfig.plugins,
                title: {
                    display: true,
                    text: 'Serviços Mais Populares',
                    font: {
                        size: 16,
                        weight: 'bold'
                    }
                }
            }
        }
    });
}

function createMonthlyChart(ctx) {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const colors = getChartColors(currentTheme);
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Sem 1', 'Sem 2', 'Sem 3', 'Sem 4'],
            datasets: [
                {
                    label: 'Agendamentos',
                    data: [12, 19, 15, 25],
                    borderColor: colors.primary,
                    backgroundColor: colors.primary + '20',
                    yAxisID: 'y'
                },
                {
                    label: 'Receita (x100)',
                    data: [8, 15, 12, 20],
                    borderColor: colors.success,
                    backgroundColor: colors.success + '20',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: {
                    display: true,
                    text: 'Visão Geral Semanal'
                }
            },
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left'
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false
                    }
                }
            }
        }
    });
}

function updateChartsTheme(theme) {
    const colors = getChartColors(theme);
    
    Object.values(chartInstances).forEach(chart => {
        if (chart && chart.options && chart.options.scales) {
            // Update grid colors
            if (chart.options.scales.y && chart.options.scales.y.grid) {
                chart.options.scales.y.grid.color = colors.grid;
            }
            if (chart.options.scales.x && chart.options.scales.x.grid) {
                chart.options.scales.x.grid.color = colors.grid;
            }
            
            // Update text colors
            if (chart.options.plugins && chart.options.plugins.legend) {
                chart.options.plugins.legend.labels.color = colors.text;
            }
            
            chart.update('none');
        }
    });
}

// Lazy load charts when they come into view
function setupLazyCharts() {
    const chartContainers = document.querySelectorAll('.chart-container[data-chart]');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const container = entry.target;
                const chartType = container.dataset.chart;
                loadChart(container, chartType);
                observer.unobserve(container);
            }
        });
    });
    
    chartContainers.forEach(container => {
        observer.observe(container);
    });
}

function loadChart(container, chartType) {
    // Add loading spinner
    container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center h-100">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Carregando gráfico...</span>
            </div>
        </div>
    `;
    
    // Simulate API call and create chart
    setTimeout(() => {
        const canvas = document.createElement('canvas');
        container.innerHTML = '';
        container.appendChild(canvas);
        
        switch (chartType) {
            case 'revenue':
                chartInstances[chartType] = createRevenueChart(canvas);
                break;
            case 'appointments':
                chartInstances[chartType] = createAppointmentsChart(canvas);
                break;
            case 'services':
                chartInstances[chartType] = createServicesChart(canvas);
                break;
            case 'monthly':
                chartInstances[chartType] = createMonthlyChart(canvas);
                break;
        }
    }, 500);
}

// Export for global access
window.chartUtils = {
    initializeCharts,
    setupLazyCharts,
    updateChartsTheme,
    chartInstances
};