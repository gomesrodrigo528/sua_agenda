/**
 * WhatsApp CRM JavaScript - Sistema Multi-Tenant
 * Gerencia interface de chat, mensagens e interações
 */

// Estado global
let chats = [];
let currentChatId = null;
let currentUserId = null;
let currentUserPhone = null;
let currentUserAvatar = null;
let currentUserName = null;
let messages = [];
let isLoading = false;
let isSending = false;

// Elementos DOM
const chatsList = document.getElementById('chatsList');
const emptyState = document.getElementById('emptyState');
const chatContainer = document.getElementById('chatContainer');
const chatAvatar = document.getElementById('chatAvatar');
const chatName = document.getElementById('chatName');
const chatPhone = document.getElementById('chatPhone');
const messagesContainer = document.getElementById('messagesContainer');
const messageForm = document.getElementById('messageForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const searchInput = document.getElementById('searchInput');

// Modal Nova Conversa
const newChatModal = document.getElementById('newChatModal');
const newChatForm = document.getElementById('newChatForm');
const submitNewChatBtn = document.getElementById('submitNewChatBtn');
const newPhoneInput = document.getElementById('newPhoneInput');
const newMessageInput = document.getElementById('newMessageInput');

// Modal Editar Usuário
const editUserModal = document.getElementById('editUserModal');
const editUserForm = document.getElementById('editUserForm');
const editNameInput = document.getElementById('editNameInput');
const editPhoneDisplay = document.getElementById('editPhoneDisplay');

// Funções de formatação
function formatTime(timestamp) {
    if (!timestamp) return 'Agora';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const seconds = Math.floor(diff / 1000);
    
    if (seconds < 60) return 'Agora';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h`;
    
    return date.toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleString('pt-BR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Carregar lista de chats
async function carregarChats() {
    try {
        const response = await fetch('/api/whatsapp/chats');
        if (!response.ok) throw new Error('Erro ao carregar chats');
        
        chats = await response.json();
        renderizarChats();
        
    } catch (error) {
        console.error('Erro ao carregar chats:', error);
        mostrarErro('Erro ao carregar conversas');
    }
}

// Renderizar lista de chats
function renderizarChats(filter = '') {
    if (chats.length === 0) {
        chatsList.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="bi bi-chat-dots"></i>
                </div>
                <p>Nenhuma conversa ainda</p>
                <p class="empty-subtitle">Clique em "Nova Conversa" para começar</p>
            </div>
        `;
        return;
    }

    const filteredChats = chats.filter(chat => 
        chat.name.toLowerCase().includes(filter.toLowerCase()) ||
        chat.phone.includes(filter)
    );

    chatsList.innerHTML = filteredChats.map(chat => `
        <div 
            class="chat-item ${chat.chat_id === currentChatId ? 'active' : ''} ${chat.unread_count > 0 ? 'unread' : ''}" 
            onclick="abrirChat(${chat.chat_id}, ${chat.user_id}, '${escapeHtml(chat.name)}', '${chat.phone}', '${chat.avatar || ''}')"
        >
            <div class="chat-avatar">
                ${renderizarAvatar(chat.name, chat.avatar)}
            </div>
            <div class="chat-info">
                <h4 class="chat-name">${escapeHtml(chat.name)}</h4>
                <p class="chat-last-message">${escapeHtml(chat.last_message || 'Sem mensagens')}</p>
            </div>
            <div class="chat-meta">
                <span class="chat-time">${formatTime(chat.last_update)}</span>
                ${chat.unread_count > 0 ? `<span class="chat-unread">${chat.unread_count}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// Renderizar avatar
function renderizarAvatar(name, avatarUrl = null) {
    if (avatarUrl) {
        return `<img src="${avatarUrl}" alt="${name}" />`;
    }
    return `<i class="bi bi-person"></i>`;
}

// Abrir chat
async function abrirChat(chatId, userId, name, phone, avatarUrl = null) {
    currentChatId = chatId;
    currentUserId = userId;
    currentUserPhone = phone;
    currentUserAvatar = avatarUrl;
    currentUserName = name;
    
    // Atualiza UI
    emptyState.classList.add('hidden');
    chatContainer.classList.remove('hidden');
    
    // Atualiza header
    chatAvatar.innerHTML = renderizarAvatar(name, avatarUrl);
    chatName.textContent = name;
    chatPhone.textContent = phone;
    
    // Marca mensagens como lidas
    try {
        await fetch(`/api/whatsapp/mark_as_read/${chatId}`, { method: 'POST' });
    } catch (error) {
        console.error('Erro ao marcar como lido:', error);
    }
    
    // Carrega mensagens
    await carregarMensagens();
    
    // Atualiza lista de chats
    await carregarChats();
    renderizarChats(searchInput.value);
    
    // Mobile: esconde sidebar
    if (window.innerWidth <= 768) {
        document.querySelector('.whatsapp-sidebar').classList.add('hidden');
    }
}

// Carregar mensagens
async function carregarMensagens() {
    if (!currentChatId || isLoading) return;
    
    try {
        isLoading = true;
        
        const response = await fetch(`/api/whatsapp/messages/${currentChatId}`);
        if (!response.ok) throw new Error('Erro ao carregar mensagens');
        
        const newMessages = await response.json();
        
        if (JSON.stringify(newMessages) !== JSON.stringify(messages)) {
            messages = newMessages;
            renderizarMensagens();
        }
        
    } catch (error) {
        console.error('Erro ao carregar mensagens:', error);
    } finally {
        isLoading = false;
    }
}

// Renderizar mensagens
function renderizarMensagens() {
    if (messages.length === 0) {
        messagesContainer.innerHTML = `
            <div class="empty-state">
                <div class="empty-icon">
                    <i class="bi bi-chat-dots"></i>
                </div>
                <p>Nenhuma mensagem ainda</p>
                <p class="empty-subtitle">Envie uma mensagem para iniciar</p>
            </div>
        `;
        return;
    }

    messagesContainer.innerHTML = messages.map(msg => {
        const isOwn = msg.direction === 'sent';
        const alignment = isOwn ? 'justify-end' : 'justify-start';
        const bgClass = isOwn ? 'message-sent' : 'message-received';
        
        let mediaContent = '';
        
        switch (msg.message_type) {
            case 'image':
                mediaContent = `
                    <div class="message-media">
                        <img src="${msg.media_url}" alt="Imagem" class="media-image" onclick="abrirLightbox('${msg.media_url}')">
                    </div>
                `;
                break;
            case 'audio':
                mediaContent = `
                    <div class="message-media">
                        <audio controls class="media-audio">
                            <source src="${msg.media_url}" type="audio/mpeg">
                            Seu navegador não suporta áudio.
                        </audio>
                    </div>
                `;
                break;
            case 'video':
                mediaContent = `
                    <div class="message-media">
                        <video controls class="media-video">
                            <source src="${msg.media_url}" type="video/mp4">
                            Seu navegador não suporta vídeo.
                        </video>
                    </div>
                `;
                break;
            case 'document':
                mediaContent = `
                    <div class="message-media">
                        <div class="media-document">
                            <i class="bi bi-file-earmark"></i>
                            <a href="${msg.media_url}" target="_blank" class="document-link">
                                ${msg.media_filename || 'Documento'}
                            </a>
                        </div>
                    </div>
                `;
                break;
            default:
                mediaContent = `
                    <div class="message-text">
                        ${escapeHtml(msg.message)}
                    </div>
                `;
        }

        return `
            <div class="message-wrapper ${alignment}">
                <div class="message ${bgClass}">
                    ${mediaContent}
                    <div class="message-time">
                        ${formatTimestamp(msg.timestamp)}
                    </div>
                </div>
            </div>
        `;
    }).join('');

    scrollToBottom();
}

// Scroll para o final
function scrollToBottom() {
    setTimeout(() => {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 100);
}

// Enviar mensagem
async function enviarMensagem(message) {
    if (!currentChatId || isSending) return;
    
    try {
        isSending = true;
        sendBtn.disabled = true;
        sendBtn.innerHTML = '<i class="bi bi-hourglass-split"></i>';
        
        const response = await fetch('/api/whatsapp/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: currentChatId,
                message: message
            })
        });
        
        if (response.ok) {
            messageInput.value = '';
            messageInput.style.height = 'auto';
            await carregarMensagens();
            await carregarChats();
        } else {
            const result = await response.json();
            mostrarErro(result.error || 'Erro ao enviar mensagem');
        }
        
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        mostrarErro('Erro ao enviar mensagem');
    } finally {
        isSending = false;
        sendBtn.disabled = false;
        sendBtn.innerHTML = '<i class="bi bi-send"></i>';
        messageInput.focus();
    }
}

// Iniciar nova conversa
async function iniciarNovaConversa(phone, message) {
    try {
        submitNewChatBtn.disabled = true;
        submitNewChatBtn.textContent = 'Criando...';
        
        // Cria o chat
        const webhookResponse = await fetch('/api/whatsapp/create_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phone })
        });
        
        if (!webhookResponse.ok) throw new Error('Erro ao criar chat');
        
        const { chat_id, user } = await webhookResponse.json();
        
        // Envia a mensagem
        const sendResponse = await fetch('/api/whatsapp/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                chat_id: chat_id,
                message: message
            })
        });
        
        if (!sendResponse.ok) throw new Error('Erro ao enviar mensagem');
        
        // Recarrega chats e abre o novo
        await carregarChats();
        const chat = chats.find(c => c.chat_id === chat_id);
        if (chat) {
            abrirChat(chat.chat_id, user.id, chat.name, chat.phone);
        }
        
        // Fecha modal
        fecharModalNovaConversa();
        
    } catch (error) {
        console.error('Erro ao criar conversa:', error);
        mostrarErro('Erro ao criar conversa: ' + error.message);
    } finally {
        submitNewChatBtn.disabled = false;
        submitNewChatBtn.textContent = 'Iniciar Conversa';
    }
}

// Editar nome do usuário
async function atualizarNomeUsuario(userId, newName) {
    try {
        const response = await fetch('/api/whatsapp/update_user', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: userId,
                name: newName
            })
        });
        
        if (!response.ok) throw new Error('Erro ao atualizar nome');
        
        // Atualiza UI
        chatName.textContent = newName;
        chatAvatar.innerHTML = renderizarAvatar(newName, currentUserAvatar);
        
        // Recarrega chats
        await carregarChats();
        
        // Fecha modal
        fecharModalEditarUsuario();
        
        mostrarSucesso('Nome atualizado com sucesso!');
        
    } catch (error) {
        console.error('Erro ao atualizar nome:', error);
        mostrarErro('Erro ao atualizar nome');
    }
}

// Modal Nova Conversa
function abrirModalNovaConversa() {
    newChatModal.classList.remove('hidden');
    newPhoneInput.focus();
}

function fecharModalNovaConversa() {
    newChatModal.classList.add('hidden');
    newPhoneInput.value = '';
    newMessageInput.value = '';
}

// Modal Editar Usuário
function editarUsuario() {
    if (!currentUserId) return;
    editNameInput.value = chatName.textContent;
    editPhoneDisplay.value = chatPhone.textContent;
    editUserModal.classList.remove('hidden');
    editNameInput.focus();
}

function fecharModalEditarUsuario() {
    editUserModal.classList.add('hidden');
}

// Voltar para lista (mobile)
function voltarParaLista() {
    if (window.innerWidth <= 768) {
        document.querySelector('.whatsapp-sidebar').classList.remove('hidden');
        chatContainer.classList.add('hidden');
        emptyState.classList.remove('hidden');
    }
}

// Abrir lightbox para imagens
function abrirLightbox(imageUrl) {
    // Implementar lightbox simples
    const lightbox = document.createElement('div');
    lightbox.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 2000;
        cursor: pointer;
    `;
    
    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
    `;
    
    lightbox.appendChild(img);
    document.body.appendChild(lightbox);
    
    lightbox.addEventListener('click', () => {
        document.body.removeChild(lightbox);
    });
}

// Mostrar erro
function mostrarErro(mensagem) {
    // Implementar sistema de notificações
    alert(mensagem);
}

// Mostrar sucesso
function mostrarSucesso(mensagem) {
    // Implementar sistema de notificações
    alert(mensagem);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', function() {
    // Form de mensagem
    if (messageForm) {
        messageForm.addEventListener('submit', (e) => {
            e.preventDefault();
            if (isSending) return;
            const message = messageInput.value.trim();
            if (message) enviarMensagem(message);
        });
    }

    // Auto-resize textarea
    if (messageInput) {
        messageInput.addEventListener('input', () => {
            messageInput.style.height = 'auto';
            messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
        });

        messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (!isSending) {
                    messageForm.dispatchEvent(new Event('submit'));
                }
            }
        });
    }

    // Busca
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            renderizarChats(e.target.value);
        });
    }

    // Modal Nova Conversa
    if (newChatForm) {
        newChatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const phone = newPhoneInput.value.trim().replace(/\D/g, '');
            const message = newMessageInput.value.trim();
            
            if (phone && message) {
                iniciarNovaConversa(phone, message);
            }
        });
    }

    // Modal Editar Usuário
    if (editUserForm) {
        editUserForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const newName = editNameInput.value.trim();
            if (newName && currentUserId) {
                atualizarNomeUsuario(currentUserId, newName);
            }
        });
    }

    // Upload de arquivo
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (file) {
                try {
                    // Implementar upload de arquivo
                    mostrarErro('Upload de arquivo ainda não implementado');
                } catch (error) {
                    console.error('Erro ao enviar arquivo:', error);
                    mostrarErro('Erro ao enviar arquivo');
                }
                e.target.value = '';
            }
        });
    }

    // Auto-refresh
    setInterval(() => {
        carregarChats();
        if (currentChatId && !isSending) {
            carregarMensagens();
        }
    }, 5000);

    // Inicialização
    carregarChats();
});

// Detectar mudanças de conectividade
window.addEventListener('online', function() {
    console.log('Conexão restaurada');
    carregarChats();
});

window.addEventListener('offline', function() {
    console.log('Conexão perdida');
    mostrarErro('Conexão perdida. Alguns dados podem não estar atualizados.');
});
