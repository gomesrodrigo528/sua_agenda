// Sistema de Notificações da Barra Superior
// Variáveis globais
let notificationData = { total: 0, agendamentos: [] };
let notificationInterval;

// Inicialização quando a página carrega
document.addEventListener('DOMContentLoaded', function() {
    carregarDadosEmpresa();
    carregarDadosUsuario();
    carregarNotificacoes();
    
    // Atualizar notificações a cada 30 segundos
    notificationInterval = setInterval(carregarNotificacoes, 30000);
    
    // Configurar botão do menu lateral na barra superior (mobile)
    configurarBotaoMenuMobile();
    
    // Fechar dropdown ao clicar fora
    document.addEventListener('click', function(event) {
        const dropdown = document.getElementById('notification-dropdown');
        const btn = document.getElementById('notification-btn');
        
        if (!btn.contains(event.target) && !dropdown.contains(event.target)) {
            fecharDropdown();
        }
    });
});

// Configurar botão do menu lateral na barra superior (mobile)
function configurarBotaoMenuMobile() {
    const menuToggleBtn = document.getElementById('toggle-menu-mobile');
    if (menuToggleBtn) {
        menuToggleBtn.addEventListener('click', function() {
            // Alternar classe do menu lateral diretamente
            const menuLateral = document.getElementById('menu-lateral');
            if (menuLateral) {
                menuLateral.classList.toggle('open');
                console.log('Menu lateral toggled:', menuLateral.classList.contains('open'));
            } else {
                console.error('Menu lateral não encontrado');
            }
        });
    }
}

        // Carregar dados da empresa
        async function carregarDadosEmpresa() {
            try {
                const response = await fetch('/api/empresa/logada');
                if (response.ok) {
                    const data = await response.json();
                    
                    // Atualizar logo apenas se existir (desktop)
                    const logoElement = document.getElementById('empresa-logo');
                    if (logoElement && data.logo) {
                        logoElement.src = data.logo;
                    }
                    
                    // Atualizar nome da empresa
                    const nomeElement = document.getElementById('empresa-nome');
                    if (nomeElement) {
                        nomeElement.textContent = data.nome_empresa;
                    }
                    
                    // Aplicar cor da empresa na barra superior (mesma lógica do menu lateral)
                    const corEmpresa = data.cor_emp || '#343a40';
                    document.documentElement.style.setProperty('--cor-empresa', corEmpresa);
                    
                    // Aplicar cor diretamente na barra de notificações
                    const notificationBar = document.getElementById('notification-bar');
                    if (notificationBar) {
                        notificationBar.style.backgroundColor = corEmpresa;
                    }
                }
            } catch (error) {
                console.error('Erro ao carregar dados da empresa:', error);
            }
        }

// Carregar dados do usuário
async function carregarDadosUsuario() {
    try {
        const response = await fetch('/api/usuario/logado');
        if (response.ok) {
            const data = await response.json();
            
            // Atualizar nome do usuário apenas se existir
            const usuarioElement = document.getElementById('user-name');
            if (usuarioElement && data.nome_usuario) {
                usuarioElement.textContent = data.nome_usuario;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar dados do usuário:', error);
    }
}

// Carregar notificações
async function carregarNotificacoes() {
    try {
        const response = await fetch('/api/notificacoes/agendamentos');
        if (response.ok) {
            notificationData = await response.json();
            atualizarInterfaceNotificacoes();
        }
    } catch (error) {
        console.error('Erro ao carregar notificações:', error);
    }
}

// Atualizar interface das notificações
function atualizarInterfaceNotificacoes() {
    const badge = document.getElementById('notification-badge');
    const dropdown = document.getElementById('notification-dropdown');
    const list = document.getElementById('notification-list');
    const empty = document.getElementById('notification-empty');
    
    // Verificar se os elementos existem antes de usar
    if (!badge || !dropdown || !list || !empty) {
        console.warn('Elementos de notificação não encontrados');
        return;
    }
    
    if (notificationData.total > 0) {
        // Mostrar badge
        if (badge) {
            badge.textContent = notificationData.total;
            badge.style.display = 'flex';
        }
        
        // Mostrar lista de agendamentos
        if (list) {
            list.innerHTML = '';
            notificationData.agendamentos.forEach(agendamento => {
                const item = criarItemNotificacao(agendamento);
                list.appendChild(item);
            });
        }
        
        if (empty) {
            empty.style.display = 'none';
        }
    } else {
        // Esconder badge
        if (badge) {
            badge.style.display = 'none';
        }
        
        // Mostrar estado vazio
        if (list) {
            list.innerHTML = '';
        }
        if (empty) {
            empty.style.display = 'block';
        }
    }
}

// Criar item de notificação
function criarItemNotificacao(agendamento) {
    const item = document.createElement('div');
    item.className = 'notification-item';
    
    // Formatar data
    const dataFormatada = new Date(agendamento.data).toLocaleDateString('pt-BR');
    const horaFormatada = agendamento.horario.substring(0, 5);
    
    item.innerHTML = `
        <div class="notification-item-header">
            <div class="notification-cliente">${agendamento.cliente_nome}</div>
            <div class="notification-servico">${agendamento.servico_nome}</div>
        </div>
        <div class="notification-datetime">
            <i class="bi bi-calendar3 me-1"></i>${dataFormatada}
            <i class="bi bi-clock ms-3 me-1"></i>${horaFormatada}
        </div>
        ${agendamento.descricao ? `<div class="notification-descricao">${agendamento.descricao}</div>` : ''}
    `;
    
    // Adicionar evento de clique
    item.addEventListener('click', function() {
        // Aqui você pode adicionar ação ao clicar no agendamento
        console.log('Agendamento clicado:', agendamento.id);
        // Opcional: redirecionar para detalhes do agendamento
        // window.location.href = `/agendamento/${agendamento.id}`;
    });
    
    return item;
}

// Toggle do dropdown
function toggleNotificationDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    dropdown.classList.toggle('show');
}

// Fechar dropdown
function fecharDropdown() {
    const dropdown = document.getElementById('notification-dropdown');
    dropdown.classList.remove('show');
}

// Marcar todos como vistos
async function marcarTodosComoVistos() {
    try {
        const response = await fetch('/api/notificacoes/marcar-visto', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            // Recarregar notificações
            await carregarNotificacoes();
            fecharDropdown();
            
            // Mostrar mensagem de sucesso
            mostrarMensagem('Sucesso', 'Todos os agendamentos foram marcados como vistos!');
        } else {
            throw new Error('Erro ao marcar como vistos');
        }
    } catch (error) {
        console.error('Erro ao marcar como vistos:', error);
        mostrarMensagem('Erro', 'Erro ao marcar agendamentos como vistos');
    }
}

// Função para mostrar mensagens (reutilizar a existente)
function mostrarMensagem(titulo, mensagem, tipo = 'info') {
    // Usar a função existente do sistema
    if (typeof window.mostrarMensagem === 'function') {
        window.mostrarMensagem(titulo, mensagem, tipo);
    } else {
        alert(`${titulo}: ${mensagem}`);
    }
}

// Limpar intervalo quando a página for fechada
window.addEventListener('beforeunload', function() {
    if (notificationInterval) {
        clearInterval(notificationInterval);
    }
});

// Função para atualizar notificações manualmente (útil para outras páginas)
function atualizarNotificacoes() {
    carregarNotificacoes();
}

// Exportar funções para uso global
window.toggleNotificationDropdown = toggleNotificationDropdown;
window.marcarTodosComoVistos = marcarTodosComoVistos;
window.atualizarNotificacoes = atualizarNotificacoes;
