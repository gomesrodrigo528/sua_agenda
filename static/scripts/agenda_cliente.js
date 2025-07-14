async function buscarAgendamentos() {
    const form = document.getElementById('formAgendamentos');
    const mensagem = document.querySelector('.msg');
    const resultadoDiv = document.getElementById('resultado');

    // Mostrar mensagem de carregamento
    resultadoDiv.innerHTML = '<p>Carregando seus agendamentos...</p>';

    const url = `/api/agenda_cliente`;

    try {
        const response = await fetch(url);
        resultadoDiv.innerHTML = ''; // Limpa resultados anteriores

        if (response.ok) {
            const contentType = response.headers.get("content-type");

            if (!contentType || !contentType.includes("application/json")) {
                throw new Error("Resposta do servidor não é JSON.");
            }

            const data = await response.json();

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
                resultadoDiv.innerHTML = '<p>Nenhum agendamento encontrado para este cliente.</p>';
            }
        } else {
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const errorData = await response.json();
                resultadoDiv.innerHTML = `<p>${errorData.mensagem || errorData.erro || 'Erro ao buscar agendamentos.'}</p>`;
            } else {
                resultadoDiv.innerHTML = `<p>Erro ${response.status}: ${response.statusText}</p>`;
            }
        }
    } catch (error) {
        console.error('Erro:', error);
        resultadoDiv.innerHTML = `<p>Erro ao buscar agendamentos: ${error.message}</p>`;
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
        link.addEventListener('click', () => {
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
            alert('Cliente não logado!');
            return;
        }
        let cliente = {};
        try {
            const res = await fetch(`/api/cliente/${clienteId}`);
            if (res.ok) {
                cliente = await res.json();
            }
        } catch (e) {}
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
            alert('Cliente não logado!');
            return;
        }
        const email = document.getElementById('cliente_email').value.trim();
        const telefone = document.getElementById('cliente_telefone').value.trim();
        const endereco = document.getElementById('cliente_endereco').value.trim();
        const senha = document.getElementById('cliente_senha').value;
        if (!email || !telefone || !endereco) {
            alert('Preencha todos os campos obrigatórios!');
            return;
        }
        const payload = { email, telefone, endereco };
        if (senha) payload.senha = senha;
        try {
            const res = await fetch(`/api/cliente/${clienteId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                alert('Dados atualizados com sucesso!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditarCliente'));
                modal.hide();
                atualizarNomeClienteTopo();
            } else {
                const erro = await res.json();
                alert(erro.error || 'Erro ao atualizar dados.');
            }
        } catch (e) {
            alert('Erro ao atualizar dados.');
        }
    });
}

// Função para renderizar agendamentos com botão Cancelar
function renderizarAgendamentos(agendamentos) {
    const container = document.getElementById('lista-agendamentos');
    container.innerHTML = '';
    agendamentos.forEach(agendamento => {
        const card = document.createElement('div');
        card.className = 'agendamento-card';
        // Mensagem WhatsApp
        const mensagem = encodeURIComponent(
            `Olá, gostaria de falar sobre meu agendamento:\n` +
            `Cliente: ${document.getElementById('userName').textContent}\n` +
            `Serviço: ${agendamento.nome_servico}\n` +
            `Data: ${formatarDataBR(agendamento.data)}\n` +
            `Horário: ${formatarHora(agendamento.horario)}`
        );
        // Telefone do profissional
        const telefoneProf = agendamento.telefone_profissional ? agendamento.telefone_profissional.replace(/\D/g, '') : '';
        // Botão WhatsApp
        let whatsappBtn = '';
        if (telefoneProf.length >= 10) {
            whatsappBtn = `<button class="btn-whatsapp" title="Conversar no WhatsApp" data-tel="${telefoneProf}" data-msg="${mensagem}"><i class='fab fa-whatsapp'></i></button>`;
        } else {
            whatsappBtn = `<button class="btn-whatsapp" title="WhatsApp não disponível" disabled><i class='fab fa-whatsapp'></i></button>`;
        }
        card.innerHTML = `
            <div class="agendamento-label">${agendamento.nome_empresa || ''}</div>
            <div class="agendamento-info"><span class="agendamento-label">Data:</span> ${formatarDataBR(agendamento.data)}</div>
            <div class="agendamento-info"><span class="agendamento-label">Horário:</span> ${formatarHora(agendamento.horario)}</div>
            <div class="agendamento-info"><span class="agendamento-label">Serviço:</span> ${agendamento.nome_servico}</div>
            <div class="agendamento-info"><span class="agendamento-label">Profissional:</span> ${agendamento.nome_profissional}</div>
            <div class="botoes-agendamento">
                <button class="btn-cancelar" data-id="${agendamento.id}">Cancelar</button>
                ${whatsappBtn}
            </div>
        `;
        container.appendChild(card);
    });
    // Adiciona eventos aos botões WhatsApp
    container.querySelectorAll('.btn-whatsapp').forEach(btn => {
        btn.addEventListener('click', function() {
            const tel = this.getAttribute('data-tel');
            const msg = this.getAttribute('data-msg');
            if (tel && msg) {
                window.open(`https://wa.me/${tel}?text=${msg}`, '_blank');
            }
        });
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

// Função para confirmar cancelamento
const btnConfirmarCancelamento = document.getElementById('btnConfirmarCancelamento');
if (btnConfirmarCancelamento) {
    btnConfirmarCancelamento.addEventListener('click', async function() {
        const justificativa = document.getElementById('justificativa_cancelamento').value.trim();
        if (!justificativa) {
            alert('Por favor, informe a justificativa do cancelamento.');
            return;
        }
        if (!agendamentoIdParaCancelar) {
            alert('Agendamento não selecionado.');
            return;
        }
        mostrarLoadingOverlay();
        try {
            const res = await fetch(`/api/agendamento/cancelar/${agendamentoIdParaCancelar}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ justificativa })
            });
            esconderLoadingOverlay();
            if (res.ok) {
                alert('Agendamento cancelado com sucesso!');
                const modal = bootstrap.Modal.getInstance(document.getElementById('modalJustificativaCancelamento'));
                modal.hide();
                // Atualizar lista de agendamentos
                carregarAgendamentos();
            } else {
                const erro = await res.json();
                alert(erro.error || 'Erro ao cancelar agendamento.');
            }
        } catch (e) {
            esconderLoadingOverlay();
            alert('Erro ao cancelar agendamento.');
        }
    });
}

// Função para carregar agendamentos do cliente
async function carregarAgendamentos() {
    try {
        const res = await fetch('/api/meus-agendamentos');
        if (res.ok) {
            const agendamentos = await res.json();
            renderizarAgendamentos(agendamentos);
        }
    } catch (e) {}
}
document.addEventListener('DOMContentLoaded', carregarAgendamentos);
