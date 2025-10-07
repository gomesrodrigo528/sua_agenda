// Dashboard JavaScript - Mobile First

let dashboardData = {};
let graficoFaturamento = null;

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    atualizarDataAtual();
    carregarDashboard();
    
    // Atualizar dashboard a cada 5 minutos
    setInterval(carregarDashboard, 300000);
});

// Atualizar data atual no header
function atualizarDataAtual() {
    const hoje = new Date();
    const opcoes = { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
    };
    const dataFormatada = hoje.toLocaleDateString('pt-BR', opcoes);
    document.getElementById('data-atual').textContent = dataFormatada;
}

// Carregar dados do dashboard
async function carregarDashboard() {
    try {
        mostrarLoading(true);
        
        // Carregar dados principais
        const response = await fetch('/api/dashboard/dados');
        if (!response.ok) {
            throw new Error('Erro ao carregar dados do dashboard');
        }
        
        dashboardData = await response.json();
        
        // Atualizar interface
        atualizarMetricas();
        atualizarProximosAtendimentos();
        atualizarServicosPopulares();
        atualizarResumoFinanceiro();
        
        // Carregar gráfico
        await carregarGraficoFaturamento();
        
        mostrarLoading(false);
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        mostrarErro('Erro ao carregar dados do dashboard');
        mostrarLoading(false);
    }
}

// Atualizar métricas principais
function atualizarMetricas() {
    // Faturamento do dia
    document.getElementById('faturamento-hoje').textContent = 
        formatarMoeda(dashboardData.faturamento_hoje || 0);
    
    // Atendimentos do dia
    document.getElementById('atendimentos-hoje').textContent = 
        dashboardData.atendimentos_hoje || 0;
    document.getElementById('atendimentos-concluidos').textContent = 
        `${dashboardData.atendimentos_concluidos || 0} concluídos`;
    
    // Faturamento do mês
    document.getElementById('faturamento-mes').textContent = 
        formatarMoeda(dashboardData.faturamento_mes || 0);
    
    // Meta do mês (se configurada)
    if (dashboardData.meta_mes && dashboardData.meta_mes > 0) {
        document.getElementById('meta-card').style.display = 'flex';
        document.getElementById('percentual-meta').textContent = 
            `${Math.round(dashboardData.percentual_meta || 0)}%`;
        document.getElementById('valor-meta').textContent = 
            formatarMoeda(dashboardData.meta_mes);
    }
}

// Atualizar próximos atendimentos
function atualizarProximosAtendimentos() {
    const container = document.getElementById('proximos-atendimentos');
    
    if (!dashboardData.proximos_atendimentos || dashboardData.proximos_atendimentos.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-calendar-x"></i>
                <p>Nenhum atendimento nas próximas 3 horas</p>
            </div>
        `;
        return;
    }
    
    const html = dashboardData.proximos_atendimentos.map(atendimento => {
        const cliente = atendimento.clientes || {};
        const servico = atendimento.servicos || {};
        const horario = formatarHorario(atendimento.horario);
        const status = atendimento.status || 'Pendente';
        
        return `
            <div class="atendimento-item">
                <div class="atendimento-horario">${horario}</div>
                <div class="atendimento-info">
                    <div class="atendimento-cliente">${cliente.nome_cliente || 'Cliente'}</div>
                    <div class="atendimento-servico">${servico.nome_servico || 'Serviço'}</div>
                </div>
                <div class="atendimento-status ${status.toLowerCase()}">${status}</div>
            </div>
        `;
    }).join('');
    
    container.innerHTML = html;
}

// Atualizar serviços populares
function atualizarServicosPopulares() {
    const container = document.getElementById('servicos-populares');
    
    if (!dashboardData.servicos_populares || dashboardData.servicos_populares.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-star"></i>
                <p>Nenhum serviço popular encontrado</p>
            </div>
        `;
        return;
    }
    
    const html = dashboardData.servicos_populares.map(servico => `
        <div class="servico-item">
            <div class="servico-nome">${servico[0]}</div>
            <div class="servico-count">${servico[1]}x</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Atualizar resumo financeiro
function atualizarResumoFinanceiro() {
    document.getElementById('clientes-novos').textContent = 
        dashboardData.clientes_novos || 0;
    
    document.getElementById('contas-pendentes').textContent = 
        dashboardData.contas_pendentes || 0;
    
    document.getElementById('valor-pendente').textContent = 
        formatarMoeda(dashboardData.valor_pendente || 0);
}

// Carregar gráfico de faturamento
async function carregarGraficoFaturamento() {
    try {
        const response = await fetch('/api/dashboard/grafico-faturamento');
        if (!response.ok) {
            throw new Error('Erro ao carregar dados do gráfico');
        }
        
        const dadosGrafico = await response.json();
        criarGraficoFaturamento(dadosGrafico);
        
    } catch (error) {
        console.error('Erro ao carregar gráfico:', error);
        document.getElementById('grafico-faturamento').parentElement.innerHTML = 
            '<div class="empty-state"><i class="bi bi-bar-chart"></i><p>Erro ao carregar gráfico</p></div>';
    }
}

// Criar gráfico de faturamento
function criarGraficoFaturamento(dados) {
    const ctx = document.getElementById('grafico-faturamento').getContext('2d');
    
    // Destruir gráfico anterior se existir
    if (graficoFaturamento) {
        graficoFaturamento.destroy();
    }
    
    graficoFaturamento = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: dados.map(item => item.data),
            datasets: [{
                label: 'Faturamento (R$)',
                data: dados.map(item => item.faturamento),
                backgroundColor: 'rgba(102, 126, 234, 0.8)',
                borderColor: 'rgba(102, 126, 234, 1)',
                borderWidth: 1,
                borderRadius: 4,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return 'R$ ' + value.toLocaleString('pt-BR');
                        }
                    }
                },
                x: {
                    ticks: {
                        maxRotation: 45,
                        minRotation: 0
                    }
                }
            },
            animation: {
                duration: 1000,
                easing: 'easeInOutQuart'
            }
        }
    });
}

// Funções utilitárias
function formatarMoeda(valor) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(valor);
}

function formatarHorario(horario) {
    if (!horario) return '';
    return horario.substring(0, 5); // HH:MM
}

function mostrarLoading(mostrar) {
    const overlay = document.getElementById('dashboard-loading');
    overlay.style.display = mostrar ? 'flex' : 'none';
}

function mostrarErro(mensagem) {
    // Usar modal global se disponível
    if (typeof mostrarModalMensagem === 'function') {
        mostrarModalMensagem('Erro', mensagem, 'error');
    } else {
        alert(mensagem);
    }
}

// Função para refresh manual
function refreshDashboard() {
    carregarDashboard();
}

// Event listeners
document.addEventListener('click', function(e) {
    // Refresh button
    if (e.target.closest('.refresh-btn')) {
        carregarDashboard();
    }
});

// PWA - Service Worker registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registrado com sucesso');
            })
            .catch(function(error) {
                console.log('Erro ao registrar ServiceWorker:', error);
            });
    });
}

// Notificações push (se suportado)
if ('Notification' in window && 'serviceWorker' in navigator) {
    if (Notification.permission === 'default') {
        Notification.requestPermission().then(function(permission) {
            if (permission === 'granted') {
                console.log('Permissão para notificações concedida');
            }
        });
    }
}

// Detectar mudanças de conectividade
window.addEventListener('online', function() {
    console.log('Conexão restaurada');
    carregarDashboard();
});

window.addEventListener('offline', function() {
    console.log('Conexão perdida');
    mostrarErro('Conexão perdida. Alguns dados podem não estar atualizados.');
});

// Performance monitoring
window.addEventListener('load', function() {
    if ('performance' in window) {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`Dashboard carregado em ${loadTime}ms`);
    }
});
