from flask import Blueprint, request, jsonify
from utils.vapid_keys import get_vapid_keys
from pywebpush import webpush, WebPushException
import os
import json
from supabase import create_client

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

push_bp = Blueprint('push_bp', __name__)

# Endpoint para fornecer a chave pública VAPID
@push_bp.route('/api/push/vapid_public', methods=['GET'])
def get_vapid_public():
    _, public_key = get_vapid_keys()
    return jsonify({'publicKey': public_key})

# Endpoint para registrar a subscription do usuário
@push_bp.route('/api/push/subscribe', methods=['POST'])
def subscribe():
    subscription = request.get_json()
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    # Salva a subscription no Supabase
    data = {
        'user_id': user_id,
        'subscription': json.dumps(subscription)
    }
    # Tenta atualizar se já existe, senão insere
    existing = supabase.table('push_subscriptions').select('id').eq('user_id', user_id).execute()
    if existing.data:
        supabase.table('push_subscriptions').update(data).eq('user_id', user_id).execute()
    else:
        supabase.table('push_subscriptions').insert(data).execute()
    return jsonify({'success': True})

# Função utilitária para enviar notificação push

def agendar_notificacao_push(user_id, agendamento_id, agendamento_data, agendamento_hora, servico_nome):
    try:
        # Busca a subscription do usuário
        resp = supabase.table('push_subscriptions').select('subscription').eq('user_id', user_id).execute()
        if not resp.data:
            print(f"[PUSH] Nenhuma subscription encontrada para o usuário {user_id}")
            return
        subscription_info = json.loads(resp.data[0]['subscription'])
        private_key, public_key = get_vapid_keys()
        payload = {
            'title': 'Novo Agendamento',
            'body': f'Você tem um novo agendamento: {servico_nome} em {agendamento_data} às {agendamento_hora}',
            'agendamento_id': agendamento_id
        }
        webpush(
            subscription_info,
            json.dumps(payload),
            vapid_private_key=private_key,
            vapid_claims={
                "sub": "mailto:contato@suaagenda.fun"
            }
        )
        print(f"[PUSH] Notificação enviada para o usuário {user_id}")
    except WebPushException as ex:
        print(f"[PUSH] Erro ao enviar notificação push: {ex}")
    except Exception as e:
        print(f"[PUSH] Erro inesperado: {e}") 