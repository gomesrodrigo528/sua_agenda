import os
import base64
from py_vapid import Vapid01

VAPID_PRIVATE_KEY_FILE = "vapid_private.key"
VAPID_PUBLIC_KEY_FILE = "vapid_public.key"

def generate_vapid_keys():
    if not (os.path.exists(VAPID_PRIVATE_KEY_FILE) and os.path.exists(VAPID_PUBLIC_KEY_FILE)):
        vapid = Vapid01()
        vapid.generate_keys()
        private_key = vapid.private_pem().decode()
        public_key = vapid.public_pem().decode()
        with open(VAPID_PRIVATE_KEY_FILE, "w") as f:
            f.write(private_key)
        with open(VAPID_PUBLIC_KEY_FILE, "w") as f:
            f.write(public_key)
        print("Chaves VAPID geradas!")
    else:
        print("Chaves VAPID já existem.")

def get_vapid_keys():
    generate_vapid_keys()
    with open(VAPID_PRIVATE_KEY_FILE) as f:
        private_key = f.read().strip()
    with open(VAPID_PUBLIC_KEY_FILE) as f:
        public_key = f.read().strip()
    return private_key, public_key

def get_vapid_public_key_base64():
    """Retorna a chave pública VAPID em formato base64 URL-safe para uso no frontend"""
    generate_vapid_keys()
    with open(VAPID_PUBLIC_KEY_FILE) as f:
        public_key_pem = f.read().strip()
    
    # Extrair apenas a parte base64 da chave PEM
    lines = public_key_pem.split('\n')
    base64_content = ''.join([line for line in lines if not line.startswith('-----')])
    
    # Converter para bytes e depois para base64 URL-safe
    key_bytes = base64.b64decode(base64_content)
    return base64.urlsafe_b64encode(key_bytes).decode('utf-8').rstrip('=') 