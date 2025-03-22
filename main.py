from flask import Flask, redirect, url_for
from services import services_bp
from users import users_bp
from clientes import clientes_bp
from relatorios import relatorios_bp
from agenda import agenda_bp
from login import login_bp
from agendamento import agendamento_bp
from agenda_cliente import agenda_cliente_bp
from lembrete_email import lembrete_email_bp, verificar_agendamentos  # Importe a função aqui
from config import config_bp
from payment import payment_bp
from sucesso import sucesso_bp
from tasks import tasks_bp
from renovacao import renovacao_bp
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

# Configuração do agendador



@app.route("/")
def inicio():
    return redirect(url_for('agenda_bp.renderizar_agenda'))

# Iniciar o agendador
if __name__ == '__main__':

    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
