fetch('/api/push/vapid_public')
  .then(res => res.json())
  .then(data => {
    const publicKey = data.publicKey;
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.register('/static/sw.js').then(function(reg) {
            Notification.requestPermission().then(function(permission) {
                if (permission === 'granted') {
                    reg.pushManager.subscribe({
                        userVisibleOnly: true,
                        applicationServerKey: publicKey
                    }).then(function(subscription) {
                        fetch('/api/push/subscribe', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify(subscription)
                        });
                    });
                }
            });
        });
    }
  }); 