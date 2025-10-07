// Funções para gerenciar popups (escopo global)
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

// Função para substituir confirm
function mostrarConfirmacao(mensagem, callback) {
    mostrarPopup('confirm', mensagem, 'Confirmar', callback);
}

// Função para mostrar pop-up de mensagem
function mostrarMensagem(msg, titulo = 'Mensagem') {
    document.getElementById('modalMensagemLabel').textContent = titulo;
    document.getElementById('modalMensagemBody').textContent = msg;
    var modal = new bootstrap.Modal(document.getElementById('modalMensagem'));
    modal.show();
}

// Funções para gerenciar tela de carregamento
function mostrarCarregamento() {
    document.getElementById('loading-screen').style.display = 'flex';
}

function esconderCarregamento() {
    document.getElementById('loading-screen').style.display = 'none';
}

// Variável global para armazenar o usuário logado
let usuarioLogado = null;

// Função para buscar o usuário logado uma vez
async function buscarUsuarioLogado() {
    try {
        const response = await fetch('/api/usuario/logado');
        if (!response.ok) throw new Error('Erro ao buscar usuário logado');
        usuarioLogado = await response.json();
    } catch (e) {
        usuarioLogado = { nome_usuario: '' };
    }
}

document.addEventListener('DOMContentLoaded', async function () {
    const calendarEl = document.getElementById('calendar');
    const listContainer = document.getElementById('list-container');
    const appointmentList = document.getElementById('appointment-list');
    const filter = document.getElementById('filter');
    let filtroAgendamento = 'meus'; // padrão: meus agendamentos

    await buscarUsuarioLogado(); // Busca o usuário logado uma vez antes de renderizar

    // Botões de filtro
    const btnMeus = document.getElementById('btnMeusAgendamentos');
    const btnTodos = document.getElementById('btnTodosAgendamentos');
    if (btnMeus && btnTodos) {
        btnMeus.addEventListener('click', function () {
            filtroAgendamento = 'meus';
            btnMeus.classList.add('active');
            btnTodos.classList.remove('active');
            calendar.refetchEvents();
            renderAppointments(filter.value);
        });
        btnTodos.addEventListener('click', function () {
            filtroAgendamento = 'todos';
            btnTodos.classList.add('active');
            btnMeus.classList.remove('active');
            calendar.refetchEvents();
            renderAppointments(filter.value);
        });
    }

    const cachedData = {};

    async function fetchData(url) {
        // Adiciona o filtro na URL
        const urlComFiltro = url.includes('?') ? `${url}&filtro=${filtroAgendamento}` : `${url}?filtro=${filtroAgendamento}`;
        if (cachedData[urlComFiltro]) {
            return cachedData[urlComFiltro];
        }
        const response = await fetch(urlComFiltro);
        const data = await response.json();
        cachedData[urlComFiltro] = data;
        return data;
    }

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'pt-br',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay',
        },

        buttonText: {
            today: 'Hoje',
            month: 'Mês',
            week: 'Semana',
            day: 'Dia'
        },
        events: async function (fetchInfo, successCallback, failureCallback) {
            try {
                const data = await fetchData('/agenda/data');
                console.log('Agendamentos recebidos do backend:', data);
                if (Array.isArray(data)) {
                    const eventos = data.map((agendamento) => {
                        // Usa o nome do usuário logado já buscado
                        const nomeUsuario = usuarioLogado && usuarioLogado.nome_usuario ? usuarioLogado.nome_usuario : '';
                        const nomeEmpresa = agendamento.nome_empresa;
                        return {
                            id: agendamento.id,
                            title: `${agendamento.cliente_nome} -  ${agendamento.servico_nome}`,
                            start: `${agendamento.data}T${agendamento.horario}`,
                            allDay: false,
                            descricao: agendamento.descricao,
                            telefone: agendamento.telefone,
                            empresa: nomeEmpresa,
                            nome_usuario: nomeUsuario,  // Usa o nome do usuário logado
                            finalizado: agendamento.finalizado || false,
                            conta_receber: agendamento.conta_receber || false,
                            servico_preco: agendamento.servico_preco || 0
                        };
                    });

                    console.log('Eventos formatados para o calendário:', eventos);
                    successCallback(eventos);
                } else {
                    console.error('Dados recebidos não são um array:', data);
                    failureCallback('Erro nos dados recebidos');
                }
            } catch (error) {
                console.error('Erro ao buscar agendamentos:', error);
                failureCallback(error);
            }
        },

        eventMouseEnter: function (info) {
            const eventEl = info.el;
            eventEl.style.cursor = 'pointer';
        },
        eventMouseLeave: function (info) {
            const eventEl = info.el;
            eventEl.style.cursor = '';
        },
        eventClick: function (info) {
            if (!info.event.extendedProps.finalizado) {
                mostrarDetalhesAgendamento(info.event);
            } else {
                mostrarPopup('warning', 'Este agendamento já foi finalizado e não pode ser modificado.', 'Aviso');
            }
        },
        eventDidMount: function (info) {
            const eventEl = info.el;
            const now = new Date();

            if (info.event.start < now) {
                eventEl.style.backgroundColor = 'red';
                eventEl.style.color = 'white';
            }
            // Destacar agendamentos de contas a receber apenas com cor do texto (forçado)
            if (info.event.extendedProps.conta_receber) {
                eventEl.style.setProperty('color', 'orange', 'important');
                eventEl.style.fontWeight = 'bold';
            }
        }
    });

    calendar.render();

    async function renderAppointments(view) {
        try {
            const data = await fetchData('/agenda/data');
            // Obter data local correta usando Intl.DateTimeFormat
            const now = new Date();
            const localDate = new Intl.DateTimeFormat('pt-BR', {
                timeZone: 'America/Sao_Paulo',
                year: 'numeric',
                month: '2-digit',
                day: '2-digit'
            }).format(now);
            
            // Converter formato brasileiro (DD/MM/YYYY) para ISO (YYYY-MM-DD)
            const [day, month, year] = localDate.split('/');
            const today = `${year}-${month}-${day}`;
            
            let filteredAppointments;
    
            console.log('Dados recebidos:', data);
            console.log('Filtro aplicado:', view);
            console.log('Data atual (UTC):', now.toISOString().split('T')[0]);
            console.log('Data atual (Brasil):', today);
    
            if (view === 'day') {
                console.log('Filtrando para hoje:', today);
                filteredAppointments = data.filter(event => {
                    console.log('Comparando:', event.data, 'com', today);
                    return event.data === today;
                });
                console.log('Agendamentos de hoje encontrados:', filteredAppointments.length);
            } else if (view === 'week') {
                const todayDate = new Date(today + 'T00:00:00');
                const weekStart = new Date(todayDate);
                weekStart.setDate(todayDate.getDate() - todayDate.getDay());
                weekStart.setHours(0, 0, 0, 0);
    
                const weekEnd = new Date(weekStart);
                weekEnd.setDate(weekStart.getDate() + 6);
                weekEnd.setHours(23, 59, 59, 999);
    
                console.log('Filtrando para semana:', weekStart.toISOString().split('T')[0], 'até', weekEnd.toISOString().split('T')[0]);
                filteredAppointments = data.filter(event => {
                    const eventDate = new Date(event.data + 'T00:00:00');
                    const isInWeek = eventDate >= weekStart && eventDate <= weekEnd;
                    console.log('Evento:', event.data, 'está na semana?', isInWeek);
                    return isInWeek;
                });
                console.log('Agendamentos da semana encontrados:', filteredAppointments.length);
            } else if (view === 'month') {
                const todayDate = new Date(today + 'T00:00:00');
                const month = todayDate.getMonth();
                const year = todayDate.getFullYear();
                
                console.log('Filtrando para mês:', month + 1, '/', year);
                filteredAppointments = data.filter(event => {
                    const eventDate = new Date(event.data + 'T00:00:00');
                    const isInMonth = eventDate.getMonth() === month && eventDate.getFullYear() === year;
                    console.log('Evento:', event.data, 'está no mês?', isInMonth);
                    return isInMonth;
                });
                console.log('Agendamentos do mês encontrados:', filteredAppointments.length);
            }
    
            // Ordena os agendamentos por data e horário
            filteredAppointments.sort((a, b) => {
                const dateA = new Date(`${a.data}T${a.horario}`);
                const dateB = new Date(`${b.data}T${b.horario}`);
                return dateA - dateB; // Ordem crescente
            });
    
            if (filteredAppointments.length === 0) {
                // Exibe mensagem de ausência de agendamentos
                let noAppointmentsMessage;
                if (view === 'day') {
                    noAppointmentsMessage = 'Sem agendamentos para hoje.';
                } else if (view === 'week') {
                    noAppointmentsMessage = 'Sem agendamentos para esta semana.';
                } else if (view === 'month') {
                    noAppointmentsMessage = 'Sem agendamentos para este mês.';
                }
    
                appointmentList.innerHTML = `
                    <li class="no-appointments-message" style="text-align: center; margin-top: 20px; background-color: transparent; box-shadow: none;">
                        <strong>${noAppointmentsMessage}</strong>
                     <p style="font-size: 14px; margin-top: 5px;" display="none">Clique em "Novo Agendamento" para adicionar um agendamento.</p>

                     <img src="static/img/sem_agendamentos.png" alt="Sem agendamentos" style="max-width: 100%; max-height: 200px; display: block; margin: 0 auto;">
                    </li>
                `;
                return;
            }
    
            // Resolve todas as promessas de agendamentos
            const appointmentsHTML = await Promise.all(filteredAppointments.map(async (event) => {
                const eventDate = new Date(event.data + 'T00:00:00');
                const isPast = new Date(eventDate) < new Date(now);
                const isContaReceber = event.conta_receber || false;
    
                try {
                    const response = await fetch('/api/usuario/logado');
                    if (!response.ok) {
                        throw new Error('Erro ao buscar nome do usuário');
                    }
                    const data = await response.json();
                    const nomeUsuario = data.nome_usuario;
    
                    const linkWhatsApp = `https://wa.me/+55${event.telefone}?text=Olá, ${event.cliente_nome}. Sou ${nomeUsuario} da empresa ${event.nome_empresa} e gostaria de falar com você sobre o agendamento de: ${event.servico_nome} na data: ${eventDate.toLocaleDateString()} às ${event.horario}`;
    
                    // Define a cor de fundo baseada no status
                    let backgroundColor = 'transparent';
                    let textColor = 'black';
                    
                    if (isPast) {
                        backgroundColor = 'blanchedalmond';
                        textColor = 'red';
                    } else if (isContaReceber) {
                        backgroundColor = 'yellow';
                        textColor = 'black';
                    }
    
                    // Define o status e badge
                    let statusBadge = '';
                    let statusClass = '';
                    
                    if (event.status === 'cancelado') {
                        statusBadge = '<span class="status-badge status-cancelado">Cancelado</span>';
                        statusClass = 'cancelled';
                    } else if (event.status === 'finalizado') {
                        statusBadge = '<span class="status-badge status-finalizado">Finalizado</span>';
                        statusClass = 'completed';
                    } else {
                        statusBadge = '<span class="status-badge status-ativo">Ativo</span>';
                        statusClass = 'active';
                    }

                    return `
                    <li class="appointment-item ${statusClass}">
                        <div class="appointment-info">
                            <div class="appointment-header">
                                <strong>${event.cliente_nome}</strong>
                                ${statusBadge}
                            </div>
                            <div class="appointment-service">
                                <i class="bi bi-briefcase me-1"></i>${event.servico_nome}
                            </div>
                            <div class="appointment-datetime">
                                <i class="bi bi-calendar-event me-1"></i>${eventDate.toLocaleDateString('pt-BR')} às ${event.horario}
                            </div>
                            ${event.descricao ? `<div class="appointment-description"><i class="bi bi-chat-text me-1"></i>${event.descricao}</div>` : ''}
                            ${isContaReceber ? '<div class="appointment-payment"><i class="bi bi-currency-dollar me-1"></i>💰 Conta a Receber</div>' : ''}
                        </div>
                        <div class="button-group-2">
                            ${event.status !== 'cancelado' && event.status !== 'finalizado' ? `
                                <button class="btn btn-danger btn-cancelar" data-id="${event.id}">
                                    <i class="bi bi-x-circle me-1"></i>Cancelar
                                </button>
                                <button class="btn btn-success btn-finalizar" data-id="${event.id}" data-valor="${event.servico_preco || 0}">
                                    <i class="bi bi-check-circle me-1"></i>Finalizar
                                </button>
                            ` : ''}
                            <a class="btn btn-success btn-sm whatsapp-button d-flex align-items-center" target="_blank" href="${linkWhatsApp}">
                                <i class="bi bi-whatsapp me-1"></i>WhatsApp
                            </a>
                        </div>
                    </li>
                    `;
                } catch (error) {
                    console.error('Erro ao buscar nome do usuário:', error.message);
                    return ''; // Retorna uma string vazia em caso de erro
                }
            }));
    
            // Atualiza o HTML da lista de agendamentos com os eventos filtrados.
            appointmentList.innerHTML = appointmentsHTML.join('');
    
            document.querySelectorAll('.btn-cancelar').forEach(button => {
                button.addEventListener('click', function () {
                    const id = this.getAttribute('data-id');
                    cancelarAgendamento(id);
                });
            });
    
            document.querySelectorAll('.btn-finalizar').forEach(button => {
                button.addEventListener('click', function () {
                    const id = this.getAttribute('data-id');
                    const valorServico = parseFloat(this.getAttribute('data-valor')) || 0;
                    mostrarModalPagamento(id, valorServico);
                });
            });
    
        } catch (error) {
            console.error('Erro ao renderizar os agendamentos:', error);
        }
    }
    
    filter.addEventListener('change', () => {
        renderAppointments(filter.value);
    });
    
    renderAppointments('day');
    calendar.render();
    
});

// Exemplo usando localStorage (onde o nome do usuário foi salvo após o login)

async function mostrarDetalhesAgendamento(event) {
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');
    modalTitle.textContent = ` ${event.title}`;

    let extraMsg = '';
    let showBtns = true;
    if (event.extendedProps.conta_receber) {
        extraMsg = '<div class="alert alert-warning mt-3">Para dar baixa, utilize o módulo de Contas a Receber.</div>';
        showBtns = false;
    }

    // Formatar o valor do serviço
    const valorServico = event.extendedProps.servico_preco || 0;
    const valorFormatado = valorServico > 0 ? `R$ ${parseFloat(valorServico).toFixed(2).replace('.', ',')}` : 'Valor não informado';

    // Novo: Profissional responsável
    const nomeProfissional = event.extendedProps.nome_usuario ? event.extendedProps.nome_usuario : '';
    const profissionalHtml = nomeProfissional ? `<p><strong>Profissional:</strong> <span style="color: #007bff;">${nomeProfissional}</span></p>` : '';

    modalBody.innerHTML = `
    <p><strong>Cliente:</strong> ${event.title.split(' - ')[0]}</p>
    <p><strong>Serviço:</strong> ${event.title.split(' - ')[1]}</p>
    ${profissionalHtml}
    <p><strong>Valor:</strong> <span style="color: #28a745; font-weight: bold;">${valorFormatado}</span></p>
    <p><strong>Data:</strong> ${event.start.toLocaleDateString()}</p>
    <p><strong>Horário:</strong> ${event.start.toLocaleTimeString()}</p>
    <p><strong>Descrição:</strong> ${event.extendedProps.descricao || 'Sem descrição'}</p>
    <p><strong>Telefone:</strong> ${event.extendedProps.telefone}</p>
    ${event.extendedProps.conta_receber ? '<p><strong style="color: orange;">💰 Conta a Receber</strong></p>' : ''}
    <div class="button-group d-flex justify-content-end align-items-center mt-3">
        ${showBtns ? '<button class="btn btn-danger btn-cancelar me-2">Cancelar</button>' : ''}
        ${showBtns ? '<button class="btn btn-success btn-finalizar me-2">Finalizar</button>' : ''}
        <a class="btn btn-success btn-sm whatsapp-button d-flex align-items-center" target="_blank" id="btnEnviarMensagem">
            <i class="bi bi-whatsapp me-1"></i> Whatsapp
        </a>
    </div>
    ${extraMsg}
`;

    // Usa o nome do usuário logado já buscado
    const nomeUsuario = usuarioLogado && usuarioLogado.nome_usuario ? usuarioLogado.nome_usuario : '';
    const linkWhatsApp = `https://wa.me/+55${event.extendedProps.telefone}?text=Olá, ${event.title.split(' - ')[0]}. Sou ${nomeUsuario} da empresa ${event.extendedProps.empresa} e gostaria de falar com você sobre o agendamento de: ${event.title.split(' - ')[1]} na data: ${event.start.toLocaleDateString()} às ${event.start.toLocaleTimeString()} `;
    document.getElementById('btnEnviarMensagem').setAttribute('href', linkWhatsApp);

    const btnCancelar = document.querySelector('.btn-cancelar');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function () {
            cancelarAgendamento(event.id);
        });
    }

    const btnFinalizar = document.querySelector('.btn-finalizar');
    if (btnFinalizar) {
        btnFinalizar.addEventListener('click', function () {
            mostrarModalPagamento(event.id, valorServico);
        });
    }

    const modal = new bootstrap.Modal(document.getElementById('agendamentoDetalhesModal'));
    modal.show();
}

function mostrarModalPagamento(agendamentoId, valorServico = 0) {
    const modalPagamentoBody = document.getElementById('modal-pagamento-body');
    const modalPagamento = new bootstrap.Modal(document.getElementById('pagamentoModal'));

    modalPagamentoBody.innerHTML = `
            <form id="form-pagamento">
                <div class="mb-3">
                    <label for="valor-pagamento" class="form-label">Valor</label>
                    <input type="number" class="form-control" id="valor-pagamento" required value="${valorServico}" step="0.01">
                </div>
                <div class="mb-3">
                    <label for="meio-pagamento" class="form-label">Meio de Pagamento</label>
                    <select class="form-control" id="meio-pagamento" required>
                        <option value="Cartão de Crédito">Cartão de Crédito</option>
                        <option value="Cartão de Débito">Cartão de Débito</option>
                        <option value="Dinheiro">Dinheiro</option>
                        <option value="Pix">Pix</option>
                        <option value="Outro">sem custo</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-success">finalizar</button>
            </form>
        `;

    document.getElementById('form-pagamento').addEventListener('submit', function (e) {
        e.preventDefault();

        const valor = document.getElementById('valor-pagamento').value;
        const meioPagamento = document.getElementById('meio-pagamento').value;

        finalizarAgendamento(agendamentoId, valor, meioPagamento);
        modalPagamento.hide();
    });

    modalPagamento.show();
}

function finalizarAgendamento(agendamentoId, valor, meioPagamento) {
    mostrarCarregamento();
    fetch(`/api/agendamento/finalizar/${agendamentoId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            valor: parseFloat(valor),
            meio_pagamento: meioPagamento,
        }),
    })
        .then(response => response.json())
        .then(data => {
            esconderCarregamento();
            if (data.message) {
                // Mostra popup de sucesso com a mensagem do backend
                mostrarPopup('success', data.message, 'Sucesso!');
                // Configura o botão OK para fazer reload
                const confirmBtn = document.querySelector('#popup-success .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-success');
                    location.reload();
                };
            } else if (data.error) {
                // Mostra popup de erro com a mensagem do backend
                mostrarPopup('error', data.error, 'Erro');
                // Configura o botão OK para fazer reload
                const confirmBtn = document.querySelector('#popup-error .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-error');
                    location.reload();
                };
            } else {
                // Fallback para erro genérico
                mostrarPopup('error', 'Erro ao finalizar agendamento.', 'Erro');
                const confirmBtn = document.querySelector('#popup-error .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-error');
                    location.reload();
                };
            }
        })
        .catch(error => {
            esconderCarregamento();
            console.error('Erro:', error);
            mostrarPopup('error', 'Erro ao finalizar agendamento.', 'Erro');
            const confirmBtn = document.querySelector('#popup-error .popup-btn');
            confirmBtn.onclick = () => {
                fecharPopup('popup-error');
                location.reload();
            };
        });
}

function cancelarAgendamento(id) {
    mostrarConfirmacao("Tem certeza que deseja cancelar este agendamento?", () => {
        mostrarCarregamento();
        fetch(`/api/agendamento/${id}`, { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                esconderCarregamento();
                if (data.message) {
                    // Mostra popup de sucesso com a mensagem do backend
                    mostrarPopup('success', data.message, 'Sucesso!');
                    // Configura o botão OK para fazer reload
                    const confirmBtn = document.querySelector('#popup-success .popup-btn');
                    confirmBtn.onclick = () => {
                        fecharPopup('popup-success');
                        location.reload();
                    };
                } else if (data.error) {
                    // Mostra popup de erro com a mensagem do backend
                    mostrarPopup('error', data.error, 'Erro');
                    // Configura o botão OK para fazer reload
                    const confirmBtn = document.querySelector('#popup-error .popup-btn');
                    confirmBtn.onclick = () => {
                        fecharPopup('popup-error');
                        location.reload();
                    };
                } else {
                    // Fallback para erro genérico
                    mostrarPopup('error', 'Erro ao cancelar agendamento.', 'Erro');
                    const confirmBtn = document.querySelector('#popup-error .popup-btn');
                    confirmBtn.onclick = () => {
                        fecharPopup('popup-error');
                        location.reload();
                    };
                }
            })
            .catch(error => {
                esconderCarregamento();
                console.error('Erro ao processar a solicitação:', error);
                mostrarPopup('error', 'Erro ao cancelar agendamento.', 'Erro');
                const confirmBtn = document.querySelector('#popup-error .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-error');
                    location.reload();
                };
            });
    });
}

function carregarDados() {
    fetch('/api/clientes')
        .then(response => response.json())
        .then(data => {
            const clienteSelect = document.getElementById('cliente-agendamento');
            data.forEach(cliente => {
                const option = document.createElement('option');
                option.value = cliente.id;
                option.textContent = cliente.nome_cliente;
                clienteSelect.appendChild(option);
            });
        });

    fetch('/api/usuarios')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro na requisição: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            const usuarioSelect = document.getElementById('usuario-agendamento');
            if (usuarioSelect) {
                data.forEach(usuario => {
                    const option = document.createElement('option');
                    option.value = usuario.id;
                    option.textContent = usuario.nome_usuario;
                    usuarioSelect.appendChild(option);
                });
            } else {
                console.error('Elemento select com ID "usuario-agendamento" não encontrado.');
            }
        })
        .catch(error => {
            console.error('Erro ao buscar ou processar os usuários:', error.message);
        });

    fetch('/api/servicos')
        .then(response => response.json())
        .then(data => {
            const servicoSelect = document.getElementById('servico-agendamento');
            data.forEach(servico => {
                const option = document.createElement('option');
                option.value = servico.id;
                option.textContent = servico.nome_servico;
                servicoSelect.appendChild(option);
            });
        });
}

document.getElementById('form-agendamento').addEventListener('submit', function (e) {
    e.preventDefault();

    const cliente = document.getElementById('cliente-agendamento').value;
    const usuario = document.getElementById('usuario-agendamento').value;
    const servico = document.getElementById('servico-agendamento').value;
    const data = document.getElementById('data-agendamento').value;
    const horario = document.getElementById('hora-agendamento').value;
    const descricao = document.getElementById('descricao-agendamento').value;

    const dadosAgendamento = {
        cliente_id: cliente,
        usuario_id: usuario,
        servico_id: servico,
        data: data,
        horario: horario,
        descricao: descricao
    };

    mostrarCarregamento();
    fetch('/api/agendar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dadosAgendamento)
    })
        .then(response => response.json())
        .then(data => {
            esconderCarregamento();
            if (data.message) {
                // Mostra popup de sucesso com a mensagem do backend
                mostrarPopup('success', data.message, 'Sucesso!');
                // Configura o botão OK para fazer reload
                const confirmBtn = document.querySelector('#popup-success .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-success');
                    location.reload();
                };
            } else if (data.error) {
                // Mostra popup de erro com a mensagem do backend
                mostrarPopup('error', data.error, 'Erro');
                // Configura o botão OK para fazer reload
                const confirmBtn = document.querySelector('#popup-error .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-error');
                    location.reload();
                };
            } else {
                // Fallback para erro genérico
                mostrarPopup('error', 'Erro ao criar agendamento.', 'Erro');
                const confirmBtn = document.querySelector('#popup-error .popup-btn');
                confirmBtn.onclick = () => {
                    fecharPopup('popup-error');
                    location.reload();
                };
            }
        })
        .catch(error => {
            esconderCarregamento();
            console.error('Erro ao enviar os dados do agendamento:', error);
            mostrarPopup('error', 'Erro ao criar agendamento.', 'Erro');
            const confirmBtn = document.querySelector('#popup-error .popup-btn');
            confirmBtn.onclick = () => {
                fecharPopup('popup-error');
                location.reload();
            };
        });
});

carregarDados();