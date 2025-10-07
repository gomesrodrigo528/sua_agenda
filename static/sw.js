self.addEventListener('push', function(event) {
    let data = {};
    try {
        data = event.data.json();
        console.log('[SW] Dados da notificação recebidos como JSON:', data);
    } catch (e) {
        try {
            data = { title: 'Notificação', body: event.data.text() };
            console.log('[SW] Dados da notificação recebidos como texto:', data);
        } catch (err) {
            data = { title: 'Notificação', body: 'Você recebeu uma notificação.' };
            console.error('[SW] Erro ao processar dados da notificação:', err);
        }
    }
    try {
        self.registration.showNotification(data.title, {
            body: data.body,
            icon: '/static/img/logo.png'
        });
        console.log('[SW] Notificação exibida:', data.title);
    } catch (e) {
        console.error('[SW] Erro ao exibir notificação:', e);
    }

    // Envia mensagem para todas as abas abertas para tocar som
    self.clients.matchAll({type: 'window'}).then(function(clients) {
        if (!clients || clients.length === 0) {
            console.warn('[SW] Nenhuma aba aberta para enviar mensagem de som.');
        }
        clients.forEach(function(client) {
            try {
                client.postMessage({action: 'playSound'});
                console.log('[SW] Mensagem enviada para aba para tocar som.');
            } catch (e) {
                console.error('[SW] Erro ao enviar mensagem para aba:', e);
            }
        });
    }).catch(function(e) {
        console.error('[SW] Erro ao buscar clients:', e);
    });
}); 