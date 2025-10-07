// Funcionalidades de busca para o modal de agendamento
let timeoutClientes = null;
let timeoutServicos = null;

// Função para fechar o modal de agendamento
function fecharModalAgendamento() {
    const modal = bootstrap.Modal.getInstance(document.getElementById('agendamentoModal'));
    if (modal) {
        modal.hide();
    }
    // Limpar formulário
    document.getElementById('form-agendamento').reset();
    document.getElementById('cliente-id').value = '';
    document.getElementById('servico-id').value = '';
    document.getElementById('cliente-dropdown').style.display = 'none';
    document.getElementById('servico-dropdown').style.display = 'none';
}

// Função para buscar clientes
async function buscarClientes(termo) {
    if (!termo || termo.length < 2) {
        document.getElementById('cliente-dropdown').style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/clientes?busca=${encodeURIComponent(termo)}`);
        const clientes = await response.json();
        
        const dropdown = document.getElementById('cliente-dropdown');
        dropdown.innerHTML = '';
        
        if (clientes.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item text-muted">Nenhum cliente encontrado</div>';
        } else {
            clientes.forEach(cliente => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${cliente.nome_cliente}</strong>
                            ${cliente.telefone ? `<br><small class="text-muted">${cliente.telefone}</small>` : ''}
                        </div>
                        <i class="bi bi-person-circle text-primary"></i>
                    </div>
                `;
                
                item.addEventListener('click', () => {
                    document.getElementById('cliente-busca').value = cliente.nome_cliente;
                    document.getElementById('cliente-id').value = cliente.id;
                    dropdown.style.display = 'none';
                });
                
                dropdown.appendChild(item);
            });
        }
        
        dropdown.style.display = 'block';
    } catch (error) {
        console.error('Erro ao buscar clientes:', error);
        document.getElementById('cliente-dropdown').innerHTML = '<div class="dropdown-item text-danger">Erro ao buscar clientes</div>';
        document.getElementById('cliente-dropdown').style.display = 'block';
    }
}

// Função para buscar serviços
async function buscarServicos(termo) {
    if (!termo || termo.length < 2) {
        document.getElementById('servico-dropdown').style.display = 'none';
        return;
    }

    try {
        const response = await fetch(`/api/servicos?busca=${encodeURIComponent(termo)}`);
        const servicos = await response.json();
        
        const dropdown = document.getElementById('servico-dropdown');
        dropdown.innerHTML = '';
        
        if (servicos.length === 0) {
            dropdown.innerHTML = '<div class="dropdown-item text-muted">Nenhum serviço encontrado</div>';
        } else {
            servicos.forEach(servico => {
                const item = document.createElement('div');
                item.className = 'dropdown-item';
                item.style.cursor = 'pointer';
                item.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <strong>${servico.nome_servico}</strong>
                            ${servico.preco ? `<br><small class="text-success">R$ ${parseFloat(servico.preco).toFixed(2)}</small>` : ''}
                        </div>
                        <i class="bi bi-briefcase text-primary"></i>
                    </div>
                `;
                
                item.addEventListener('click', () => {
                    document.getElementById('servico-busca').value = servico.nome_servico;
                    document.getElementById('servico-id').value = servico.id;
                    dropdown.style.display = 'none';
                });
                
                dropdown.appendChild(item);
            });
        }
        
        dropdown.style.display = 'block';
    } catch (error) {
        console.error('Erro ao buscar serviços:', error);
        document.getElementById('servico-dropdown').innerHTML = '<div class="dropdown-item text-danger">Erro ao buscar serviços</div>';
        document.getElementById('servico-dropdown').style.display = 'block';
    }
}

// Event listeners para os campos de busca
document.addEventListener('DOMContentLoaded', function() {
    // Campo de busca de clientes
    const clienteBusca = document.getElementById('cliente-busca');
    if (clienteBusca) {
        clienteBusca.addEventListener('input', function() {
            clearTimeout(timeoutClientes);
            timeoutClientes = setTimeout(() => {
                buscarClientes(this.value);
            }, 300);
        });

        // Fechar dropdown quando clicar fora
        clienteBusca.addEventListener('blur', function() {
            setTimeout(() => {
                document.getElementById('cliente-dropdown').style.display = 'none';
            }, 200);
        });

        // Mostrar dropdown quando focar
        clienteBusca.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                buscarClientes(this.value);
            }
        });
    }

    // Campo de busca de serviços
    const servicoBusca = document.getElementById('servico-busca');
    if (servicoBusca) {
        servicoBusca.addEventListener('input', function() {
            clearTimeout(timeoutServicos);
            timeoutServicos = setTimeout(() => {
                buscarServicos(this.value);
            }, 300);
        });

        // Fechar dropdown quando clicar fora
        servicoBusca.addEventListener('blur', function() {
            setTimeout(() => {
                document.getElementById('servico-dropdown').style.display = 'none';
            }, 200);
        });

        // Mostrar dropdown quando focar
        servicoBusca.addEventListener('focus', function() {
            if (this.value.length >= 2) {
                buscarServicos(this.value);
            }
        });
    }

    // Carregar usuários quando o modal abrir
    const modalAgendamento = document.getElementById('agendamentoModal');
    if (modalAgendamento) {
        modalAgendamento.addEventListener('show.bs.modal', function() {
            carregarUsuarios();
        });
    }
});

// Função para carregar usuários
async function carregarUsuarios() {
    try {
        const response = await fetch('/api/usuarios');
        const usuarios = await response.json();
        
        const usuarioSelect = document.getElementById('usuario-agendamento');
        usuarioSelect.innerHTML = '<option value="">Selecione um profissional</option>';
        
        usuarios.forEach(usuario => {
            const option = document.createElement('option');
            option.value = usuario.id;
            option.textContent = usuario.nome_usuario;
            usuarioSelect.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar usuários:', error);
    }
}

// Atualizar função de envio do formulário
document.addEventListener('DOMContentLoaded', function() {
    const formAgendamento = document.getElementById('form-agendamento');
    if (formAgendamento) {
        formAgendamento.addEventListener('submit', function(e) {
            e.preventDefault();

            // Validação dos campos obrigatórios
            const clienteId = document.getElementById('cliente-id').value;
            const servicoId = document.getElementById('servico-id').value;
            const usuarioId = document.getElementById('usuario-agendamento').value;
            const data = document.getElementById('data-agendamento').value;
            const horario = document.getElementById('hora-agendamento').value;

            if (!clienteId) {
                mostrarMensagem('Por favor, selecione um cliente.', 'Atenção');
                return;
            }

            if (!servicoId) {
                mostrarMensagem('Por favor, selecione um serviço.', 'Atenção');
                return;
            }

            if (!usuarioId) {
                mostrarMensagem('Por favor, selecione um profissional.', 'Atenção');
                return;
            }

            if (!data) {
                mostrarMensagem('Por favor, selecione uma data.', 'Atenção');
                return;
            }

            if (!horario) {
                mostrarMensagem('Por favor, selecione um horário.', 'Atenção');
                return;
            }

            const dadosAgendamento = {
                cliente_id: clienteId,
                usuario_id: usuarioId,
                servico_id: servicoId,
                data: data,
                horario: horario,
                descricao: document.getElementById('descricao-agendamento').value
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
                    mostrarPopup('success', data.message, 'Sucesso!');
                    const confirmBtn = document.querySelector('#popup-success .popup-btn');
                    confirmBtn.onclick = () => {
                        fecharPopup('popup-success');
                        fecharModalAgendamento();
                        location.reload();
                    };
                } else if (data.error) {
                    mostrarPopup('error', data.error, 'Erro');
                    const confirmBtn = document.querySelector('#popup-error .popup-btn');
                    confirmBtn.onclick = () => {
                        fecharPopup('popup-error');
                    };
                }
            })
            .catch(error => {
                esconderCarregamento();
                console.error('Erro:', error);
                mostrarPopup('error', 'Erro ao realizar agendamento. Tente novamente.', 'Erro');
            });
        });
    }
});
