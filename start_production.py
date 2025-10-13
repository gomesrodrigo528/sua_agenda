#!/usr/bin/env python3
"""
Script de inicialização para produção
Configura o ambiente e inicia o servidor Flask com Gunicorn
"""

import os
import sys
import logging
from pathlib import Path

def setup_logging():
    """Configura o sistema de logging"""
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', 'logs/app.log')
    
    # Criar diretório de logs se não existir
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configurado - Nível: {log_level}, Arquivo: {log_file}")
    return logger

def validate_environment():
    """Valida variáveis de ambiente críticas"""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'MERCADOPAGO_ACCESS_TOKEN',
        'FLASK_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        raise ValueError(f"Variáveis de ambiente obrigatórias não encontradas: {', '.join(missing_vars)}")
    
    return True

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        'static/uploads',
        'static/uploads/whatsapp',
        'static/uploads/whatsapp/images',
        'static/uploads/whatsapp/audios',
        'static/uploads/whatsapp/videos',
        'static/uploads/whatsapp/documents',
        'logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"📁 Diretório criado/verificado: {directory}")

def main():
    """Função principal"""
    print("🚀 Iniciando aplicação Flask em produção...")
    
    # Configurar logging
    logger = setup_logging()
    
    # Validar ambiente
    try:
        validate_environment()
        logger.info("✅ Variáveis de ambiente validadas")
    except ValueError as e:
        logger.error(f"❌ Erro de validação: {e}")
        sys.exit(1)
    
    # Criar diretórios
    create_directories()
    logger.info("✅ Diretórios criados/verificados")
    
    # Configurar variáveis de ambiente
    os.environ['FLASK_ENV'] = 'production'
    os.environ['FLASK_DEBUG'] = 'False'
    
    # Importar e configurar a aplicação
    try:
        from main import app
        logger.info("✅ Aplicação Flask importada com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao importar aplicação: {e}")
        sys.exit(1)
    
    # Configurar Gunicorn
    port = int(os.getenv('PORT', 5000))
    workers = int(os.getenv('GUNICORN_WORKERS', 4))
    threads = int(os.getenv('GUNICORN_THREADS', 2))
    timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
    
    logger.info(f"🌐 Configurações do servidor:")
    logger.info(f"   - Porta: {port}")
    logger.info(f"   - Workers: {workers}")
    logger.info(f"   - Threads: {threads}")
    logger.info(f"   - Timeout: {timeout}s")
    
    # Iniciar servidor
    try:
        import gunicorn.app.wsgiapp as wsgi
        sys.argv = [
            'gunicorn',
            '-b', f'0.0.0.0:{port}',
            'main:app',
            '--workers', str(workers),
            '--threads', str(threads),
            '--timeout', str(timeout),
            '--keepalive', '2',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--preload',
            '--access-logfile', '-',
            '--error-logfile', '-',
            '--log-level', 'info'
        ]
        wsgi.run()
    except Exception as e:
        logger.error(f"❌ Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
