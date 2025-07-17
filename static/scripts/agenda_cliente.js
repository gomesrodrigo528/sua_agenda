async function buscarAgendamentos() {
    const form = document.getElementById('formAgendamentos');
    const mensagem = document.querySelector('.msg');
    const resultadoDiv = document.getElementById('resultado');

    // Função para obter cookie
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Verificar se o cliente está logado
    const idUsuarioCliente = getCookie('id_usuario_cliente');
    const idCliente = getCookie('cliente_id');
    const idEmpresa = getCookie('id_empresa');
    
    if (!idUsuarioCliente || !idCliente || !idEmpresa) {
        console.log('Cliente não está logado, redirecionando...');
        window.location.href = '/login';
        return;
    }

    // Mostrar mensagem de carregamento
    resultadoDiv.innerHTML = '<p>Carregando seus agendamentos...</p>';

    const url = `/api/agenda_cliente`;

    try {
        // Preparar headers com fallback
        let headers = {};
        if (idUsuarioCliente) {
            headers['X-Usuario-Cliente'] = idUsuarioCliente;
        }

        const response = await fetch(url, {
            method: 'GET',
            headers: headers,
            credentials: 'include' // Incluir cookies na requisição
        });
        
        resultadoDiv.innerHTML = ''; // Limpa resultados anteriores

        if (response.ok) {
            const contentType = response.headers.get("content-type");

            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("Resposta do servidor não é JSON.");
            }

            const data = await response.json();
            console.log('Dados recebidos em buscarAgendamentos:', data);

            if (data.agendamentos && data.agendamentos.length > 0) {
                // Oculta o formulário e exibe a mensagem
                form.style.display = 'none';
                mensagem.style.display = 'block';

                data.agendamentos.forEach(agendamento => {
                    const whatsappUrl = `https://wa.me/${agendamento.empresa.telefone}?text=${encodeURIComponent(
                        `Olá, sou o ${data.cliente.nome}. Gostaria de falar sobre meu agendamento com ${agendamento.usuario} na data ${formatarData(agendamento.data)}, horário ${agendamento.horario}, para o serviço ${agendamento.servico}.`
                    )}`;

                    const card = `<div class="card">
    <div class="card-header">
        ${agendamento.empresa.logo ? `<img src="${agendamento.empresa.logo}" alt="Logo da Empresa" class="card-logo">` : ''}
        <h3 class="card-title">${agendamento.empresa.nome}</h3>
    </div>
    <p><strong>Data:</strong> ${formatarData(agendamento.data)}</p>
    <p><strong>Horário:</strong> ${agendamento.horario}</p>
    <p><strong>Serviço:</strong> ${agendamento.servico}</p>
    <p><strong>Profissional:</strong> ${agendamento.usuario}</p>
   <button class="whatsapp-button" onclick="window.open('${whatsappUrl}', '_blank')">
    <img src="https://upload.wikimedia.org/wikipedia/commons/6/6b/WhatsApp.svg" alt="WhatsApp Icon">
</button>

</div>

`;
                    resultadoDiv.innerHTML += card;
                });
            } else {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #666;">
                        <div style="font-size: 64px; margin-bottom: 20px; color: #ccc;">
                            <i class="bi bi-calendar-x"></i>
                        </div>
                        <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Nenhum agendamento encontrado</h3>
                        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            Você ainda não possui agendamentos ativos.<br>
                            Que tal fazer seu primeiro agendamento?
                        </p>
                        <a href="/agendamento" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                            <i class="bi bi-calendar-plus"></i> Fazer Agendamento
                        </a>
                    </div>
                `;
            }
        } else if (response.status === 401) {
            console.log('Não autorizado, redirecionando para login...');
            window.location.href = '/login';
        } else {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const errorData = await response.json();
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #666;">
                        <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            ${errorData.mensagem || errorData.erro || 'Ocorreu um erro ao buscar seus agendamentos.'}
                        </p>
                        <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                            <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                        </button>
                    </div>
                `;
            } else {
                resultadoDiv.innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #666;">
                        <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            Erro ${response.status}: ${response.statusText}
                        </p>
                        <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                            <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                        </button>
                    </div>
                `;
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        resultadoDiv.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #666;">
                <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                    <i class="bi bi-exclamation-triangle"></i>
                </div>
                <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    Ocorreu um erro inesperado ao buscar seus agendamentos.
                </p>
                <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                    <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                </button>
            </div>
        `;
    }
}

// Função para formatar a data no padrão DD/MM/AAAA
function formatarData(dataISO) {
    const [ano, mes, dia] = dataISO.split('-');
    return `${dia}/${mes}/${ano}`;
}

function formatarDataBR(dataISO) {
    if (!dataISO) return '';
    const [ano, mes, dia] = dataISO.split('-');
    return `${dia}/${mes}/${ano}`;
}
function formatarHora(hora) {
    if (!hora) return '';
    return hora.slice(0,5); // Pega HH:mm
}

// Funcionalidade do Menu Lateral
document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('mainContent');
    const menuToggle = document.getElementById('menuToggle');
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    // Função para abrir o menu
    function openSidebar() {
        sidebar.classList.add('active');
        sidebarOverlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    // Função para fechar o menu
    function closeSidebar() {
        sidebar.classList.remove('active');
        sidebarOverlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    // Event listeners
    if (menuToggle) menuToggle.addEventListener('click', openSidebar);
    if (sidebarToggle) sidebarToggle.addEventListener('click', closeSidebar);
    if (sidebarOverlay) sidebarOverlay.addEventListener('click', closeSidebar);

    // Fechar menu ao clicar em um link
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            // Fechar menu mobile se necessário
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Fechar menu ao redimensionar a tela
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            closeSidebar();
        }
    });
});

// Preencher nome do cliente logado no topo
function atualizarNomeClienteTopo() {
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    const nome = getCookie('cliente_name');
    if (nome) {
        document.getElementById('userName').textContent = nome;
    }
}
document.addEventListener('DOMContentLoaded', atualizarNomeClienteTopo);

// Abrir modal de edição de cliente e preencher dados (reutiliza lógica do agendamento_cli.js)
const btnEditarCliente = document.getElementById('btnEditarCliente');
if (btnEditarCliente) {
    btnEditarCliente.addEventListener('click', async function() {
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        const clienteId = getCookie('cliente_id');
        if (!clienteId) {
            mostrarAlerta('Cliente não logado!', 'error');
            return;
        }
        let cliente = {};
        try {
            const res = await fetch(`/api/cliente/${clienteId}`);
            if (res.ok) {
                cliente = await res.json();
            }
        } catch (e) {
            console.error('Erro ao carregar dados do cliente:', e);
        }
        document.getElementById('cliente_nome').value = cliente.nome_cliente || getCookie('cliente_name') || '';
        document.getElementById('cliente_email').value = cliente.email || getCookie('cliente_email') || '';
        document.getElementById('cliente_telefone').value = cliente.telefone || '';
        document.getElementById('cliente_endereco').value = cliente.endereco || '';
        document.getElementById('cliente_senha').value = '';
        const modal = new bootstrap.Modal(document.getElementById('modalEditarCliente'));
        modal.show();
    });
}

// Salvar alterações do cliente (reutiliza lógica do agendamento_cli.js)
const btnSalvarCliente = document.getElementById('btnSalvarCliente');
if (btnSalvarCliente) {
    btnSalvarCliente.addEventListener('click', async function() {
        const clienteId = (function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        })('cliente_id');
        if (!clienteId) {
            mostrarAlerta('Cliente não logado!', 'error');
            return;
        }
        const email = document.getElementById('cliente_email').value.trim();
        const telefone = document.getElementById('cliente_telefone').value.trim();
        const endereco = document.getElementById('cliente_endereco').value.trim();
        const senha = document.getElementById('cliente_senha').value;
        if (!email || !telefone || !endereco) {
            mostrarAlerta('Preencha todos os campos obrigatórios!', 'warning');
            return;
        }
        const payload = { email, telefone, endereco };
        if (senha) payload.senha = senha;
        try {
            mostrarTelaCarregamento('Salvando alterações...');
            const res = await fetch(`/api/cliente/${clienteId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                mostrarAlerta('Dados atualizados com sucesso!', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarCliente'));
                modal.hide();
                atualizarNomeClienteTopo();
            } else {
                const erro = await res.json();
                mostrarAlerta(erro.error || 'Erro ao atualizar dados.', 'error');
            }
        } catch (e) {
            mostrarAlerta('Erro ao atualizar dados.', 'error');
        } finally {
            esconderTelaCarregamento();
        }
    });
}

// Função para renderizar agendamentos com botão Cancelar
function renderizarAgendamentos(data) {
    const container = document.getElementById('lista-agendamentos');
    container.innerHTML = '';
    if (!data.agendamentos || data.agendamentos.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #666;">
                <div style="font-size: 64px; margin-bottom: 20px; color: #ccc;">
                    <i class="bi bi-calendar-x"></i>
                </div>
                <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Nenhum agendamento encontrado</h3>
                <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    Você ainda não possui agendamentos ativos.<br>
                    Que tal fazer seu primeiro agendamento?
                </p>
                <a href="/agendamento" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                    <i class="bi bi-calendar-plus"></i> Fazer Agendamento
                </a>
            </div>
        `;
        return;
    }
    data.agendamentos.forEach(agendamento => {
        const whatsappUrl = `https://wa.me/${agendamento.empresa.telefone}?text=${encodeURIComponent(
            `Olá, sou o ${data.cliente.nome}. Gostaria de falar sobre meu agendamento com ${agendamento.usuario} na data ${formatarData(agendamento.data)}, horário ${agendamento.horario}, para o serviço ${agendamento.servico}.`
        )}`;
        const card = document.createElement('div');
        card.className = 'agendamento-card';
        card.innerHTML = `
            <div class="agendamento-label">
                ${agendamento.empresa.logo ? `<img src="${agendamento.empresa.logo}" alt="Logo da Empresa" class="card-logo">` : ''}
                ${agendamento.empresa.nome || ''}
            </div>
            <div class="agendamento-info"><span class="agendamento-label">Data:</span> ${formatarDataBR(agendamento.data)}</div>
            <div class="agendamento-info"><span class="agendamento-label">Horário:</span> ${formatarHora(agendamento.horario)}</div>
            <div class="agendamento-info"><span class="agendamento-label">Serviço:</span> ${agendamento.servico}</div>
            <div class="agendamento-info"><span class="agendamento-label">Profissional:</span> ${agendamento.usuario}</div>
            <div class="botoes-agendamento">
                <button class="btn-cancelar" data-id="${agendamento.id || ''}">Cancelar</button>
                <button class="btn-whatsapp" title="Conversar no WhatsApp" onclick="window.open('${whatsappUrl}', '_blank')"><i class='fab fa-whatsapp'></i></button>
            </div>
        `;
        container.appendChild(card);
    });
    // Adiciona eventos aos botões Cancelar
    container.querySelectorAll('.btn-cancelar').forEach(btn => {
        btn.addEventListener('click', function() {
            const id = this.getAttribute('data-id');
            abrirModalCancelamento(id);
        });
    });
}

// Variável global para armazenar o ID do agendamento a cancelar
let agendamentoIdParaCancelar = null;

// Função para abrir modal de justificativa
window.abrirModalCancelamento = function(id) {
    agendamentoIdParaCancelar = id;
    document.getElementById('justificativa_cancelamento').value = '';
    const modal = new bootstrap.Modal(document.getElementById('modalJustificativaCancelamento'));
    modal.show();
}

// Função para mostrar overlay de carregamento
function mostrarLoadingOverlay() {
    let overlay = document.getElementById('loading-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.innerHTML = '<div class="loading-spinner"></div><span>Processando...</span>';
        document.body.appendChild(overlay);
    }
    overlay.style.display = 'flex';
}
function esconderLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) overlay.style.display = 'none';
}

// Funções para gerenciar popups
function mostrarPopup(tipo, mensagem, titulo = null, callback = null) {
    const popup = document.getElementById(`popup-${tipo}`);
    const messageElement = document.getElementById(`popup-${tipo}-message`);
    
    if (titulo) {
        const titleElement = popup.querySelector('.popup-title');
        titleElement.textContent = titulo;
    }
    
    messageElement.textContent = mensagem;
    popup.style.display = 'flex';
    
    // Se houver callback, configurar o botão de confirmação
    if (callback && tipo === 'confirm') {
        const confirmBtn = document.getElementById('popup-confirm-btn');
        confirmBtn.onclick = () => {
            fecharPopup(`popup-${tipo}`);
            callback();
        };
    }
}

function fecharPopup(popupId) {
    const popup = document.getElementById(popupId);
    popup.classList.add('fade-out');
    setTimeout(() => {
        popup.style.display = 'none';
        popup.classList.remove('fade-out');
    }, 300);
}

// Função para substituir alert
function mostrarAlerta(mensagem, tipo = 'warning') {
    mostrarPopup(tipo, mensagem);
}

// Função para substituir confirm
function mostrarConfirmacao(mensagem, callback) {
    mostrarPopup('confirm', mensagem, 'Confirmar', callback);
}

// Função para confirmar cancelamento
const btnConfirmarCancelamento = document.getElementById('btnConfirmarCancelamento');
if (btnConfirmarCancelamento) {
    btnConfirmarCancelamento.addEventListener('click', async function() {
        const justificativa = document.getElementById('justificativa_cancelamento').value.trim();
        if (!justificativa) {
            mostrarAlerta('Por favor, informe a justificativa do cancelamento.', 'warning');
            return;
        }
        if (!agendamentoIdParaCancelar) {
            mostrarAlerta('Agendamento não selecionado.', 'error');
            return;
        }
        mostrarTelaCarregamento('Cancelando agendamento...');
        try {
            const res = await fetch(`/api/agendamento/cancelar/${agendamentoIdParaCancelar}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ justificativa })
            });
            
            if (res.ok) {
                mostrarAlerta('Agendamento cancelado com sucesso!', 'success');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalJustificativaCancelamento'));
                modal.hide();
                // Atualizar lista de agendamentos
                mostrarTelaCarregamento('Atualizando lista...');
                await carregarAgendamentos();
            } else {
                const erro = await res.json();
                mostrarAlerta(erro.error || 'Erro ao cancelar agendamento.', 'error');
            }
        } catch (e) {
            mostrarAlerta('Erro ao cancelar agendamento.', 'error');
        } finally {
            esconderTelaCarregamento();
        }
    });
}

// Função para carregar agendamentos do cliente
async function carregarAgendamentos() {
    try {
        console.log('🚀 Iniciando carregamento de agendamentos...');
        
        // Função para obter cookie
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        
        // Debug: mostrar todos os cookies
        console.log('🍪 Cookies disponíveis:');
        const allCookies = document.cookie.split(';');
        allCookies.forEach(cookie => {
            console.log('  ', cookie.trim());
        });
        
        // Verificar se o cliente está logado
        const idUsuarioCliente = getCookie('id_usuario_cliente');
        const idCliente = getCookie('cliente_id');
        const idEmpresa = getCookie('id_empresa');
        
        console.log('🔍 Verificação de autenticação:');
        console.log('  id_usuario_cliente:', idUsuarioCliente);
        console.log('  cliente_id:', idCliente);
        console.log('  id_empresa:', idEmpresa);
        
        if (!idUsuarioCliente || !idCliente || !idEmpresa) {
            console.log('❌ Cliente não está logado, redirecionando...');
            window.location.href = '/login';
            return;
        }
        
        console.log('✅ Cliente logado, buscando agendamentos...');
        
        // Preparar headers com fallback
        let headers = {};
        if (idUsuarioCliente) {
            headers['X-Usuario-Cliente'] = idUsuarioCliente;
        }
        
        console.log('📤 Fazendo requisição para /api/agenda_cliente...');
        console.log('📋 Headers:', headers);
        
        const res = await fetch('/api/agenda_cliente', { 
            method: 'GET',
            headers: headers,
            credentials: 'include' // Incluir cookies na requisição
        });
        
        console.log('📥 Resposta recebida:');
        console.log('  Status:', res.status);
        console.log('  Status Text:', res.statusText);
        console.log('  Headers:', Object.fromEntries(res.headers.entries()));
        
        if (res.ok) {
            const data = await res.json();
            console.log('✅ Dados recebidos com sucesso:', data);
            renderizarAgendamentos(data);
        } else if (res.status === 401) {
            console.log('❌ Não autorizado, redirecionando para login...');
            window.location.href = '/login';
        } else if (res.status === 404) {
            // Verificar se é a mensagem de "nenhum agendamento encontrado"
            const errorData = await res.json().catch(() => ({}));
            if (errorData.mensagem && errorData.mensagem.includes('Nenhum agendamento encontrado')) {
                // Tratar como situação normal - sem agendamentos
                document.getElementById('lista-agendamentos').innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #666;">
                        <div style="font-size: 64px; margin-bottom: 20px; color: #ccc;">
                            <i class="bi bi-calendar-x"></i>
                        </div>
                        <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Nenhum agendamento encontrado</h3>
                        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            Você ainda não possui agendamentos ativos.<br>
                            Que tal fazer seu primeiro agendamento?
                        </p>
                        <a href="/agendamento" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                            <i class="bi bi-calendar-plus"></i> Fazer Agendamento
                        </a>
                    </div>
                `;
            } else {
                // Outro erro 404 - mostrar mensagem de erro
                document.getElementById('lista-agendamentos').innerHTML = `
                    <div style="text-align: center; padding: 60px 20px; color: #666;">
                        <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                            <i class="bi bi-exclamation-triangle"></i>
                        </div>
                        <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                        <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                            ${errorData.erro || errorData.mensagem || 'Ocorreu um erro ao buscar seus agendamentos.'}
                        </p>
                        <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                            <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                        </button>
                    </div>
                `;
            }
        } else {
            console.error('❌ Erro ao buscar agendamentos:', res.status, res.statusText);
            const errorData = await res.json().catch(() => ({}));
            console.error('❌ Dados do erro:', errorData);
            document.getElementById('lista-agendamentos').innerHTML = `
                <div style="text-align: center; padding: 60px 20px; color: #666;">
                    <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                        <i class="bi bi-exclamation-triangle"></i>
                    </div>
                    <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                    <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                        ${errorData.erro || errorData.mensagem || 'Ocorreu um erro ao buscar seus agendamentos.'}
                    </p>
                    <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                        <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                    </button>
                </div>
            `;
        }
    } catch (error) {
        console.error('❌ Erro na função carregarAgendamentos:', error);
        document.getElementById('lista-agendamentos').innerHTML = `
            <div style="text-align: center; padding: 60px 20px; color: #666;">
                <div style="font-size: 64px; margin-bottom: 20px; color: #dc3545;">
                    <i class="bi bi-exclamation-triangle"></i>
                </div>
                <h3 style="color: #333; margin-bottom: 15px; font-weight: 600;">Erro ao carregar agendamentos</h3>
                <p style="font-size: 16px; line-height: 1.6; margin-bottom: 30px;">
                    Ocorreu um erro inesperado ao buscar seus agendamentos.
                </p>
                <button onclick="carregarAgendamentos()" class="btn btn-primary" style="padding: 12px 30px; font-size: 16px; border-radius: 8px;">
                    <i class="bi bi-arrow-clockwise"></i> Tentar Novamente
                </button>
            </div>
        `;
        throw error; // Re-throw para que o .finally() seja executado
    }
}

// Funções para controlar a tela de carregamento
function mostrarTelaCarregamento(mensagem = 'Carregando...') {
    const loadingScreen = document.getElementById('loading-screen');
    const loadingText = document.getElementById('loading-text');
    
    if (loadingText) {
        loadingText.textContent = mensagem;
    }
    
    loadingScreen.style.display = 'flex';
    loadingScreen.classList.add('fade-in');
    loadingScreen.classList.remove('fade-out');
}

function esconderTelaCarregamento() {
    const loadingScreen = document.getElementById('loading-screen');
    loadingScreen.classList.add('fade-out');
    loadingScreen.classList.remove('fade-in');
    
    setTimeout(() => {
        loadingScreen.style.display = 'none';
    }, 300);
}

// Detectar mudança de aba (visibilitychange) - removido para evitar carregamentos desnecessários
// document.addEventListener('visibilitychange', function() {
//     if (document.visibilityState === 'visible') {
//         console.log('🔄 Aba voltou ao foco, recarregando dados...');
//         mostrarTelaCarregamento('Atualizando dados...');
//         
//         // Aguardar um pouco antes de recarregar para dar tempo da aba estabilizar
//         setTimeout(() => {
//             carregarAgendamentos().finally(() => {
//                 esconderTelaCarregamento();
//             });
//         }, 500);
//     }
// });

// Detectar quando a janela ganha foco - removido para evitar carregamentos desnecessários
// window.addEventListener('focus', function() {
//     console.log('🔄 Janela ganhou foco, verificando se precisa atualizar...');
//     // Só mostrar loading se a página já foi carregada antes
//     if (document.getElementById('lista-agendamentos').children.length > 0) {
//         mostrarTelaCarregamento('Verificando atualizações...');
//         
//         setTimeout(() => {
//             carregarAgendamentos().finally(() => {
//                 esconderTelaCarregamento();
//             });
//         }, 300);
//     }
// });

// Carregar agendamentos quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    console.log('Página carregada, iniciando carregamento de agendamentos...');
    mostrarTelaCarregamento('Carregando seus agendamentos...');
    
    carregarAgendamentos().finally(() => {
        esconderTelaCarregamento();
    });
    
    atualizarNomeClienteTopo();
});
