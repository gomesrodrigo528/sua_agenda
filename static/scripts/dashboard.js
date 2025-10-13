// Dashboard JavaScript - Mobile First

let dashboardData = {};
let graficoFaturamento = null;

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    atualizarDataAtual();
    carregarComponentesIndividuais();
    
    // Atualizar dashboard a cada 5 minutos
    setInterval(carregarComponentesIndividuais, 300000);
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

// Carregar componentes individualmente
async function carregarComponentesIndividuais() {
    try {
        // Carregar métricas principais primeiro (mais rápido)
        await carregarMetricas();
        
        // Carregar outros componentes em paralelo
        Promise.all([
            carregarProximosAtendimentos(),
            carregarServicosPopulares(),
            carregarResumoFinanceiro(),
            carregarGraficoFaturamento()
        ]).catch(error => {
            console.error('Erro ao carregar componentes:', error);
        });
        
    } catch (error) {
        console.error('Erro ao carregar dashboard:', error);
        mostrarErro('Erro ao carregar dados do dashboard');
    }
}

// Carregar métricas principais
async function carregarMetricas() {
    try {
        const response = await fetch('/api/dashboard/metricas');
        if (!response.ok) {
            throw new Error('Erro ao carregar métricas');
        }
        
        const metricas = await response.json();
        atualizarMetricas(metricas);
        
    } catch (error) {
        console.error('Erro ao carregar métricas:', error);
        // Manter valores padrão em caso de erro
    }
}

// Carregar próximos atendimentos
async function carregarProximosAtendimentos() {
    try {
        const response = await fetch('/api/dashboard/proximos-atendimentos');
        if (!response.ok) {
            throw new Error('Erro ao carregar atendimentos');
        }
        
        const atendimentos = await response.json();
        atualizarProximosAtendimentos(atendimentos);
        
    } catch (error) {
        console.error('Erro ao carregar atendimentos:', error);
        mostrarEstadoVazio('proximos-atendimentos', 'Nenhum atendimento nas próximas 3 horas');
    }
}

// Carregar serviços populares
async function carregarServicosPopulares() {
    try {
        const response = await fetch('/api/dashboard/servicos-populares');
        if (!response.ok) {
            throw new Error('Erro ao carregar serviços');
        }
        
        const servicos = await response.json();
        atualizarServicosPopulares(servicos);
        
    } catch (error) {
        console.error('Erro ao carregar serviços:', error);
        mostrarEstadoVazio('servicos-populares', 'Nenhum serviço popular encontrado');
    }
}

// Carregar resumo financeiro
async function carregarResumoFinanceiro() {
    try {
        const response = await fetch('/api/dashboard/resumo-financeiro');
        if (!response.ok) {
            throw new Error('Erro ao carregar resumo financeiro');
        }
        
        const financeiro = await response.json();
        atualizarResumoFinanceiro(financeiro);
        
    } catch (error) {
        console.error('Erro ao carregar resumo financeiro:', error);
        // Manter valores padrão em caso de erro
    }
}

// Atualizar métricas principais
function atualizarMetricas(metricas) {
    // Faturamento do dia
    document.getElementById('faturamento-hoje').textContent = 
        formatarMoeda(metricas.faturamento_hoje || 0);
    
    // Atendimentos do dia
    document.getElementById('atendimentos-hoje').textContent = 
        metricas.atendimentos_hoje || 0;
    document.getElementById('atendimentos-concluidos').textContent = 
        `${metricas.atendimentos_concluidos || 0} concluídos`;
    
    // Faturamento do mês
    document.getElementById('faturamento-mes').textContent = 
        formatarMoeda(metricas.faturamento_mes || 0);
    
    // Meta do mês (se configurada)
    if (metricas.meta_mes && metricas.meta_mes > 0) {
        document.getElementById('meta-card').style.display = 'flex';
        document.getElementById('percentual-meta').textContent = 
            `${Math.round(metricas.percentual_meta || 0)}%`;
        document.getElementById('valor-meta').textContent = 
            formatarMoeda(metricas.meta_mes);
    }
}

// Atualizar próximos atendimentos
function atualizarProximosAtendimentos(atendimentos) {
    const container = document.getElementById('proximos-atendimentos');
    
    if (!atendimentos || atendimentos.length === 0) {
        mostrarEstadoVazio('proximos-atendimentos', 'Nenhum atendimento nas próximas 3 horas');
        return;
    }
    
    const html = atendimentos.map(atendimento => {
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
function atualizarServicosPopulares(servicos) {
    const container = document.getElementById('servicos-populares');
    
    if (!servicos || servicos.length === 0) {
        mostrarEstadoVazio('servicos-populares', 'Nenhum serviço popular encontrado');
        return;
    }
    
    const html = servicos.map(servico => `
        <div class="servico-item">
            <div class="servico-nome">${servico[0]}</div>
            <div class="servico-count">${servico[1]}x</div>
        </div>
    `).join('');
    
    container.innerHTML = html;
}

// Atualizar resumo financeiro
function atualizarResumoFinanceiro(financeiro) {
    document.getElementById('clientes-novos').textContent = 
        financeiro.clientes_novos || 0;
    
    document.getElementById('contas-pendentes').textContent = 
        financeiro.contas_pendentes || 0;
    
    document.getElementById('valor-pendente').textContent = 
        formatarMoeda(financeiro.valor_pendente || 0);
    
    document.getElementById('contas-pagas').textContent = 
        financeiro.contas_pagas || 0;
    
    document.getElementById('valor-recebido').textContent = 
        formatarMoeda(financeiro.valor_recebido || 0);
    
    document.getElementById('contas-pagar-pendentes').textContent = 
        financeiro.contas_pagar_pendentes || 0;
    
    document.getElementById('valor-pagar-pendente').textContent = 
        formatarMoeda(financeiro.valor_pagar_pendente || 0);
    
    document.getElementById('contas-pagar-pagas').textContent = 
        financeiro.contas_pagar_pagas || 0;
    
    document.getElementById('valor-pago').textContent = 
        formatarMoeda(financeiro.valor_pago || 0);
    
    document.getElementById('entradas-mes').textContent = 
        formatarMoeda(financeiro.entradas_mes || 0);
    
    document.getElementById('saidas-mes').textContent = 
        formatarMoeda(financeiro.saidas_mes || 0);
    
    document.getElementById('saldo-mes').textContent = 
        formatarMoeda(financeiro.saldo_mes || 0);
}

// Carregar gráfico de faturamento
async function carregarGraficoFaturamento() {
    try {
        const response = await fetch('/api/dashboard/grafico-faturamento');
        if (!response.ok) {
            throw new Error('Erro ao carregar dados do gráfico');
        }
        
        const dadosGrafico = await response.json();
        
        // Esconder skeleton e mostrar gráfico
        document.getElementById('chart-loading').style.display = 'none';
        document.getElementById('grafico-faturamento').style.display = 'block';
        
        criarGraficoFaturamento(dadosGrafico);
        
    } catch (error) {
        console.error('Erro ao carregar gráfico:', error);
        document.getElementById('chart-loading').innerHTML = 
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

// Mostrar estado vazio
function mostrarEstadoVazio(containerId, mensagem) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="empty-state">
            <i class="bi bi-calendar-x"></i>
            <p>${mensagem}</p>
        </div>
    `;
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
    carregarComponentesIndividuais();
}

// Event listeners
document.addEventListener('click', function(e) {
    // Refresh button
    if (e.target.closest('.refresh-btn')) {
        carregarComponentesIndividuais();
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
    carregarComponentesIndividuais();
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
