function renderMenu(containerId) {
    // Verifica se há dados de cliente/empresa nos cookies ou localStorage (apenas para debug)
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }
    const idEmpresa = localStorage.getItem('id_empresa') || getCookie('id_empresa');
    const clienteId = localStorage.getItem('cliente_id') || getCookie('cliente_id');
    const clienteName = localStorage.getItem('cliente_name') || getCookie('cliente_name');
    
    // Removida a restrição que impedia o carregamento do menu
    // O menu agora será sempre carregado, independente dos cookies

    const loading = document.getElementById('loading');
    if (loading) {
        loading.style.display = 'flex'; // Exibe a tela de carregamento
    }

    const container = document.getElementById(containerId);
    if (!container) {
        console.error(`Container com o ID "${containerId}" não encontrado.`);
        if (loading) {
            loading.style.display = 'none'; // Remove a tela de carregamento em caso de erro
        }
        return;
    }

    // Verifica se está na página do PDV
    const isPDV = window.location.pathname.includes('/vendas');

    // Adiciona timeout para evitar carregamento infinito
    const timeout = setTimeout(() => {
        console.error('Timeout ao carregar dados da empresa');
        if (loading) {
            loading.style.display = 'none';
        }
        // Renderiza menu com dados padrão em caso de timeout
        renderDefaultMenu(container, isPDV);
    }, 10000); // 10 segundos de timeout

    fetch('/api/empresa/logada')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            clearTimeout(timeout); // Limpa o timeout se a requisição for bem-sucedida
            
            if (data.erro) {
                throw new Error(data.erro);
            }
            
            const logo = data.logo || '/static/img/logo.png';
            const corEmpresa = data.cor_emp || '#343a40';
            document.documentElement.style.setProperty('--cor-empresa', corEmpresa);

            // Se for PDV, adiciona style="display: none" para telas médias e maiores
            const menuStyle = isPDV ? 
                `width: 250px; min-height: 100vh; background-color: ${corEmpresa}; @media (min-width: 768px) { display: none; }` :
                `width: 250px; min-height: 100vh; background-color: ${corEmpresa};`;

            container.innerHTML = `
            <nav id="menu-lateral" class="text-white p-3" style="${menuStyle}">
                <ul class="nav flex-column mt-4">
                    <img src="${logo}" id="logo" alt="Logo da Empresa" style="max-width: 100%; height: 180px;">

                    <!-- Ações principais -->
                    <li class="nav-item mb-3">
                        <a href="/agenda" class="nav-link text-white"><i class="bi bi-calendar3"></i> Agenda</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/vendas" class="nav-link text-white"><i class="bi bi-currency-dollar"></i> Vender</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/clientes" class="nav-link text-white"><i class="bi bi-people"></i> Clientes</a>
                    </li>

                    <!-- Operações de suporte -->
                    <li class="nav-item mb-3">
                        <a href="/servicos" class="nav-link text-white"><i class="bi bi-hammer"></i> Serviços</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/produtos" class="nav-link text-white"><i class="bi bi-box-seam"></i> Produtos</a>
                    </li>

                    <!-- Gestão e administração -->
                    <li class="nav-item mb-3">
                        <a href="/financeiro" class="nav-link text-white"><i class="bi bi-cash"></i> Financeiro</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/relatorios" class="nav-link text-white"><i class="bi bi-bar-chart"></i> Relatórios</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/usuarios" class="nav-link text-white"><i class="bi bi-person-badge"></i> Usuários</a>
                    </li>
                    <li class="nav-item mb-3">
                        <a href="/configuracao" class="nav-link text-white"><i class="bi bi-gear"></i> Configurações</a>
                    </li>

                    <!-- Sair -->
                    <li class="nav-item mb-3">
                        <a href="/login" class="nav-link text-white"><i class="bi bi-arrow-90deg-up"></i> Sair</a>
                    </li>
                </ul>
            </nav>
            `;

            // Garantir que o código de manipulação do menu seja chamado depois de renderizar o menu
            setupMenu();

            // Se for PDV, adiciona uma regra CSS para esconder o menu em telas médias e maiores
            if (isPDV) {
                const style = document.createElement('style');
                style.textContent = `
                    @media (min-width: 768px) {
                        #menu-lateral {
                            display: none !important;
                        }
                        main {
                            margin-left: 0 !important;
                            padding-left: 0 !important;
                            width: 100% !important;
                        }
                        .container {
                            max-width: 100% !important;
                            margin-left: auto !important;
                            margin-right: auto !important;
                            padding-left: 1rem !important;
                            padding-right: 1rem !important;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        })
        .catch(error => {
            clearTimeout(timeout); // Limpa o timeout em caso de erro
            console.error('Erro ao carregar dados da empresa:', error);
            
            // Renderiza menu com dados padrão em caso de erro
            renderDefaultMenu(container, isPDV);
        })
        .finally(() => {
            if (loading) {
                loading.style.display = 'none'; // Oculta a tela de carregamento após o carregamento
            }
        });
}

// Função para renderizar menu com dados padrão em caso de erro
function renderDefaultMenu(container, isPDV) {
    const menuStyle = isPDV ? 
        `width: 250px; min-height: 100vh; background-color: #343a40; @media (min-width: 768px) { display: none; }` :
        `width: 250px; min-height: 100vh; background-color: #343a40;`;

    container.innerHTML = `
    <nav id="menu-lateral" class="text-white p-3" style="${menuStyle}">
        <ul class="nav flex-column mt-4">
            <img src="/static/img/logo.png" id="logo" alt="Logo da Empresa" style="max-width: 100%; height: 180px;">

            <!-- Ações principais -->
            <li class="nav-item mb-3">
                <a href="/agenda" class="nav-link text-white"><i class="bi bi-calendar3"></i> Agenda</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/vendas" class="nav-link text-white"><i class="bi bi-currency-dollar"></i> Vender</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/clientes" class="nav-link text-white"><i class="bi bi-people"></i> Clientes</a>
            </li>

            <!-- Operações de suporte -->
            <li class="nav-item mb-3">
                <a href="/servicos" class="nav-link text-white"><i class="bi bi-hammer"></i> Serviços</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/produtos" class="nav-link text-white"><i class="bi bi-box-seam"></i> Produtos</a>
            </li>

            <!-- Gestão e administração -->
            <li class="nav-item mb-3">
                <a href="/financeiro" class="nav-link text-white"><i class="bi bi-cash"></i> Financeiro</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/relatorios" class="nav-link text-white"><i class="bi bi-bar-chart"></i> Relatórios</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/usuarios" class="nav-link text-white"><i class="bi bi-person-badge"></i> Usuários</a>
            </li>
            <li class="nav-item mb-3">
                <a href="/configuracao" class="nav-link text-white"><i class="bi bi-gear"></i> Configurações</a>
            </li>

            <!-- Sair -->
            <li class="nav-item mb-3">
                <a href="/login" class="nav-link text-white"><i class="bi bi-arrow-90deg-up"></i> Sair</a>
            </li>
        </ul>
    </nav>
    `;

    // Garantir que o código de manipulação do menu seja chamado
    setupMenu();

    // Se for PDV, adiciona uma regra CSS para esconder o menu em telas médias e maiores
    if (isPDV) {
        const style = document.createElement('style');
        style.textContent = `
            @media (min-width: 768px) {
                #menu-lateral {
                    display: none !important;
                }
                main {
                    margin-left: 0 !important;
                    padding-left: 0 !important;
                    width: 100% !important;
                }
                .container {
                    max-width: 100% !important;
                    margin-left: auto !important;
                    margin-right: auto !important;
                    padding-left: 1rem !important;
                    padding-right: 1rem !important;
                }
            }
        `;
        document.head.appendChild(style);
    }
}

// Função para configurar o menu
function setupMenu() {
    const menuLateral = document.getElementById("menu-lateral");
    const toggleMenu = document.getElementById("toggle-menu");
    const menuContainer = document.getElementById("menu-container");

    // Função para fechar o menu
    function closeMenu() {
        menuLateral.classList.remove("open");
    }

    // Evento para abrir o menu
    toggleMenu.addEventListener("click", function () {
        menuLateral.classList.toggle("open");
    });

    // Fechar o menu ao clicar fora dele
    document.addEventListener("click", function (event) {
        // Verifica se o clique foi fora do menu lateral e do botão de alternância
        if (!menuLateral.contains(event.target) && !toggleMenu.contains(event.target) && !menuContainer.contains(event.target)) {
            closeMenu();
        }
    });
}
