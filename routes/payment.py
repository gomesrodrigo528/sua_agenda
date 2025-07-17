from flask import Blueprint, render_template, redirect, flash, request
from routes.api_mercadopago import gerar_link_pagamento
from supabase import create_client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

payment_bp = Blueprint('payment', __name__)

@payment_bp.route('/adquirir', methods=['GET'])
def payment():
    # Renderiza a página com os planos
    return render_template('payment.html')

@payment_bp.route('/adquirir/<plano>', methods=['GET'])
def process_payment(plano):
    try:
        # Validação de segurança: verificar se o plano é válido
        planos_validos = ['mensal', 'trimestral', 'anual', 'teste']
        if plano not in planos_validos:
            flash("Plano inválido!", "error")
            return redirect('/adquirir')
        
        # Se for teste gratuito, redirecionar diretamente para cadastro
        if plano == 'teste':
            return redirect('/pagamentoaprovado/teste')
        
        link_pagamento = gerar_link_pagamento(plano)
        if not link_pagamento:
            flash("Erro ao gerar link de pagamento. Tente novamente mais tarde.", "error")
            return redirect('/adquirir')
        return redirect(link_pagamento)
    except ValueError:
        flash("Plano inválido!", "error")
        return redirect('/adquirir')

@payment_bp.route('/renovar/<plano>', methods=['GET'])
def renovar_pagamento(plano):
    try:
        link_pagamento = gerar_link_pagamento(plano, tipo="renovacao")
        if not link_pagamento:
            flash("Erro ao gerar link de pagamento. Tente novamente mais tarde.", "error")
            return redirect('/renovacao')
        return redirect(link_pagamento)
    except ValueError:
        flash("Plano inválido!", "error")
        return redirect('/renovacao')

@payment_bp.route('/renovacao', methods=['GET'])
def renovacao():
    return render_template('planos_renovacao.html')

# Nova rota para validação de empresa
@payment_bp.route('/api/verificar-empresa', methods=['POST'])
def verificar_empresa():
    try:
        data = request.get_json()
        email = data.get('email')
        cnpj = data.get('cnpj')
        
        if not email or not cnpj:
            return {'error': 'Email e CNPJ são obrigatórios'}, 400
        
        # Verificar se a empresa já existe por email
        response_email = supabase.table('empresa').select('*').eq('email_empresa', email).execute()
        if response_email.data:
            empresa = response_email.data[0]
            return {
                'existe': True,
                'teste_ativo': empresa.get('teste_de_app', False),
                'dias_restantes': empresa.get('dias_restantes', 0)
            }
        
        # Verificar se a empresa já existe por CNPJ
        response_cnpj = supabase.table('empresa').select('*').eq('cnpj', cnpj).execute()
        if response_cnpj.data:
            empresa = response_cnpj.data[0]
            return {
                'existe': True,
                'teste_ativo': empresa.get('teste_de_app', False),
                'dias_restantes': empresa.get('dias_restantes', 0)
            }
        
        return {'existe': False}
        
    except Exception as e:
        return {'error': str(e)}, 500