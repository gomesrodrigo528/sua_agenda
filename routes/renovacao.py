from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from supabase import create_client
import os
import mercadopago

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Mercado Pago
MP_ACCESS_TOKEN = 'TEST-1242682277274715-060519-40f45c2b119be74c36a87e6263c9f5e5-1360530545'
mp = mercadopago.SDK(MP_ACCESS_TOKEN)

# Planos disponíveis
PLANOS = {
    'mensal':  {'nome': 'Plano Mensal',      'valor': 35.00,  'dias': 30},
    'trimestral': {'nome': 'Plano Trimestral',  'valor': 85.00,  'dias': 90},
    'anual':   {'nome': 'Plano Anual',       'valor': 125.00, 'dias': 365},
}

# Blueprint para renovação
renovacao_bp = Blueprint('renovacao', __name__)

@renovacao_bp.route('/renovar/<plano>')
def renovar_plano(plano):
    if plano not in PLANOS:
        flash('Plano inválido!', 'danger')
        return redirect(url_for('renovacao.planos_renovacao'))

    user_id = request.cookies.get('user_id')
    empresa_id = request.cookies.get('empresa_id')
    if not empresa_id:
        flash('Empresa não identificada. Faça login novamente.', 'danger')
        return redirect(url_for('login.login'))

    plano_info = PLANOS[plano]
    NGROK_BASE_URL = "https://8e4bfe71c016.ngrok-free.app"
    back_urls = {
        "success": f"{NGROK_BASE_URL}/renovacao-sucesso",
        "failure": f"{NGROK_BASE_URL}/renovacao-falha",
        "pending": f"{NGROK_BASE_URL}/renovacao-falha"
    }
    print("Back URLs geradas para Mercado Pago:", back_urls)
    preference_data = {
        "items": [
            {
                "title": plano_info['nome'],
                "quantity": 1,
                "currency_id": "BRL",
                "unit_price": float(plano_info['valor'])
            }
        ],
        "payer": {},
        "back_urls": back_urls,
        "auto_return": "approved",
        "metadata": {
            "empresa_id": empresa_id,
            "user_id": user_id,
            "plano": plano
        }
    }
    try:
        preference_result = mp.preference().create(preference_data)
        preference = preference_result.get("response", {})
        if "init_point" not in preference:
            # Log detalhado do erro
            print("Erro ao criar preferência Mercado Pago:", preference)
            flash('Erro ao iniciar pagamento. Verifique as credenciais do Mercado Pago ou tente novamente mais tarde.', 'danger')
            return redirect(url_for('renovacao.planos_renovacao'))
        return redirect(preference["init_point"])
    except Exception as e:
        print("Exceção ao criar preferência Mercado Pago:", e)
        flash('Erro inesperado ao iniciar pagamento. Tente novamente mais tarde.', 'danger')
        return redirect(url_for('renovacao.planos_renovacao'))

@renovacao_bp.route('/notificacao-pagamento', methods=['POST'])
def notificacao_pagamento():
    # Mercado Pago envia notificações de pagamento para cá
    data = request.json
    empresa_id = request.args.get('empresa_id')
    plano = request.args.get('plano')
    if not empresa_id or not plano or plano not in PLANOS:
        return jsonify({'error': 'Dados insuficientes'}), 400

    # Buscar status do pagamento
    if data and 'data' in data and 'id' in data['data']:
        payment_id = data['data']['id']
        payment = mp.payment().get(payment_id)["response"]
        if payment.get('status') == 'approved':
            # Atualizar dias_restantes
            empresa = supabase.table("empresa").select("dias_restantes").eq("id", empresa_id).execute().data
            if empresa:
                dias_atual = empresa[0]['dias_restantes'] or 0
                dias_novos = PLANOS[plano]['dias']
                novo_total = dias_atual + dias_novos
                supabase.table("empresa").update({"dias_restantes": novo_total, "acesso": True}).eq("id", empresa_id).execute()
            return jsonify({'status': 'ok'}), 200
    return jsonify({'status': 'ignored'}), 200

@renovacao_bp.route('/renovacao-sucesso')
def renovacao_sucesso():
    payment_id = request.args.get('payment_id')
    status = request.args.get('status')
    print(f"[DEBUG] payment_id recebido: {payment_id}")
    print(f"[DEBUG] status recebido: {status}")
    if not payment_id or status != 'approved':
        print('[DEBUG] Pagamento não aprovado ou payment_id ausente.')
        flash('Pagamento não aprovado ou inválido.', 'danger')
        return redirect(url_for('renovacao.planos_renovacao'))

    # Buscar detalhes do pagamento no Mercado Pago
    try:
        payment = mp.payment().get(payment_id)
        print(f"[DEBUG] Resposta do Mercado Pago: {payment}")
        payment_info = payment.get('response', {})
        metadata = payment_info.get('metadata', {})
        print(f"[DEBUG] Metadata recebido do pagamento: {metadata}")
        empresa_id = metadata.get('empresa_id')
        plano = metadata.get('plano')
        if not empresa_id or not plano:
            print('[DEBUG] Metadata incompleto: empresa_id ou plano ausente.')
            flash('Não foi possível identificar a empresa ou o plano.', 'danger')
            return redirect(url_for('renovacao.planos_renovacao'))
        # Atualizar dias_restantes conforme o plano
        dias = PLANOS.get(plano, {}).get('dias', 0)
        print(f"[DEBUG] Dias do plano: {dias}")
        if dias > 0:
            # Buscar dias atuais e somar
            empresa = supabase.table('empresa').select('dias_restantes').eq('id', empresa_id).single().execute()
            print(f"[DEBUG] Empresa encontrada: {empresa}")
            dias_atuais = empresa.data['dias_restantes'] if empresa.data and empresa.data['dias_restantes'] else 0
            novo_total = dias_atuais + dias
            print(f"[DEBUG] Atualizando dias_restantes para: {novo_total}")
            # Atualizar dias_restantes e acesso
            supabase.table('empresa').update({
                'dias_restantes': novo_total,
                'acesso': True
            }).eq('id', empresa_id).execute()
            print(f'Dias restantes atualizados para empresa {empresa_id}: {novo_total} e acesso ativado')
        else:
            print('[DEBUG] Plano inválido para atualização.')
            flash('Plano inválido para atualização.', 'danger')
            return redirect(url_for('renovacao.planos_renovacao'))
    except Exception as e:
        print('[DEBUG] Erro ao atualizar dias_restantes:', e)
        flash('Erro ao atualizar dias restantes. Contate o suporte.', 'danger')
        return redirect(url_for('renovacao.planos_renovacao'))
    print('[DEBUG] Renderizando página de sucesso!')
    return render_template('renovacao_sucesso.html')

@renovacao_bp.route('/renovacao-falha')
def renovacao_falha():
    return render_template('renovacao_falha.html')

@renovacao_bp.route('/planos-renovacao')
def planos_renovacao():
    return render_template('planos_renovacao.html')

# (As rotas antigas de renovação manual podem ser removidas se não forem mais usadas)


