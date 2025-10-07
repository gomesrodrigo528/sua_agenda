function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
        .replace(/-/g, '+')
        .replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function registerPush() {
    if (!('serviceWorker' in navigator)) {
        console.error('Service Worker não suportado neste navegador.');
        return;
    }
    if (!('PushManager' in window)) {
        console.error('PushManager não suportado neste navegador.');
        return;
    }
    try {
        const registration = await navigator.serviceWorker.register('/static/sw.js');
        console.log('Service Worker registrado:', registration);

        const permission = await Notification.requestPermission();
        if (permission !== 'granted') {
            console.warn('Permissão de notificação não concedida:', permission);
            return;
        }
        console.log('Permissão de notificação concedida.');

        const response = await fetch('/api/push/vapid_public');
        if (!response.ok) {
            console.error('Erro ao buscar chave pública VAPID:', response.status, response.statusText);
            return;
        }
        const vapidPublicKey = (await response.json()).publicKey;
        if (!vapidPublicKey) {
            console.error('Chave pública VAPID não recebida do backend.');
            return;
        }
        console.log('Chave pública VAPID recebida:', vapidPublicKey);

        let convertedVapidKey;
        try {
            convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);
        } catch (e) {
            console.error('Erro ao converter chave VAPID para Uint8Array:', e);
            return;
        }

        let subscription;
        try {
            subscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: convertedVapidKey
            });
        } catch (e) {
            console.error('Erro ao fazer subscribe no PushManager:', e);
            return;
        }
        if (!subscription) {
            console.error('Subscription não foi criada.');
            return;
        }
        console.log('Subscription criada:', subscription);

        try {
            const subResp = await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(subscription)
            });
            if (!subResp.ok) {
                console.error('Erro ao enviar subscription ao backend:', subResp.status, subResp.statusText);
                return;
            }
            console.log('Subscription enviada ao backend com sucesso.');
        } catch (e) {
            console.error('Erro ao enviar subscription ao backend:', e);
            return;
        }
        console.log('Push registrado com sucesso!');
    } catch (error) {
        console.error('Erro inesperado ao registrar push:', error);
    }
}

if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', function(event) {
        if (event.data && event.data.action === 'playSound') {
            try {
                const audio = new Audio('/static/som_notificacao.mp3');
                audio.play().then(() => {
                    console.log('Som de notificação reproduzido com sucesso.');
                }).catch(e => {
                    console.error('Erro ao tentar reproduzir o som de notificação:', e);
                });
                console.log('[DEBUG] playSound: comando recebido do Service Worker, áudio disparado.');
            } catch (e) {
                console.error('Erro ao criar objeto de áudio:', e);
            }
        }
    });
}

registerPush(); 