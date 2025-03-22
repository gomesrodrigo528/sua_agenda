document.addEventListener('DOMContentLoaded', function () {
    const calendarEl = document.getElementById('calendar');
    const listContainer = document.getElementById('list-container');
    const appointmentList = document.getElementById('appointment-list');
    const filter = document.getElementById('filter');

    const cachedData = {};

    async function fetchData(url) {
        if (cachedData[url]) {
            return cachedData[url];
        }
        const response = await fetch(url);
        const data = await response.json();
        cachedData[url] = data;
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
                if (Array.isArray(data)) {
                    const eventos = await Promise.all(data.map(async (agendamento) => {
                        const usuarioResponse = await fetch('/api/usuario/logado'); // Aqui você busca os dados do usuário logado
                        const usuarioData = await usuarioResponse.json();
                        const nomeUsuario = usuarioData.nome_usuario; // Pegue o nome do usuário logado
                        const nomeEmpresa = agendamento.nome_empresa; // A empresa já está sendo retornada no agendamento

                        return {
                            id: agendamento.id,
                            title: `${agendamento.cliente_nome} -  ${agendamento.servico_nome}`,
                            start: `${agendamento.data}T${agendamento.horario}`,
                            allDay: false,
                            descricao: agendamento.descricao,
                            telefone: agendamento.telefone,
                            empresa: nomeEmpresa,
                            nome_usuario: nomeUsuario,  // Adiciona o nome do usuário ao evento
                            finalizado: agendamento.finalizado || false
                        };
                    }));

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
                alert('Este agendamento já foi finalizado e não pode ser modificado.');
            }
        },
        eventDidMount: function (info) {
            const eventEl = info.el;
            const now = new Date();

            if (info.event.start < now) {
                eventEl.style.backgroundColor = 'red';
                eventEl.style.color = 'white';
            }
        }
    });

    calendar.render();

    async function renderAppointments(view) {
        try {
            const data = await fetchData('/agenda/data');
            const now = new Date();
            let filteredAppointments;
    
            if (view === 'day') {
                const today = now.toISOString().split('T')[0];
                filteredAppointments = data.filter(event => event.data === today);
            } else if (view === 'week') {
                const weekStart = new Date(now);
                weekStart.setDate(now.getDate() - now.getDay());
                weekStart.setHours(0, 0, 0, 0);
    
                const weekEnd = new Date(weekStart);
                weekEnd.setDate(weekStart.getDate() + 6);
    
                filteredAppointments = data.filter(event => {
                    const eventDate = new Date(event.data + 'T00:00:00');
                    return eventDate >= weekStart && eventDate <= weekEnd;
                });
            } else if (view === 'month') {
                const month = now.getMonth();
                filteredAppointments = data.filter(event => {
                    const eventDate = new Date(event.data + 'T00:00:00');
                    return eventDate.getMonth() === month && eventDate.getFullYear() === now.getFullYear();
                });
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
    
                try {
                    const response = await fetch('/api/usuario/logado');
                    if (!response.ok) {
                        throw new Error('Erro ao buscar nome do usuário');
                    }
                    const data = await response.json();
                    const nomeUsuario = data.nome_usuario;
    
                    const linkWhatsApp = `https://wa.me/+55${event.telefone}?text=Olá, ${event.cliente_nome}. Sou ${nomeUsuario} da empresa ${event.nome_empresa} e gostaria de falar com você sobre o agendamento de: ${event.servico_nome} na data: ${eventDate.toLocaleDateString()} às ${event.horario}`;
    
                    return `
                    <div class="appointment-details">
                        <li class="appointment-item" style="background-color: ${isPast ? 'blanchedalmond' : 'transparent'}; color: ${isPast ? 'red' : 'black'}; margin-top: 20px;">
                            <div>
                                <strong>${event.cliente_nome} - ${event.servico_nome}</strong> <br>
                                <span><strong>Data:</strong> ${eventDate.toLocaleDateString()} às ${event.horario}</span>
                            </div>
                            <div class="button-group-2">
                                <button class="btn btn-danger btn-cancelar" data-id="${event.id}">Cancelar</button>
                                <button class="btn btn-success btn-finalizar" data-id="${event.id}">Finalizar</button>
                                <a class="btn btn-success btn-sm whatsapp-button d-flex align-items-center" target="_blank" href="${linkWhatsApp}">
                                    <i class="bi bi-whatsapp me-1"></i> Whatsapp
                                </a>
                            </div>
                        </li>
                    </div>
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
                    mostrarModalPagamento(id);
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

    modalBody.innerHTML = `
    <p><strong>Cliente:</strong> ${event.title.split(' - ')[0]}</p>
    <p><strong>Serviço:</strong> ${event.title.split(' - ')[1]}</p>
    <p><strong>Data:</strong> ${event.start.toLocaleDateString()}</p>
    <p><strong>Horário:</strong> ${event.start.toLocaleTimeString()}</p>
    <p><strong>Descrição:</strong> ${event.extendedProps.descricao || 'Sem descrição'}</p>
    <p><strong>Telefone:</strong> ${event.extendedProps.telefone}</p>
    <div class="button-group d-flex justify-content-end align-items-center mt-3">
        <button class="btn btn-danger btn-cancelar me-2">Cancelar</button>
        <button class="btn btn-success btn-finalizar me-2">Finalizar</button>
        <a class="btn btn-success btn-sm whatsapp-button d-flex align-items-center" target="_blank" id="btnEnviarMensagem">
            <i class="bi bi-whatsapp me-1"></i> Whatsapp
        </a>
    </div>

    
`;


    try {
        const response = await fetch('/api/usuario/logado');
        if (!response.ok) {
            throw new Error('Erro ao buscar nome do usuário');
        }
        const data = await response.json();
        if (data && data.nome_usuario) {
            const nomeUsuario = data.nome_usuario;
            const linkWhatsApp = `https://wa.me/+55${event.extendedProps.telefone}?text=Olá, ${event.title.split(' - ')[0]}. Sou ${nomeUsuario} da empresa ${event.extendedProps.empresa} e gostaria de falar com vocé. sobre o agendamento de: ${event.title.split(' - ')[1]} na data: ${event.start.toLocaleDateString()} às ${event.start.toLocaleTimeString()} `;
            document.getElementById('btnEnviarMensagem').setAttribute('href', linkWhatsApp);
        }
    } catch (error) {
        console.error('Erro ao buscar nome do usuário:', error.message);
    }



    const btnCancelar = document.querySelector('.btn-cancelar');
    if (btnCancelar) {
        btnCancelar.addEventListener('click', function () {
            cancelarAgendamento(event.id);
        });
    }

    const btnFinalizar = document.querySelector('.btn-finalizar');
    if (btnFinalizar) {
        btnFinalizar.addEventListener('click', function () {
            mostrarModalPagamento(event.id);
        });
    }

    const modal = new bootstrap.Modal(document.getElementById('agendamentoDetalhesModal'));
    modal.show();
}

function mostrarModalPagamento(agendamentoId) {
    const modalPagamentoBody = document.getElementById('modal-pagamento-body');
    const modalPagamento = new bootstrap.Modal(document.getElementById('pagamentoModal'));

    modalPagamentoBody.innerHTML = `
            <form id="form-pagamento">
                <div class="mb-3">
                    <label for="valor-pagamento" class="form-label">Valor</label>
                    <input type="number" class="form-control" id="valor-pagamento" required>
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
                alert('Agendamento finalizado com sucesso!');
                location.reload();
            } else {
                alert('Erro ao finalizar agendamento.');
            }
        })
        .catch(error => {
            esconderCarregamento();
            console.error('Erro:', error);
        });
}

function cancelarAgendamento(id) {
    if (!confirm("Tem certeza que deseja cancelar este agendamento?")) return;

    mostrarCarregamento();
    fetch(`/api/agendamento/${id}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(data => {
            esconderCarregamento();
            if (data.message) {
                location.reload();
            } else {
                alert('Erro ao cancelar agendamento.');
            }
        })
        .catch(error => {
            esconderCarregamento();
            console.error('Erro ao processar a solicitação:', error);
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
                location.reload();
            } else {
                alert('Erro ao criar agendamento.');
            }
        })
        .catch(error => {
            esconderCarregamento();
            console.error('Erro ao enviar os dados do agendamento:', error);
        });
});






function mostrarCarregamento() {
    document.getElementById('loading-screen').style.display = 'flex';
}
function esconderCarregamento() {
    document.getElementById('loading-screen').style.display = 'none';
}
carregarDados();