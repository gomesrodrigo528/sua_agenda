from flask import Blueprint, render_template, redirect, flash
from api_mercadopago import gerar_link_pagamento



payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/adquirir', methods=['GET'])
def payment():
    # Renderiza a página com os planos
    return render_template('payment.html')

@payment_bp.route('/adquirir/<plano>', methods=['GET'])
def process_payment(plano):
    try:
        # Gerar o link de pagamento baseado no plano escolhido
        link_pagamento = gerar_link_pagamento(plano)
        return redirect(link_pagamento)  # Redireciona para o Mercado Pago
    except ValueError:
        flash("Plano inválido!", "error")
        return redirect('/adquirir')

@payment_bp.route('/renovar/<plano>', methods=['GET'])
def renovar_pagamento(plano):
    try:
        link_pagamento = gerar_link_pagamento(plano, tipo="renovacao")
        return redirect(link_pagamento)
    except ValueError:
        flash("Plano inválido!", "error")
        return redirect('/renovacao')

@payment_bp.route('/renovacao', methods=['GET'])
def renovacao():
    return render_template('planos_renovacao.html')