from flask import Flask, redirect, url_for
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
import os

# Configuração do Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

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

@app.route("/")
def inicio():
    return redirect(url_for('agenda_bp.renderizar_agenda'))

# Iniciar o agendador
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
