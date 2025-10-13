/**
 * Sistema de Notificação Global WhatsApp
 * Funciona em todas as páginas do sistema
 */

class WhatsAppNotificationSystem {
    constructor() {
        this.notificationElement = document.getElementById('whatsapp-notification');
        this.soundElement = document.getElementById('notification-sound');
        this.isVisible = false;
        this.autoHideTimeout = null;
        
        // Verificar se os elementos existem
        if (!this.notificationElement) {
            console.warn('⚠️ Elemento de notificação WhatsApp não encontrado');
            return;
        }
        
        this.init();
    }
    
    init() {
        // Adicionar event listeners
        this.notificationElement.addEventListener('click', () => {
            this.hide();
        });
        
        // Verificar status do áudio
        this.checkAudioStatus();
        
        // Verificar se há mensagens não lidas ao carregar a página
        this.checkForUnreadMessages();
        
        // Configurar polling para verificar novas mensagens
        this.startPolling();
        
        // Adicionar listener para interação do usuário (necessário para alguns navegadores)
        document.addEventListener('click', () => {
            if (this.soundElement && this.soundElement.paused) {
                // Tentar carregar o áudio após primeira interação
                this.soundElement.load();
            }
        }, { once: true });
    }
    
    /**
     * Mostra uma notificação
     * @param {Object} data - Dados da notificação
     * @param {string} data.name - Nome do cliente
     * @param {string} data.message - Mensagem recebida
     * @param {string} data.avatar - URL da foto de perfil
     * @param {string} data.phone - Telefone do cliente
     * @param {number} data.duration - Duração em ms (padrão: 5000)
     */
    show(data) {
        if (!this.notificationElement) return;
        
        const {
            name = 'Cliente',
            message = 'Nova mensagem recebida',
            avatar = '',
            phone = '',
            duration = 5000
        } = data;
        
        // Atualizar conteúdo
        this.updateContent(name, message, avatar, phone);
        
        // Mostrar notificação
        this.notificationElement.classList.remove('hidden');
        this.notificationElement.classList.add('show', 'slide-in');
        
        // Tocar som
        this.playSound();
        
        // Auto-hide
        this.scheduleAutoHide(duration);
        
        this.isVisible = true;
        
        console.log('🔔 Notificação WhatsApp exibida:', { name, message: message.substring(0, 50) });
    }
    
    /**
     * Atualiza o conteúdo da notificação
     */
    updateContent(name, message, avatar, phone) {
        // Nome
        const nameElement = document.getElementById('notification-name');
        if (nameElement) {
            nameElement.textContent = name;
        }
        
        // Mensagem
        const messageElement = document.getElementById('notification-message');
        if (messageElement) {
            // Truncar mensagem se muito longa
            const truncatedMessage = message.length > 100 ? 
                message.substring(0, 100) + '...' : message;
            messageElement.textContent = truncatedMessage;
        }
        
        // Avatar
        const avatarImg = document.getElementById('notification-avatar-img');
        const avatarFallback = document.getElementById('notification-avatar-fallback');
        
        if (avatarImg && avatarFallback) {
            if (avatar && avatar.trim() !== '') {
                avatarImg.src = avatar;
                avatarImg.style.display = 'block';
                avatarFallback.style.display = 'none';
            } else {
                avatarImg.src = '';
                avatarImg.style.display = 'none';
                avatarFallback.style.display = 'flex';
            }
        }
    }
    
    /**
     * Esconde a notificação
     */
    hide() {
        if (!this.notificationElement || !this.isVisible) return;
        
        this.notificationElement.classList.add('slide-out');
        
        setTimeout(() => {
            this.notificationElement.classList.remove('show', 'slide-in', 'slide-out');
            this.notificationElement.classList.add('hidden');
            this.isVisible = false;
        }, 300);
        
        // Cancelar auto-hide
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
            this.autoHideTimeout = null;
        }
    }
    
    /**
     * Agenda o auto-hide da notificação
     */
    scheduleAutoHide(duration) {
        if (this.autoHideTimeout) {
            clearTimeout(this.autoHideTimeout);
        }
        
        this.autoHideTimeout = setTimeout(() => {
            this.hide();
        }, duration);
    }
    
    /**
     * Toca o som de notificação
     */
    playSound() {
        if (this.soundElement) {
            try {
                // Resetar o áudio
                this.soundElement.currentTime = 0;
                
                // Tentar reproduzir
                const playPromise = this.soundElement.play();
                
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            console.log('🔊 Som de notificação reproduzido com sucesso');
                        })
                        .catch(error => {
                            console.log('🔇 Erro ao reproduzir som de notificação:', error.message);
                            console.log('💡 Dica: Alguns navegadores bloqueiam áudio automático. Tente clicar na página primeiro.');
                            
                            // Tentar criar um novo elemento de áudio
                            this.createAndPlaySound();
                        });
                }
            } catch (error) {
                console.log('🔇 Erro ao reproduzir som de notificação:', error.message);
                this.createAndPlaySound();
            }
        } else {
            console.log('🔇 Elemento de áudio não encontrado');
        }
    }
    
    /**
     * Cria e reproduz um novo elemento de áudio
     */
    createAndPlaySound() {
        try {
            const audio = new Audio('/static/audio/notification.mp3');
            audio.volume = 0.5; // Volume reduzido
            audio.play()
                .then(() => {
                    console.log('🔊 Som alternativo reproduzido com sucesso');
                })
                .catch(error => {
                    console.log('🔇 Erro no som alternativo:', error.message);
                });
        } catch (error) {
            console.log('🔇 Erro ao criar som alternativo:', error.message);
        }
    }
    
    /**
     * Verifica se há mensagens não lidas
     */
    async checkForUnreadMessages() {
        try {
            const response = await fetch('/api/whatsapp/chats/stats', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (response.ok) {
                const stats = await response.json();
                const totalUnread = (stats.aguardando || 0) + (stats.atendendo || 0);
                
                if (totalUnread > 0) {
                    console.log(`📊 ${totalUnread} conversas ativas encontradas`);
                }
            }
        } catch (error) {
            console.log('🔍 Erro ao verificar mensagens não lidas:', error.message);
        }
    }
    
    /**
     * Inicia o polling para verificar novas mensagens
     */
    startPolling() {
        // Verificar a cada 5 segundos
        setInterval(async () => {
            await this.checkForNewMessages();
        }, 5000);
    }
    
    /**
     * Verifica se há novas mensagens
     */
    async checkForNewMessages() {
        try {
            // Verificar se estamos na página do WhatsApp
            const isWhatsAppPage = window.location.pathname.includes('/whatsapp');
            
            // Buscar notificações do endpoint
            const response = await fetch('/api/whatsapp/notifications', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                if (data.success && data.notifications && data.notifications.length > 0) {
                    // Mostrar a notificação mais recente
                    const latestNotification = data.notifications[0];
                    
                    if (!this.isVisible) {
                        this.show({
                            name: latestNotification.name,
                            message: latestNotification.message,
                            avatar: latestNotification.avatar,
                            phone: latestNotification.phone,
                            duration: 8000
                        });
                    }
                }
            }
            
            // Fallback: Se não estamos na página do WhatsApp, verificar mensagens diretamente
            if (!isWhatsAppPage) {
                const response = await fetch('/api/whatsapp/chats/aguardando', {
                    method: 'GET',
                    headers: {
                        'Cache-Control': 'no-cache'
                    }
                });
                
                if (response.ok) {
                    const chats = await response.json();
                    
                    // Verificar se há conversas com mensagens não lidas
                    const unreadChats = chats.filter(chat => chat.unread_count > 0);
                    
                    if (unreadChats.length > 0 && !this.isVisible) {
                        const latestChat = unreadChats[0];
                        this.show({
                            name: latestChat.name,
                            message: latestChat.last_message || 'Nova mensagem',
                            avatar: latestChat.avatar,
                            phone: latestChat.phone,
                            duration: 8000
                        });
                    }
                }
            }
        } catch (error) {
            console.log('🔍 Erro ao verificar novas mensagens:', error.message);
        }
    }
    
    /**
     * Mostra notificação de teste
     */
    test() {
        this.show({
            name: 'Cliente Teste',
            message: 'Esta é uma mensagem de teste do sistema de notificações WhatsApp!',
            avatar: '',
            phone: '5511999999999',
            duration: 10000
        });
    }
    
    /**
     * Testa apenas o som
     */
    testSound() {
        console.log('🔊 Testando som de notificação...');
        this.playSound();
    }
    
    /**
     * Verifica se o áudio está carregado
     */
    checkAudioStatus() {
        if (this.soundElement) {
            console.log('🔊 Status do áudio:', {
                readyState: this.soundElement.readyState,
                networkState: this.soundElement.networkState,
                src: this.soundElement.src,
                duration: this.soundElement.duration
            });
        } else {
            console.log('🔇 Elemento de áudio não encontrado');
        }
    }
}

// Função global para fechar notificação
function closeWhatsAppNotification() {
    if (window.whatsappNotification) {
        window.whatsappNotification.hide();
    }
}

// Função global para mostrar notificação
function showWhatsAppNotification(data) {
    if (window.whatsappNotification) {
        window.whatsappNotification.show(data);
    }
}

// Função global para teste
function testWhatsAppNotification() {
    if (window.whatsappNotification) {
        window.whatsappNotification.test();
    }
}

// Função global para testar som
function testWhatsAppSound() {
    if (window.whatsappNotification) {
        window.whatsappNotification.testSound();
    }
}

// Função global para verificar status do áudio
function checkWhatsAppAudioStatus() {
    if (window.whatsappNotification) {
        window.whatsappNotification.checkAudioStatus();
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    window.whatsappNotification = new WhatsAppNotificationSystem();
    console.log('🔔 Sistema de notificação WhatsApp inicializado');
});

// Exportar para uso global
window.WhatsAppNotificationSystem = WhatsAppNotificationSystem;
