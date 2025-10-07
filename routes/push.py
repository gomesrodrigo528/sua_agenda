from flask import Blueprint, request, jsonify
from utils.vapid_keys import get_vapid_keys, get_vapid_public_key_base64
from pywebpush import webpush, WebPushException
import os
import json
from supabase_config import supabase

# Configuração do Supabase


push_bp = Blueprint('push_bp', __name__)

# Endpoint para fornecer a chave pública VAPID
@push_bp.route('/api/push/vapid_public', methods=['GET'])
def get_vapid_public():
    public_key_base64 = get_vapid_public_key_base64()
    return jsonify({'publicKey': public_key_base64})

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

def cancelar_notificacao_push(user_id, agendamento_id, agendamento_data, agendamento_hora, servico_nome):
    try:
        # Busca a subscription do usuário
        resp = supabase.table('push_subscriptions').select('subscription').eq('user_id', user_id).execute()
        if not resp.data:
            print(f"[PUSH] Nenhuma subscription encontrada para o usuário {user_id}")
            return
        subscription_info = json.loads(resp.data[0]['subscription'])
        private_key, public_key = get_vapid_keys()
        payload = {
            'title': 'Agendamento Cancelado',
            'body': f'Agendamento cancelado: {servico_nome} em {agendamento_data} às {agendamento_hora}',
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
        print(f"[PUSH] Notificação de cancelamento enviada para o usuário {user_id}")
    except WebPushException as ex:
        print(f"[PUSH] Erro ao enviar notificação de cancelamento: {ex}")
    except Exception as e:
        print(f"[PUSH] Erro inesperado no cancelamento: {e}")

@push_bp.route('/api/push/subscribe-cliente', methods=['POST'])
def subscribe_cliente():
    subscription_data = request.get_json()
    cliente_id = request.cookies.get('id_usuario_cliente')
    if not cliente_id:
        return jsonify({'error': 'Cliente não autenticado'}), 401
    
    data = {
        'endpoint': subscription_data['endpoint'],
        'keys': subscription_data['keys'],
        'subscription': subscription_data,
        'cliente_id': int(cliente_id)
    }
    
    # Verificar se já existe subscription para este cliente
    existing = supabase.table('push_subscriptions_clientes').select('id').eq('cliente_id', cliente_id).execute()
    if existing.data:
        supabase.table('push_subscriptions_clientes').update(data).eq('cliente_id', cliente_id).execute()
    else:
        supabase.table('push_subscriptions_clientes').insert(data).execute()

    return jsonify({'success': True})

def agendar_notificacao_push_cliente(cliente_id, agendamento_id, agendamento_data, agendamento_hora, servico_nome):
    try:
        # Busca a subscription do cliente
        resp = supabase.table('push_subscriptions_clientes').select('subscription').eq('cliente_id', cliente_id).execute()
        if not resp.data:
            print(f"[PUSH] Nenhuma subscription encontrada para o cliente {cliente_id}")
            return
        subscription_info = json.loads(resp.data[0]['subscription'])
        private_key, public_key = get_vapid_keys()
        payload = {
            'title': 'Agendamento Confirmado',
            'body': f'Seu agendamento foi confirmado: {servico_nome} em {agendamento_data} às {agendamento_hora}',
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
        print(f"[PUSH] Notificação de agendamento enviada para o cliente {cliente_id}")
    except WebPushException as ex:
        print(f"[PUSH] Erro ao enviar notificação de agendamento para cliente: {ex}")
    except Exception as e:
        print(f"[PUSH] Erro inesperado no agendamento para cliente: {e}")

def cancelar_notificacao_push_cliente(cliente_id, agendamento_id, agendamento_data, agendamento_hora, servico_nome):
    try:
        # Busca a subscription do cliente
        resp = supabase.table('push_subscriptions_clientes').select('subscription').eq('cliente_id', cliente_id).execute()
        if not resp.data:
            print(f"[PUSH] Nenhuma subscription encontrada para o cliente {cliente_id}")
            return
        subscription_info = json.loads(resp.data[0]['subscription'])
        private_key, public_key = get_vapid_keys()
        payload = {
            'title': 'Agendamento Cancelado',
            'body': f'Seu agendamento foi cancelado: {servico_nome} em {agendamento_data} às {agendamento_hora}',
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
        print(f"[PUSH] Notificação de cancelamento enviada para o cliente {cliente_id}")
    except WebPushException as ex:
        print(f"[PUSH] Erro ao enviar notificação de cancelamento para cliente: {ex}")
    except Exception as e:
        print(f"[PUSH] Erro inesperado no cancelamento para cliente: {e}") 
