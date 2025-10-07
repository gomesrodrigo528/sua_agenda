"""
Configurações da aplicação Sua Agenda
Todas as variáveis de ambiente são carregadas aqui
"""

import os
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

class Config:
    """Configurações da aplicação"""
    
    # Flask
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://gccxbkoejigwkqwyvcav.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # MercadoPago
    MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN')
    
    # Email (SMTP)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_EMAIL = os.getenv('SMTP_EMAIL')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    
    # Push Notifications
    VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
    VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
    
    @staticmethod
    def validate_required_env():
        """Valida se todas as variáveis obrigatórias estão definidas"""
        required_vars = [
            'SUPABASE_KEY',
            'MERCADOPAGO_ACCESS_TOKEN'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
        
        return True
