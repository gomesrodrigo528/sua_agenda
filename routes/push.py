from flask import Blueprint, request, jsonify
import json
from pywebpush import webpush, WebPushException
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from utils.vapid_keys import get_vapid_keys

push_bp = Blueprint('push_bp', __name__)
subscriptions = {}  # Em produção, use banco de dados

VAPID_PRIVATE_KEY, VAPID_PUBLIC_KEY = get_vapid_keys()
VAPID_CLAIMS = {"sub": "mailto:seu@email.com"}

scheduler = BackgroundScheduler()
scheduler.start()

@push_bp.route('/api/push/subscribe', methods=['POST'])
def push_subscribe():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    subscriptions[user_id] = request.json
    return jsonify({'success': True})

def enviar_push(user_id, title, body):
    subscription = subscriptions.get(user_id)
    if not subscription:
        return
    try:
        webpush(
            subscription_info=subscription,
            data=json.dumps({'title': title, 'body': body}),
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as ex:
        print("Erro ao enviar push:", ex)

def agendar_notificacao_push(user_id, agendamento_id, agendamento_data, agendamento_hora, servico_nome):
    agendamento_datetime = datetime.strptime(f'{agendamento_data} {agendamento_hora}', '%Y-%m-%d %H:%M')
    notificar_em = agendamento_datetime - timedelta(minutes=15)
    if notificar_em > datetime.now():
        scheduler.add_job(
            enviar_push,
            'date',
            run_date=notificar_em,
            args=[user_id, "Lembrete de Agendamento", f"Seu agendamento '{servico_nome}' começa em 15 minutos!"],
            id=f"push_{user_id}_{agendamento_id}",
            replace_existing=True
        )

@push_bp.route('/api/push/vapid_public', methods=['GET'])
def get_vapid_public():
    _, public_key = get_vapid_keys()
    # Converter PEM para base64 (remover cabeçalho e quebras de linha)
    if public_key.startswith('-----BEGIN PUBLIC KEY-----'):
        # Remove cabeçalho, rodapé e quebras de linha
        lines = public_key.split('\n')
        base64_key = ''.join([line for line in lines if line and not line.startswith('-----')])
        return jsonify({'publicKey': base64_key})
    return jsonify({'publicKey': public_key})

@push_bp.route('/api/push/teste', methods=['POST', 'GET'])
def push_teste():
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': 'Usuário não autenticado'}), 401
    enviar_push(user_id, 'Notificação de Teste', 'Esta é uma notificação push de teste!')
    return jsonify({'success': True, 'message': 'Notificação enviada (se houver subscription ativa).'}) 