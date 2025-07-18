// Variável global para armazenar o ID da empresa atual
let empresaIdAtual = null;

// Variável global para o carrinho
let carrinho = [];

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

// Variável para controlar se já foi mostrado um popup
let popupJaMostrado = false;

// Função para substituir alert
function mostrarAlerta(mensagem, tipo = 'warning') {
    if (popupJaMostrado) {
        console.log('Popup já foi mostrado, ignorando chamada duplicada');
        return;
    }
    
    popupJaMostrado = true;
    console.log(`Mostrando popup: ${tipo} - ${mensagem}`);
    
    mostrarPopup(tipo, mensagem);
    
    // Resetar após 3 segundos
    setTimeout(() => {
        popupJaMostrado = false;
    }, 3000);
}

// Função para substituir confirm
function mostrarConfirmacao(mensagem, callback) {
    mostrarPopup('confirm', mensagem, 'Confirmar', callback);
}

// Função para configurar validação de data
function configurarValidacaoData() {
    const dataInput = document.getElementById('data-input');
    if (dataInput) {
        // Define a data mínima como hoje
        const hoje = new Date().toISOString().split('T')[0];
        dataInput.setAttribute('min', hoje);
        
        // Adiciona validação adicional
        dataInput.addEventListener('change', function() {
            const dataSelecionada = new Date(this.value);
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0); // Remove as horas para comparar apenas a data
            
            if (dataSelecionada < hoje) {
                mostrarAlerta('Não é possível selecionar uma data anterior a hoje.', 'warning');
                this.value = ''; // Limpa o campo
                // Limpa os horários se houver
                const containerHorarios = document.getElementById('horarios-disponiveis');
                if (containerHorarios) {
                    containerHorarios.innerHTML = '';
                }
                const horarioSelecionado = document.getElementById('horario-selecionado');
                if (horarioSelecionado) {
                    horarioSelecionado.innerHTML = '';
                }
            } else if (dataSelecionada.getTime() === hoje.getTime()) {
                // Se for hoje, mostrar aviso sobre horários disponíveis
                mostrarAlerta('Para agendamentos no mesmo dia, apenas horários futuros estarão disponíveis.', 'warning');
            }
        });
    }
}

// Event listeners para fechar o modal
document.addEventListener('DOMContentLoaded', function() {
    const fecharModalBtns = document.querySelectorAll('#fechar-modal');
    fecharModalBtns.forEach(btn => {
        btn.addEventListener('click', function () {
            document.getElementById('modal-agendamento').style.display = 'none';
            document.getElementById('empresas-lista').style.display = 'block';
            document.getElementById('search-container').style.display = 'block';
            // Limpar formulário
            document.getElementById('form-agendamento').reset();
            document.getElementById('horarios-disponiveis').innerHTML = '';
            document.getElementById('horario-selecionado').innerHTML = '';
        });
    });
});

document.addEventListener('DOMContentLoaded', function () {
    esconderCarregamento(); // Garante que a tela de carregamento estará oculta ao carregar a página
    preencherDadosCliente(); // Preenche os campos com dados dos cookies se disponível
    configurarValidacaoData(); // Configura a validação de data
    verificarSincronizacaoDados(); // Verifica se os dados precisam ser sincronizados
});

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
    menuToggle.addEventListener('click', openSidebar);
    sidebarToggle.addEventListener('click', closeSidebar);
    sidebarOverlay.addEventListener('click', closeSidebar);

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

// Função para preencher dados do cliente nos campos do formulário
function preencherDadosCliente() {
    const cliente = getClienteInfo();
    if (cliente.nome) {
        const nomeField = document.getElementById('nome-cliente');
        if (nomeField) {
            nomeField.value = cliente.nome;
            nomeField.readOnly = true;
        }
    }
    if (cliente.email) {
        const emailField = document.getElementById('email-cliente');
        if (emailField) {
            emailField.value = cliente.email;
            emailField.readOnly = true;
        }
    }
}

// Função para verificar e sincronizar dados do cliente
async function verificarSincronizacaoDados() {
    try {
        // Verificar se há dados nos cookies
        const clienteId = getCookie('cliente_id');
        const clienteName = getCookie('cliente_name');
        const clienteEmail = getCookie('cliente_email');
        const clienteTelefone = getCookie('cliente_telefone');
        
        if (!clienteId || !clienteName || !clienteEmail || !clienteTelefone) {
            console.log('Dados do cliente incompletos nos cookies');
            return;
        }
        
        // Tentar sincronizar dados
        const response = await fetch('/api/sincronizar-dados-cliente', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            if (result.success && result.mudancas && result.mudancas.length > 0) {
                console.log('Dados sincronizados:', result.mudancas);
                // Sincronização silenciosa - sem mostrar mensagem para o usuário
            }
        } else {
            console.log('Erro ao sincronizar dados do cliente');
        }
        
    } catch (error) {
        console.error('Erro na verificação de sincronização:', error);
    }
}

async function carregarDetalhesEmpresa(empresaId, modoSPA = false) {
    try {
        // Faz a requisição para buscar os detalhes da empresa
        const response = await axios.get(`/api/empresa/${empresaId}`);
        const empresa = response.data; // Obtém os dados da empresa
        empresaIdAtual = empresaId;

        // Garantir que os valores booleanos sejam tratados corretamente
        const estacionamento = empresa.estacionamento ? 'Disponível' : null;
        const wifi = empresa.wifi ? 'Disponível' : null;
        const kids = empresa.kids ? 'Permitido' : null;
        const acessibilidade = empresa.acessibilidade ? 'Disponível' : null;
        const endereco = empresa.endereco && empresa.endereco.trim() ? empresa.endereco : 'Endereço não informado';

        // Atualiza o conteúdo da div com as informações da empresa
        const divInfo = document.getElementById('informacoes-empresa');
        if (!divInfo) {
            console.error("Elemento com id 'informacoes-empresa' não encontrado no DOM.");
            mostrarAlerta("Erro interno: elemento de informações da empresa não encontrado na página.", 'error');
            return;
        }
        divInfo.innerHTML = `
        <div class="empresa-info">
        <img src="${empresa.logo}" alt="Logo da ${empresa.nome_empresa}" class="logo-descricao">
        <h3 class="nome-empresa">${empresa.nome_empresa}</h3>
        <p class="descricao"> ${empresa.descricao}</p>
        <p class="horario"><strong>Horário de funcionamento:</strong> ${empresa.horario}</p>
        ${endereco ? '<div class="endereco-container"><i class="fas fa-map-marker-alt"></i> ' + empresa.endereco +' </div>' : ''}
    
            <div class="comodidades-container">
                ${wifi ? `<div class="botao-neumorphism">
                            <i class="fas fa-wifi"></i> 
                            <span>Wi-Fi Disponível</span>
                          </div>` : ''}
                
                ${estacionamento ? `<div class="botao-neumorphism">
                            <i class="fas fa-car"></i> 
                            <span>Estacionamento Disponível</span>
                          </div>` : ''}
                
                ${kids ? `<div class="botao-neumorphism">
                            <i class="fas fa-child"></i> 
                            <span>Atende Crianças</span>
                          </div>` : ''}
                
                ${acessibilidade ? `<div class="botao-neumorphism">
                            <i class="fas fa-wheelchair"></i> 
                            <span>Acessibilidade Disponível</span>
                          </div>` : ''}
                          </div>
        </div>
        `;
        // Se for modo SPA, adiciona os botões extras
        if (modoSPA) {
            divInfo.innerHTML += `
                <div class="botoes-detalhes-empresa" style="margin-top: 2rem; display: flex; gap: 1rem;">
                    <button class="btn btn-primary" onclick="abrirModalAgendamento(${empresa.id})">Agendar</button>
                    <button class="btn btn-success" onclick="verProdutosEmpresa(${empresa.id})">Ver Produtos</button>
                    <button class="btn btn-secondary" onclick="voltarParaListaEmpresas()">Voltar</button>
                </div>
            `;
        }
        divInfo.style.display = 'block';
    } catch (error) {
        console.error('Erro ao carregar detalhes da empresa:', error);
        let msg = 'Erro ao carregar detalhes da empresa.';
        if (error.response && error.response.data && error.response.data.error) {
            msg += '\n' + error.response.data.error;
        }
        mostrarAlerta(msg, 'error');
    }
}



document.getElementById('search-bar').addEventListener('input', function (event) {
    const nomeEmpresa = event.target.value.trim();
    const urlParams = new URLSearchParams(window.location.search);

    if (nomeEmpresa) {
        urlParams.set('nome_empresa', nomeEmpresa);
    } else {
        urlParams.delete('nome_empresa');
    }

    // Mantém a cidade na URL caso já esteja definida
    const cidadeAtual = urlParams.get('cidade') || '';
    if (cidadeAtual) {
        urlParams.set('cidade', cidadeAtual);
    }

    window.history.pushState({}, '', `${window.location.pathname}?${urlParams}`);
    carregarEmpresas();
});


async function carregarEmpresas() {
    try {
        const urlParams = new URLSearchParams(window.location.search);
        const nomeEmpresa = urlParams.get('nome_empresa') || '';
        const cidade = urlParams.get('cidade') || '';  // Adicionando cidade

        const response = await axios.get('/api/empresas', {
            params: {
                nome_empresa: nomeEmpresa,
                cidade: cidade  // Inclui a cidade na requisição
            }
        });

        const empresas = response.data;
        const lista = document.getElementById('empresas-lista');

        lista.innerHTML = '';  // Limpa a lista antes de adicionar novos itens

        if (!empresas || empresas.length === 0) {
            lista.innerHTML = '<p>Nenhuma empresa encontrada.</p>';
            return;
        }

        empresas.forEach(empresa => {
            const item = document.createElement('div');
            item.classList.add('card');
            item.dataset.nomeEmpresa = empresa.nome_empresa.toLowerCase();

            item.innerHTML = `
                <div class="card-body">
                    <img src="${empresa.logo}" alt="Logo" class="logo">
                    <div class="card-text">
                        <h3 class="card-title">${empresa.nome_empresa}</h3>
                        <p class="card-text">${empresa.descricao}</p>
                        <button class="btn btn-info btn-ver-mais" onclick="verMaisEmpresa(${empresa.id})">Ver Mais</button>
                    </div>
                </div>
            `;

            lista.appendChild(item);
        });
    } catch (error) {
        console.error('Erro ao carregar empresas:', error);
        mostrarAlerta('Erro ao carregar empresas. Tente novamente mais tarde.', 'error');
    }
}

// Chama a função para carregar as empresas ao carregar a página (isso vai considerar a URL também)
window.onload = function () {
    carregarEmpresas();
};


async function carregarFuncionarios(empresaId) {
    try {
        const response = await axios.get(`/api/usuarios/${empresaId}`);
        const funcionarios = response.data;
        const selectUsuarios = document.getElementById('profissional-select');

        selectUsuarios.innerHTML = '<option value="">Selecione o Profissional</option>';

        if (!funcionarios || funcionarios.length === 0) {
            selectUsuarios.innerHTML = '<option value="">Nenhum Profissional disponível</option>';
            return;
        }

        funcionarios.forEach(funcionario => {
            const option = document.createElement('option');
            option.value = funcionario.id;
            option.textContent = funcionario.nome_usuario;
            selectUsuarios.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar funcionários:', error);
        alert('Erro ao carregar funcionários. Tente novamente mais tarde.');
    }
}

async function carregarUsuarioResponsavel() {
    const servicoId = document.getElementById('servico-select').value;

    if (!servicoId) {
        // Limpa a lista de profissionais se nenhum serviço estiver selecionado
        document.getElementById('profissional-select').innerHTML = '<option value="">Selecione o Profissional</option>';
        return;
    }

    try {
        // Faz uma chamada para buscar o serviço específico pelo ID
        const response = await axios.get(`/api/servicos/detalhes/${servicoId}?empresa_id=${empresaIdAtual}`);
        const servico = response.data;

        const selectUsuarios = document.getElementById('profissional-select');
        selectUsuarios.innerHTML = '<option value="">Selecione o Profissional</option>';

        if (servico.id_usuario) {
            // Se o serviço tem um usuário específico
            const option = document.createElement('option');
            option.value = servico.id_usuario;
            option.textContent = servico.usuarios.nome_usuario;
            selectUsuarios.appendChild(option);
        } else if (servico.usuarios && Array.isArray(servico.usuarios)) {
            // Se o serviço não tem usuário específico, mostra todos os usuários da empresa
            servico.usuarios.forEach(usuario => {
                const option = document.createElement('option');
                option.value = usuario.id;
                option.textContent = usuario.nome_usuario;
                selectUsuarios.appendChild(option);
            });
        } else {
            selectUsuarios.innerHTML = '<option value="">Nenhum Profissional encontrado</option>';
        }
    } catch (error) {
        console.error('Erro ao carregar o usuário responsável:', error);
        alert('Erro ao carregar o profissional responsável. Tente novamente mais tarde.');
    }
}


async function carregarServicos(empresaId) {
    try {
        const response = await axios.get(`/api/servicos/${empresaId}`);
        const servicos = response.data;
        const selectServicos = document.querySelector('select[name="servico_id"]');

        selectServicos.innerHTML = '<option value="">Selecione o Serviço</option>';

        if (!servicos || servicos.length === 0) {
            selectServicos.innerHTML = '<option value="">Nenhum serviço disponível</option>';
            return;
        }

        servicos.forEach(servico => {
            const option = document.createElement('option');
            option.value = servico.id;
            option.textContent = `${servico.nome_servico} - R$ ${servico.preco.toFixed(2)}`;
            selectServicos.appendChild(option);
        });
    } catch (error) {
        console.error('Erro ao carregar serviços:', error);
        alert('Erro ao carregar serviços. Tente novamente mais tarde.');
    }
}

async function carregarHorariosDisponiveis(event) {
    const usuarioId = document.getElementById('profissional-select').value;
    const data = document.getElementById('data-input').value;

    if (!usuarioId || !data) {
        return;
    }

    try {
        const response = await axios.get(`/api/agenda/data?usuario_id=${usuarioId}&data=${data}`);
        const horariosDisponiveis = response.data.horarios_disponiveis;
        const containerHorarios = document.getElementById('horarios-disponiveis');

        containerHorarios.innerHTML = '';

        if (!horariosDisponiveis || horariosDisponiveis.length === 0) {
            const hoje = new Date().toISOString().split('T')[0];
            const dataSelecionada = document.getElementById('data-input').value;
            
            if (dataSelecionada === hoje) {
                containerHorarios.innerHTML = '<p style="color: #ffc107; text-align: center; padding: 20px;">Nenhum horário disponível para hoje. Tente selecionar outra data.</p>';
            } else {
                containerHorarios.innerHTML = '<p style="color: #ccc; text-align: center; padding: 20px;">Nenhum horário disponível para esta data.</p>';
            }
            return;
        }

        horariosDisponiveis.forEach(horario => {
            const botaoHorario = document.createElement('button');
            botaoHorario.classList.add('time-slot');
            botaoHorario.textContent = horario;
            botaoHorario.onclick = () => selecionarHorario(horario);
            containerHorarios.appendChild(botaoHorario);
        });
    } catch (err) {
        console.error('Erro ao buscar horários disponíveis:', err);
        alert(err.response?.data?.error || 'Erro ao carregar horários disponíveis.');
    }
}

// Event listeners duplicados - comentados para evitar conflitos
// document.querySelector('input[name="data"]').addEventListener('change', carregarHorariosDisponiveis);
// document.querySelector('select[name="usuario_id"]').addEventListener('change', carregarHorariosDisponiveis);

function selecionarHorario(horario) {
    const horarioSelecionado = document.getElementById('horario-selecionado');
    horarioSelecionado.textContent = `Horário selecionado: ${horario}`;

    const containerHorarios = document.getElementById('horarios-disponiveis');
    const botoes = containerHorarios.querySelectorAll('.time-slot');
    
    // Remove a seleção de todos os botões
    botoes.forEach(botao => {
        botao.classList.remove('selected');
    });
    
    // Adiciona a seleção ao botão clicado
    botoes.forEach(botao => {
        if (botao.textContent === horario) {
            botao.classList.add('selected');
        }
    });

    const form = document.getElementById('form-agendamento');
    let inputHorario = form.querySelector('input[name="horario"]');

    if (!inputHorario) {
        inputHorario = document.createElement('input');
        inputHorario.type = 'hidden';
        inputHorario.name = 'horario';
        form.appendChild(inputHorario);
    }

    inputHorario.value = horario;
}

function abrirModalAgendamento(empresaId) {
    empresaIdAtual = empresaId; // Define a empresa atual
    carregarFuncionarios(empresaId);
    carregarServicos(empresaId);
    carregarDetalhesEmpresa(empresaId); // Chama a nova função
    document.getElementById('modal-agendamento').style.display = 'flex';
    document.getElementById('empresas-lista').style.display = 'none';
    document.getElementById('search-container').style.display = 'none';
}



document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('form-agendamento');
    if (form) {
        // Variável para controlar se já está processando
        let processando = false;
        
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            console.log('=== EVENTO SUBMIT DISPARADO ===');
            
            // Evitar múltiplas submissões
            if (processando) {
                console.log('Já está processando, ignorando nova submissão');
                return;
            }
            
            processando = true;
            console.log('=== INICIANDO PROCESSAMENTO ===');

            // Desabilitar botão de submit
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Processando...';
            }

            mostrarCarregamento(); // Exibe a tela de carregamento

            const dados = new FormData(e.target);
            const dadosObj = Object.fromEntries(dados.entries());

            // Validação da data
            const dataSelecionada = new Date(dadosObj.data);
            const hoje = new Date();
            hoje.setHours(0, 0, 0, 0);
            
            if (dataSelecionada < hoje) {
                mostrarAlerta('Não é possível agendar para datas passadas.', 'warning');
                esconderCarregamento();
                return;
            }
            
            // Validação do telefone
            const telefone = dadosObj.telefone;
            if (telefone.length < 10 || telefone.length > 11) {
                mostrarAlerta('Por favor, insira um número de telefone válido com 10 ou 11 dígitos.', 'warning');
                esconderCarregamento();
                return;
            }

            try {
                console.log('=== INÍCIO DO AGENDAMENTO ===');
                console.log('Dados sendo enviados:', dadosObj);
                
                // Teste simples com fetch primeiro
                const fetchResponse = await fetch('/api/agendar-cliente', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(dadosObj)
                });
                
                console.log('=== RESPOSTA FETCH ===');
                console.log('Status:', fetchResponse.status);
                console.log('OK:', fetchResponse.ok);
                
                const responseData = await fetchResponse.json();
                console.log('Dados:', responseData);
                
                if (fetchResponse.ok) {
                    console.log('SUCESSO - Mostrando popup de sucesso');
                    mostrarAlerta(responseData.message || 'Agendamento realizado com sucesso!', 'success');
                    
                    // Limpar interface
                    document.getElementById('modal-agendamento').style.display = 'none';
                    document.getElementById('empresas-lista').style.display = 'block';
                    document.getElementById('search-container').style.display = 'block';
                    form.reset();
                    document.getElementById('horarios-disponiveis').innerHTML = '';
                    document.getElementById('horario-selecionado').innerHTML = '';
                } else {
                    console.log('ERRO - Mostrando popup de erro');
                    mostrarAlerta(responseData.error || 'Erro ao realizar o agendamento', 'error');
                }
                
            } catch (err) {
                console.log('=== ERRO CAPTURADO ===');
                console.log('Tipo de erro:', err.name);
                console.log('Mensagem:', err.message);
                
                // Erro de rede ou outro tipo
                console.log('Erro de rede detectado, mostrando mensagem de erro');
                mostrarAlerta('Erro de conexão. Verifique sua internet e tente novamente.', 'error');
            } finally {
                esconderCarregamento();
                processando = false;
                
                // Reabilitar botão de submit
                const submitBtn = form.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="bi bi-check-lg"></i> Confirmar Agendamento';
                }
                
                console.log('=== PROCESSAMENTO FINALIZADO ===');
            }
        });
    }
});

// Event listeners para campos de data e profissional
document.addEventListener('DOMContentLoaded', function() {
    const dataInput = document.getElementById('data-input');
    const profissionalSelect = document.getElementById('profissional-select');
    
    if (dataInput) {
        dataInput.addEventListener('change', carregarHorariosDisponiveis);
    }
    
    if (profissionalSelect) {
        profissionalSelect.addEventListener('change', carregarHorariosDisponiveis);
    }
});


function mostrarCarregamento() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        loadingScreen.style.display = 'flex'; // Exibe o carregamento
    } else {
        console.error('Elemento de carregamento não encontrado!');
    }
}

function esconderCarregamento() {
    const loadingScreen = document.getElementById('loading-screen');
    if (loadingScreen) {
        loadingScreen.style.display = 'none'; // Oculta o carregamento
    } else {
        console.error('Elemento de carregamento não encontrado!');
    }
}


// Validação do telefone
document.addEventListener('DOMContentLoaded', function() {
    const telefoneInput = document.getElementById('telefone-input');
    
    if (telefoneInput) {
        // Remove caracteres inválidos do telefone
        telefoneInput.addEventListener('input', (event) => {
            const apenasNumeros = telefoneInput.value.replace(/\D/g, ''); // Remove qualquer caractere não numérico
            telefoneInput.value = apenasNumeros; // Atualiza o valor no campo
        });
    }
});



// Event listener para o botão de localização
document.addEventListener('DOMContentLoaded', function() {
    const btnDefinirCidade = document.getElementById('btn-definir-cidade');
    
    if (btnDefinirCidade) {
        btnDefinirCidade.addEventListener('click', function(e) {
            e.preventDefault();
            obterCidade();
        });
    }
});





// Verifica se a geolocalização está disponível no navegador
async function obterCidade() {
    if (!navigator.geolocation) {
        mostrarAlerta('Geolocalização não é suportada pelo seu navegador.', 'warning');
        return;
    }

    // Mostrar feedback visual
    const btn = document.getElementById('btn-definir-cidade');
    if (btn) {
        btn.innerHTML = '<i class="bi bi-hourglass-split"></i><span>Obtendo localização...</span>';
        btn.disabled = true;
    }
    
    navigator.geolocation.getCurrentPosition(async (position) => {
        const latitude = position.coords.latitude;
        const longitude = position.coords.longitude;

        try {
            const url = `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error(`Erro na requisição: ${response.status}`);

            const data = await response.json();
            if (!data.address) throw new Error("A resposta da API não contém informações de endereço.");

            const cidade = data.address.city || data.address.town || data.address.village ||
                data.address.municipality || data.address.county;

            if (cidade) {
                mostrarAlerta(`Cidade detectada: ${cidade}`, 'success');

                const cidadeParam = encodeURIComponent(cidade);
                const urlParams = new URLSearchParams(window.location.search);

                // Verifica se a URL já contém a cidade correta
                if (urlParams.get('cidade') !== cidadeParam) {
                    urlParams.set('cidade', cidadeParam);
                    window.history.replaceState({}, '', `${window.location.pathname}?${urlParams}`);
                    carregarEmpresas(); // Recarrega as empresas com a nova cidade
                }

                buscarEmpresas(cidade);
            }
            else {
                mostrarAlerta('Não foi possível detectar sua cidade. Tente novamente.', 'warning');
            }
        } catch (error) {
            console.error("[ERRO] Exceção ao buscar a cidade:", error);
            mostrarAlerta('Erro ao buscar informações da cidade. Tente novamente.', 'error');
        } finally {
            // Restaurar o botão
            if (btn) {
                btn.innerHTML = '<i class="bi bi-geo-alt-fill"></i><span>Localização</span>';
                btn.disabled = false;
            }
        }
    }, (error) => {
        let mensagemErro = 'Erro ao obter localização.';
        
        switch(error.code) {
            case error.PERMISSION_DENIED:
                mensagemErro = 'Permissão de localização negada. Por favor, permita o acesso à localização.';
                break;
            case error.POSITION_UNAVAILABLE:
                mensagemErro = 'Informação de localização indisponível.';
                break;
            case error.TIMEOUT:
                mensagemErro = 'Tempo limite excedido para obter localização.';
                break;
            default:
                mensagemErro = 'Erro desconhecido ao obter localização.';
        }
        
        mostrarAlerta(mensagemErro, 'error');
        
        // Restaurar o botão
        if (btn) {
            btn.innerHTML = '<i class="bi bi-geo-alt-fill"></i><span>Localização</span>';
            btn.disabled = false;
        }
    });
}


// Função para buscar empresas com base na cidade
async function buscarEmpresas(cidade) {
    console.log(`[INFO] Buscando empresas para a cidade: ${cidade}`);

    try {
        // Monta a URL corretamente para o endpoint da API
        const url = `/api/empresas?cidade=${encodeURIComponent(cidade)}`;
        console.log(`[INFO] Enviando requisição para: ${url}`);

        // Realiza a requisição para buscar as empresas
        const response = await fetch(url);

        if (!response.ok) {
            console.error(`[ERRO] Falha ao buscar empresas. Status HTTP: ${response.status}`);
            throw new Error(`Erro na requisição: ${response.status}`);
        }

        const data = await response.json();

        // Exibe as empresas no console ou na interface
        if (data.length === 0) {
            console.warn("[AVISO] Nenhuma empresa encontrada para esta cidade.");
        } else {
            // Exemplo de como exibir as empresas no console
            data.forEach(empresa => {
                console.log(`Empresa: ${empresa.nome_empresa}, Cidade: ${empresa.cidade}`);
                // Você pode processar os dados aqui para atualizar a UI com as empresas
            });
        }
    } catch (error) {
        console.error("[ERRO] Exceção ao buscar empresas:", error);
    }
}

function filtrarEmpresas() {
    const input = document.getElementById("filtro-cidade").value.toLowerCase();
    const empresas = document.querySelectorAll(".empresa-card");

    empresas.forEach(empresa => {
        const cidade = empresa.querySelector(".empresa-info p:nth-child(5)").textContent.toLowerCase();
        if (cidade.includes(input)) {
            empresa.style.display = "flex";
        } else {
            empresa.style.display = "none";
        }
    });
}

// Função SPA para exibir detalhes da empresa na tela principal
window.verMaisEmpresa = function(empresaId) {
    // Esconde a lista e busca, se existirem
    const lista = document.getElementById('empresas-lista');
    if (lista) lista.style.display = 'none';
    const search = document.getElementById('search-container');
    if (search) search.style.display = 'none';
    const searchSection = document.getElementById('search-section');
    if (searchSection) searchSection.style.display = 'none';
    // NOVO: Esconde também a section pela classe
    const searchSectionClass = document.querySelector('.search-section');
    if (searchSectionClass) searchSectionClass.style.display = 'none';
    // Mostra o detalhe usando o layout bonito já existente
    carregarDetalhesEmpresa(empresaId, true); // true = modo SPA
}

// Função para voltar para a lista de empresas
window.voltarParaListaEmpresas = function() {
    document.getElementById('informacoes-empresa').style.display = 'none';
    document.getElementById('informacoes-empresa').innerHTML = '';
    const lista = document.getElementById('empresas-lista');
    if (lista) lista.style.display = 'block';
    const search = document.getElementById('search-container');
    if (search) search.style.display = 'block';
    const searchSection = document.getElementById('search-section');
    if (searchSection) searchSection.style.display = 'block';
    // NOVO: Mostra também a section pela classe
    const searchSectionClass = document.querySelector('.search-section');
    if (searchSectionClass) searchSectionClass.style.display = 'block';
}

// Função placeholder para ver produtos (será implementada na próxima etapa)
window.verProdutosEmpresa = async function(empresaId) {
    try {
        // Buscar produtos da empresa
        const response = await axios.get(`/api/produtos-empresa/${empresaId}`);
        const produtos = response.data;
        const infoDiv = document.getElementById('informacoes-empresa');
        if (!infoDiv) return alert('Erro interno: elemento de informações da empresa não encontrado.');

        // Renderizar lista de produtos em cards
        let html = `<div class='produtos-spa'>
            <button class='btn btn-secondary' onclick='voltarParaDetalhesEmpresa(${empresaId})'>Voltar</button>
            <h2>Produtos</h2>
            <div class='produtos-lista-cards'>`;
        if (!produtos || produtos.length === 0) {
            html += '<p>Nenhum produto disponível.</p>';
        } else {
            produtos.forEach(produto => {
                // URL da imagem do Supabase Storage
                const imagemUrl = produto.UUID_IMG 
                    ? `https://gccxbkoejigwkqwyvcav.supabase.co/storage/v1/object/public/produtosimg/${produto.UUID_IMG}`
                    : null;
                
                html += `
                <div class='produto-card'>
                    <div class='produto-imagem-container'>
                        ${imagemUrl 
                            ? `<img src="${imagemUrl}" alt="${produto.nome_produto}" class="produto-imagem" onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                               <div class='produto-imagem-placeholder' style="display: none;">
                                   <span>Imagem</span>
                               </div>`
                            : `<div class='produto-imagem-placeholder'>
                                   <span>Imagem</span>
                               </div>`
                        }
                    </div>
                    <div class='produto-info'>
                        <div class='produto-nome'><strong>${produto.nome_produto}</strong></div>
                        <div>Preço: R$ ${produto.preco.toFixed(2)}</div>
                        <div>Estoque: ${produto.estoque} ${produto.un_medida || ''}</div>
                        <div class='produto-botoes'>
                            <button class='btn btn-sm btn-success' onclick='adicionarAoCarrinho(${JSON.stringify(produto)})'>+</button>
                            <button class='btn btn-sm btn-danger' onclick='removerDoCarrinho(${produto.id})'>-</button>
                            <span id='qtd-carrinho-${produto.id}'>${getQtdCarrinho(produto.id)}</span>
                        </div>
                    </div>
                </div>`;
            });
        }
        html += '</div>';
        // Botão de carrinho flutuante
        html += `<button id='abrir-carrinho-btn' class='btn-carrinho-flutuante' onclick='abrirModalCarrinho()'>🛒 <span id='carrinho-count'>${carrinho.length}</span></button>`;
        // Modal do carrinho (inicialmente oculto)
        html += `<div id='modal-carrinho' class='modal-carrinho-overlay' style='display:none;'><div class='modal-carrinho-content' id='modal-carrinho-content'></div></div>`;
        html += '</div>';
        infoDiv.innerHTML = html;
        infoDiv.style.display = 'block';
        atualizarCarrinhoCount();
    } catch (error) {
        alert('Erro ao buscar produtos da empresa.');
    }
}

function atualizarCarrinhoCount() {
    const count = document.getElementById('carrinho-count');
    if (count) count.innerText = carrinho.length;
}

window.abrirModalCarrinho = function() {
    const modal = document.getElementById('modal-carrinho');
    if (!modal) return;
    renderizarModalCarrinho();
    modal.style.display = 'flex';
}

window.fecharModalCarrinho = function() {
    const modal = document.getElementById('modal-carrinho');
    if (modal) modal.style.display = 'none';
}

function renderizarModalCarrinho() {
    const modalContent = document.getElementById('modal-carrinho-content');
    if (!modalContent) return;
    if (carrinho.length === 0) {
        modalContent.innerHTML = `<h4>Carrinho</h4><p>Carrinho vazio.</p><button class='btn btn-secondary' onclick='fecharModalCarrinho()'>Fechar</button>`;
        return;
    }
    let total = 0;
    let html = `<h4>Carrinho</h4><ul class='carrinho-lista'>`;
    carrinho.forEach(item => {
        html += `<li>${item.nome_produto} x${item.quantidade} - R$ ${(item.preco * item.quantidade).toFixed(2)}</li>`;
        total += item.preco * item.quantidade;
    });
    html += `</ul><strong>Total: R$ ${total.toFixed(2)}</strong><br>`;
    html += `<button class='btn btn-success' onclick='finalizarCompraModal()'>Finalizar Compra</button> `;
    html += `<button class='btn btn-secondary' onclick='fecharModalCarrinho()'>Fechar</button>`;
    modalContent.innerHTML = html;
}

window.finalizarCompraModal = function() {
    fecharModalCarrinho();
    finalizarCompra();
}

window.voltarParaDetalhesEmpresa = function(empresaId) {
    carregarDetalhesEmpresa(empresaId, true);
}

window.adicionarAoCarrinho = function(produto) {
    // produto é um objeto
    let idx = carrinho.findIndex(p => p.id === produto.id);
    if (idx === -1) {
        carrinho.push({ ...produto, quantidade: 1 });
    } else {
        if (carrinho[idx].quantidade < produto.estoque) {
            carrinho[idx].quantidade++;
        }
    }
    atualizarCarrinho();
    document.getElementById('qtd-carrinho-' + produto.id).innerText = getQtdCarrinho(produto.id);
    atualizarCarrinhoCount(); // Atualiza o contador do botão flutuante
}

window.removerDoCarrinho = function(produtoId) {
    let idx = carrinho.findIndex(p => p.id === produtoId);
    if (idx !== -1) {
        if (carrinho[idx].quantidade > 1) {
            carrinho[idx].quantidade--;
        } else {
            carrinho.splice(idx, 1);
        }
    }
    atualizarCarrinho();
    let span = document.getElementById('qtd-carrinho-' + produtoId);
    if (span) span.innerText = getQtdCarrinho(produtoId);
    atualizarCarrinhoCount(); // Atualiza o contador do botão flutuante
}

function getQtdCarrinho(produtoId) {
    let item = carrinho.find(p => p.id === produtoId);
    return item ? item.quantidade : 0;
}

function atualizarCarrinho() {
    const container = document.getElementById('carrinho-container');
    if (!container) return;
    if (carrinho.length === 0) {
        container.innerHTML = '<p>Carrinho vazio.</p>';
        return;
    }
    let total = 0;
    let html = '<h4>Carrinho</h4><ul>';
    carrinho.forEach(item => {
        html += `<li>${item.nome_produto} x${item.quantidade} - R$ ${(item.preco * item.quantidade).toFixed(2)}</li>`;
        total += item.preco * item.quantidade;
    });
    html += `</ul><strong>Total: R$ ${total.toFixed(2)}</strong>`;
    container.innerHTML = html;
}

window.finalizarCompra = async function() {
    if (carrinho.length === 0) {
        alert('Seu carrinho está vazio!');
        return;
    }
    // Buscar nome do cliente dos cookies
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }
    const nomeCliente = getCookie('cliente_name') || 'Cliente';

    // Exibir formulário para endereço e meio de pagamento
    const infoDiv = document.getElementById('informacoes-empresa');
    let total = carrinho.reduce((soma, item) => soma + item.preco * item.quantidade, 0);
    let html = `<div class='finalizar-compra-form'>
        <h3>Finalizar Compra</h3>
        <p><strong>Nome:</strong> ${nomeCliente}</p>
        <p><strong>Total:</strong> R$ ${total.toFixed(2)}</p>
        <label>Endereço para entrega:</label>
        <input type='text' id='endereco-cliente' class='form-control' placeholder='Digite seu endereço completo' required />
        <label>Meio de pagamento:</label>
        <select id='meio-pagamento' class='form-control'>
            <option value='Dinheiro'>Dinheiro</option>
            <option value='Pix'>Pix</option>
            <option value='Cartão'>Cartão</option>
            <option value='Outro'>Outro</option>
        </select>
        <button class='btn btn-success' onclick='enviarPedidoWhatsApp()'>Enviar Pedido pelo WhatsApp</button>
        <button class='btn btn-secondary' onclick='verProdutosEmpresa(empresaIdAtual)'>Voltar</button>
    </div>`;
    infoDiv.innerHTML = html;

    // Adiciona validação para o campo endereço
    const btnEnviar = document.querySelector('.finalizar-compra-form .btn-success');
    btnEnviar.onclick = function() {
        const endereco = document.getElementById('endereco-cliente').value.trim();
        if (!endereco) {
            alert('Por favor, preencha o endereço para entrega.');
            document.getElementById('endereco-cliente').focus();
            return;
        }
        enviarPedidoWhatsApp();
    };
}

window.enviarPedidoWhatsApp = async function() {
    // Buscar telefone da empresa
    let empresaId = empresaIdAtual;
    let telefoneEmpresa = '';
    let nomeEmpresa = '';
    try {
        const response = await axios.get(`/api/empresa/${empresaId}`);
        telefoneEmpresa = response.data.tel_empresa || '';
        nomeEmpresa = response.data.nome_empresa || '';
    } catch (e) {
        alert('Erro ao buscar telefone da empresa.');
        return;
    }
    // Buscar nome do cliente dos cookies
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }
    const nomeCliente = getCookie('cliente_name') || 'Cliente';
    const endereco = document.getElementById('endereco-cliente').value;
    const meioPagamento = document.getElementById('meio-pagamento').value;
    let total = carrinho.reduce((soma, item) => soma + item.preco * item.quantidade, 0);
    let listaProdutos = carrinho.map(item => `- ${item.nome_produto} x${item.quantidade} (R$ ${(item.preco * item.quantidade).toFixed(2)})`).join('%0A');
    let mensagem = `Olá, gostaria de fazer um pedido na empresa *${nomeEmpresa}*:%0A%0A` +
        `Cliente: *${nomeCliente}*%0A` +
        `Produtos:%0A${listaProdutos}%0A` +
        `Total: *R$ ${total.toFixed(2)}*%0A` +
        `Endereço: ${endereco}%0A` +
        `Meio de pagamento: ${meioPagamento}`;
    let telefoneLimpo = telefoneEmpresa.replace(/\D/g, '');
    let url = `https://wa.me/55${telefoneLimpo}?text=${mensagem}`;
    window.open(url, '_blank');
}

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

// Abrir modal de edição de cliente e preencher dados
const btnEditarCliente = document.getElementById('btnEditarCliente');
if (btnEditarCliente) {
    btnEditarCliente.addEventListener('click', async function() {
        // Buscar dados do cliente via cookie ou API
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
        // Buscar dados do cliente via API
        let cliente = {};
        try {
            const res = await fetch(`/api/cliente/${clienteId}`);
            if (res.ok) {
                cliente = await res.json();
            }
        } catch (e) {}
        // Preencher campos
        document.getElementById('cliente_nome').value = cliente.nome_cliente || getCookie('cliente_name') || '';
        document.getElementById('cliente_email').value = cliente.email || getCookie('cliente_email') || '';
        document.getElementById('cliente_telefone').value = cliente.telefone || '';
        document.getElementById('cliente_endereco').value = cliente.endereco || '';
        document.getElementById('cliente_senha').value = '';
        // Abrir modal
        const modal = new bootstrap.Modal(document.getElementById('modalEditarCliente'));
        modal.show();
    });
}

// Salvar alterações do cliente
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
                // Atualizar cookies com os novos dados
                document.cookie = `cliente_email=${email}; path=/; max-age=${30 * 24 * 60 * 60}`;
                document.cookie = `cliente_telefone=${telefone}; path=/; max-age=${30 * 24 * 60 * 60}`;
                
                // Sincronizar dados automaticamente
                await verificarSincronizacaoDados();
                
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
        }
    });
}

// Função para salvar dados do cliente no localStorage após login
function salvarClienteLocalStorage(cliente) {
    if (!cliente) return;
    localStorage.setItem('cliente_id', cliente.id || '');
    localStorage.setItem('cliente_name', cliente.nome || '');
    localStorage.setItem('cliente_email', cliente.email || '');
    localStorage.setItem('cliente_telefone', cliente.telefone || '');
    localStorage.setItem('id_usuario_cliente', cliente.id_usuario_cliente || '');
    localStorage.setItem('id_empresa', cliente.id_empresa || '');
}

// Função para limpar dados do cliente do localStorage
function limparClienteLocalStorage() {
    localStorage.removeItem('cliente_id');
    localStorage.removeItem('cliente_name');
    localStorage.removeItem('cliente_email');
    localStorage.removeItem('cliente_telefone');
    localStorage.removeItem('id_usuario_cliente');
    localStorage.removeItem('id_empresa');
}

// Função para obter dados do cliente (prioriza localStorage, depois cookies)
function getClienteInfo() {
    let cliente = {
        id: localStorage.getItem('cliente_id'),
        nome: localStorage.getItem('cliente_name'),
        email: localStorage.getItem('cliente_email'),
        telefone: localStorage.getItem('cliente_telefone'),
        id_usuario_cliente: localStorage.getItem('id_usuario_cliente'),
        id_empresa: localStorage.getItem('id_empresa')
    };
    // Se não houver no localStorage, tenta cookies
    if (!cliente.email) {
        function getCookie(name) {
            const value = `; ${document.cookie}`;
            const parts = value.split(`; ${name}=`);
            if (parts.length === 2) return parts.pop().split(';').shift();
            return null;
        }
        cliente.id = getCookie('cliente_id');
        cliente.nome = getCookie('cliente_name');
        cliente.email = getCookie('cliente_email');
        cliente.telefone = getCookie('cliente_telefone');
        cliente.id_usuario_cliente = getCookie('id_usuario_cliente');
        cliente.id_empresa = getCookie('id_empresa');
    }
    return cliente;
}

// Ao fazer login, chame salvarClienteLocalStorage(cliente) com o objeto retornado pelo backend
// Exemplo de uso após login:
// salvarClienteLocalStorage(response.cliente);

// Ao fazer logout, chame limparClienteLocalStorage();

// Supondo que o formulário de cadastro de empresa tenha id 'form-cadastro-empresa'
document.addEventListener('DOMContentLoaded', function() {
    const formEmpresa = document.getElementById('form-cadastro-empresa');
    if (formEmpresa) {
        formEmpresa.addEventListener('submit', async function(e) {
            e.preventDefault();
            mostrarCarregamento();
            const dados = new FormData(e.target);
            const dadosObj = Object.fromEntries(dados.entries());
            try {
                const response = await fetch('/api/cadastrar-empresa', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(dadosObj)
                });
                const data = await response.json();
                esconderCarregamento();
                if (data.success) {
                    mostrarPopup('success', 'Empresa cadastrada com sucesso! Agora cadastre o usuário responsável.', 'Sucesso');
                    abrirModalCadastroUsuario(data.empresa_id); // Função que abre o modal de usuário
                } else {
                    mostrarPopup('error', data.error || 'Erro ao cadastrar empresa.', 'Erro');
                }
            } catch (e) {
                esconderCarregamento();
                mostrarPopup('error', 'Erro inesperado ao cadastrar empresa.', 'Erro');
            }
        });
    }
});


