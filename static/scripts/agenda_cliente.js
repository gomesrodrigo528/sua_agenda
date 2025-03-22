async function buscarAgendamentos() {
    const email = document.getElementById('email').value.trim();
    const form = document.getElementById('formAgendamentos');
    const mensagem = document.querySelector('.msg');
    const resultadoDiv = document.getElementById('resultado');

    if (!email) {
        alert('Por favor, insira um e-mail válido.');
        return;
    }

    const url = `/agenda_cliente/${encodeURIComponent(email)}`;

    try {
        const response = await fetch(url);
        resultadoDiv.innerHTML = ''; // Limpa resultados anteriores

        if (response.ok) {
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
                resultadoDiv.innerHTML += '<p>Nenhum agendamento encontrado para este cliente.</p>';
            }
        } else {
            const errorData = await response.json();
            resultadoDiv.innerHTML = `<p>${errorData.mensagem || errorData.erro || 'Erro ao buscar agendamentos.'}</p>`;
        }
    } catch (error) {
        console.error('Erro:', error);
        resultadoDiv.innerHTML = '<p>Erro ao buscar agendamentos.</p>';
    }
}

// Função para formatar a data no padrão DD/MM/AAAA
function formatarData(dataISO) {
    const [ano, mes, dia] = dataISO.split('-');
    return `${dia}/${mes}/${ano}`;
}
