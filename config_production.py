"""
Configurações específicas para produção
"""

import os

class ProductionConfig:
    """Configurações para produção"""
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # Segurança
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # CORS
    CORS_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://www.suaagenda.fun').split(',')
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
    
    # Cache
    CACHE_TYPE = 'simple'
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Gunicorn
    GUNICORN_WORKERS = int(os.getenv('GUNICORN_WORKERS', 4))
    GUNICORN_THREADS = int(os.getenv('GUNICORN_THREADS', 2))
    GUNICORN_TIMEOUT = int(os.getenv('GUNICORN_TIMEOUT', 120))
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = '100 per hour'
    
    # Health Check
    HEALTH_CHECK_INTERVAL = int(os.getenv('HEALTH_CHECK_INTERVAL', 30))
    HEALTH_CHECK_TIMEOUT = int(os.getenv('HEALTH_CHECK_TIMEOUT', 5))
    
    @staticmethod
    def validate_production_env():
        """Valida variáveis de ambiente específicas para produção"""
        required_vars = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'MERCADOPAGO_ACCESS_TOKEN',
            'FLASK_SECRET_KEY',
            'WHATSAPP_API_URL_PRODUCTION'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente obrigatórias para produção não encontradas: {', '.join(missing_vars)}")
        
        return True
