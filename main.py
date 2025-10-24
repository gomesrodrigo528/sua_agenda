from flask import Flask, redirect, url_for, request
from config import Config
from dotenv import load_dotenv
import os
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Iniciar o agendador
from waitress import serve
from routes.services import services_bp
from routes.users import users_bp
from routes.clientes import clientes_bp
from routes.relatorios import relatorios_bp
from routes.agenda import agenda_bp
from routes.login import login_bp
from routes.agendamento import agendamento_bp
from routes.agenda_cliente import agenda_cliente_bp
from routes.lembrete_email import lembrete_email_bp, verificar_agendamentos  # Importe a função aqui
from routes.config import config_bp
from routes.payment import payment_bp
from routes.sucesso import sucesso_bp
from routes.tasks import tasks_bp
from routes.renovacao import renovacao_bp
from routes.financeiro import financeiro_bp
from routes.check_health import check_health_bp
from routes.produtos import produtos_bp
from routes.vendas import vendas_bp
from routes.contas_receber import contas_receber_bp
from routes.contas_pagar import contas_pagar_bp
from routes.push import push_bp
from routes.dashboard import dashboard_bp
from routes.whatsapp import whatsapp_bp
import os

# Configuração do Flask
app = Flask(__name__)
app.config.from_object(Config)

# Configurações adicionais para templates
app.config['WHATSAPP_API_URL'] = os.getenv('WHATSAPP_API_URL', 'http://localhost:4000')

# Logar a URL efetiva da API WhatsApp utilizada pelo Flask
try:
    _dev_api = os.getenv('WHATSAPP_API_URL', 'http://localhost:4000')
    _prod_api = os.getenv('WHATSAPP_API_URL_PRODUCTION', '')
    _effective_api = _prod_api if (_prod_api and _prod_api != 'http://localhost:4000') else _dev_api
    print(f"🔗 [FLASK-BOOT] WHATSAPP_API_URL (dev): {_dev_api}")
    print(f"🔗 [FLASK-BOOT] WHATSAPP_API_URL_PRODUCTION: {_prod_api}")
    print(f"✅ [FLASK-BOOT] URL efetiva usada pelo Flask para chamar o Node: {_effective_api}")
except Exception as _e:
    print(f"⚠️ [FLASK-BOOT] Falha ao determinar URL efetiva da API WhatsApp: {_e}")

# Validar variáveis de ambiente obrigatórias
if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
    print("ERRO: SUPABASE_URL e SUPABASE_KEY são obrigatórias")
    print("Certifique-se de configurar todas as variáveis de ambiente obrigatórias.")
    exit(1)

# Registrando os Blueprints
app.register_blueprint(renovacao_bp)
app.register_blueprint(tasks_bp)
app.register_blueprint(sucesso_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(config_bp)
app.register_blueprint(services_bp)
app.register_blueprint(users_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(relatorios_bp)
app.register_blueprint(agenda_bp)
app.register_blueprint(login_bp)
app.register_blueprint(agendamento_bp)
app.register_blueprint(agenda_cliente_bp)
app.register_blueprint(lembrete_email_bp)
app.register_blueprint(financeiro_bp)
app.register_blueprint(check_health_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(vendas_bp)
app.register_blueprint(contas_receber_bp)
app.register_blueprint(contas_pagar_bp)
app.register_blueprint(push_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(whatsapp_bp)

# Middleware de log para cada requisição (inclui chamadas do Node)
@app.before_request
def log_request_info():
    try:
        full_url = request.url
        method = request.method
        origin = request.headers.get('Origin')
        user_agent = request.headers.get('User-Agent')
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        referer = request.headers.get('Referer')
        print(f"🔍 [FLASK-REQ] {method} {full_url} | IP: {ip} | Origin: {origin} | UA: {user_agent} | Referer: {referer}")
    except Exception as e:
        print(f"⚠️ [FLASK-REQ] Falha ao logar requisição: {e}")

@app.route("/")
def inicio():
    return redirect(url_for('dashboard.dashboard'))

@app.route("/health")
def health_check():
    """Endpoint de health check para o Render"""
    return {
        'status': 'healthy',
        'service': 'sua-agenda-flask',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'environment': os.getenv('FLASK_ENV', 'development')
    }

@app.route("/render-health")
def render_health_check():
    """Endpoint específico para health check do Render"""
    return {
        'status': 'healthy',
        'service': 'sua-agenda-flask',
        'timestamp': datetime.now().isoformat(),
        'uptime': 'running',
        'environment': os.getenv('FLASK_ENV', 'development')
    }


#if __name__ == '__main__':
#    serve(app, host='0.0.0.0', port=4000)


if __name__ == '__main__':
     app.run(host ='0.0.0.0', port=5000 , debug = True)