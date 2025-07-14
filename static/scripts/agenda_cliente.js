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

// Carregar agendamentos automaticamente quando a página for carregada
document.addEventListener('DOMContentLoaded', function() {
    buscarAgendamentos();
});
