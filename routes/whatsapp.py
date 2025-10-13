#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhatsApp CRM Multi-Tenant - Backend Flask
Gerencia conversas e mensagens via WhatsApp usando Baileys
Adaptado para sistema multi-tenant com Supabase
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_from_directory
from supabase_config import supabase
from datetime import datetime, date, timedelta
import json
import re
import os
import uuid
import base64
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do WhatsApp API
WHATSAPP_API_URL = os.getenv('WHATSAPP_API_URL', 'http://localhost:3000')
WHATSAPP_API_URL_PRODUCTION = os.getenv('WHATSAPP_API_URL_PRODUCTION', 'https://api.suaagenda.fun')

# Usar URL de produção se estiver em produção
def get_whatsapp_api_url():
    """Retorna a URL da API do WhatsApp baseada no ambiente"""
    if os.getenv('FLASK_ENV') == 'production':
        return WHATSAPP_API_URL_PRODUCTION
    return WHATSAPP_API_URL

whatsapp_bp = Blueprint('whatsapp', __name__)

# Configurações de upload
UPLOAD_FOLDER = 'static/uploads/whatsapp'
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'audio': {'mp3', 'wav', 'ogg', 'm4a', 'opus'},
    'video': {'mp4', 'avi', 'mov', 'webm'},
    'document': {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt', 'zip', 'rar'}
}

def send_global_notification(empresa_id, name, message, avatar, phone):
    """Envia notificação global para todos os usuários da empresa"""
    try:
        # Salvar notificação no banco para ser consumida pelo frontend
        notification_data = {
            'id_empresa': empresa_id,
            'name': name,
            'message': message,
            'avatar': avatar,
            'phone': phone,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        # Inserir na tabela de notificações (criar se não existir)
        try:
            supabase.table('whatsapp_notifications').insert(notification_data).execute()
            print(f"🔔 Notificação global salva: {name} - {message[:50]}...")
        except Exception as e:
            print(f"⚠️ Erro ao salvar notificação (tabela pode não existir): {e}")
            print(f"💡 Sistema funcionará com fallback direto das conversas")
            
    except Exception as e:
        print(f"❌ Erro ao enviar notificação global: {e}")

def verificar_login():
    """Verifica se o usuário está logado"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return None
    return user_id

def obter_id_empresa():
    """Obtém o ID da empresa do cookie"""
    return request.cookies.get('empresa_id')

def allowed_file(filename, file_type):
    """Verifica se o arquivo é permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def extract_name_from_phone(phone):
    """Extrai um nome legível do número de telefone"""
    # Remove caracteres não numéricos
    clean_phone = re.sub(r'\D', '', phone)
    
    # Se tem mais de 10 dígitos, tenta formatar
    if len(clean_phone) >= 10:
        # Formato: +55 (34) 99999-9999
        if len(clean_phone) >= 13:  # Com código do país
            return f"+{clean_phone[:2]} ({clean_phone[2:4]}) {clean_phone[4:9]}-{clean_phone[9:]}"
        elif len(clean_phone) >= 11:  # Sem código do país
            return f"({clean_phone[:2]}) {clean_phone[2:7]}-{clean_phone[7:]}"
    
    return clean_phone

def get_or_create_whatsapp_user(empresa_id, phone, profile_name=None, profile_picture=None):
    """Busca ou cria um usuário WhatsApp"""
    try:
        print(f"🔍 get_or_create_whatsapp_user chamada:")
        print(f"   Empresa ID: {empresa_id}")
        print(f"   Phone: {phone}")
        print(f"   Profile Name: {profile_name}")
        print(f"   Profile Picture: {profile_picture}")
        
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'\D', '', phone)
        print(f"🔍 Telefone limpo: {clean_phone}")
        
        # Busca usuário existente
        print(f"🔍 Buscando usuário existente...")
        user_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).eq('telefone', clean_phone).execute()
        print(f"🔍 Resposta da busca: {user_response}")
        
        if user_response.data:
            user = user_response.data[0]
            print(f"✅ Usuário existente encontrado: {user}")
            
            # Atualizar informações do perfil se fornecidas
            update_data = {}
            if profile_name and profile_name != user.get('nome_cliente'):
                update_data['nome_cliente'] = profile_name
                print(f"🔄 Atualizando nome do usuário {clean_phone}: {user.get('nome_cliente')} → {profile_name}")
            
            if profile_picture and profile_picture != user.get('avatar'):
                update_data['avatar'] = profile_picture
                print(f"🔄 Atualizando avatar do usuário {clean_phone}")
            elif not user.get('avatar'):
                # Se usuário não tem avatar, criar um baseado no nome
                import hashlib
                name = user.get('nome_cliente', clean_phone)
                avatar_url = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=007bff&color=fff&size=128"
                update_data['avatar'] = avatar_url
                print(f"🔄 Criando avatar padrão para usuário {clean_phone}")
            
            if update_data:
                print(f"🔄 Atualizando usuário com dados: {update_data}")
                supabase.table('whatsapp_users').update(update_data).eq('id_empresa', empresa_id).eq('telefone', clean_phone).execute()
                # Buscar usuário atualizado
                user_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).eq('telefone', clean_phone).execute()
                return user_response.data[0]
            
            return user
        
        # Cria novo usuário
        name = profile_name if profile_name else extract_name_from_phone(clean_phone)
        
        # Se não há foto de perfil, usar uma foto padrão para teste
        avatar_url = profile_picture
        if not avatar_url:
            # Usar uma foto padrão baseada no nome
            import urllib.parse
            encoded_name = urllib.parse.quote(name)
            avatar_url = f"https://ui-avatars.com/api/?name={encoded_name}&background=007bff&color=fff&size=128"
            print(f"🎨 Avatar gerado: {avatar_url}")
        
        user_data = {
            'id_empresa': empresa_id,
            'nome_cliente': name,
            'telefone': clean_phone,
            'avatar': avatar_url
        }
        
        print(f"👤 Criando novo usuário: {name} ({clean_phone})")
        if profile_picture:
            print(f"📸 Com foto de perfil: {profile_picture}")
        
        user_response = supabase.table('whatsapp_users').insert(user_data).execute()
        if not user_response.data:
            print(f"❌ Erro ao inserir usuário no banco")
            return None
            
        user = user_response.data[0]
        print(f"✅ Usuário criado com ID: {user['id']}")
        
        # Cria chat para o usuário
        chat_data = {
            'id_empresa': empresa_id,
            'user_id': user['id']
        }
        print(f"🔍 Criando chat com dados: {chat_data}")
        chat_response = supabase.table('whatsapp_chats').insert(chat_data).execute()
        print(f"🔍 Resposta da criação do chat: {chat_response}")
        
        if not chat_response.data:
            print(f"❌ Erro ao criar chat para usuário {user['id']}")
            return None
            
        print(f"✅ Chat criado com ID: {chat_response.data[0]['id']}")
        return user
        
    except Exception as e:
        print(f"❌ Erro ao buscar/criar usuário WhatsApp: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_chat_by_user_id(empresa_id, user_id):
    """Busca o chat de um usuário"""
    try:
        chat_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('user_id', user_id).execute()
        
        if chat_response.data:
            chat = chat_response.data[0]
            print(f"🔍 Chat encontrado: ID={chat['id']}, Status={chat.get('status', 'N/A')}")
            return chat
        else:
            print(f"❌ Chat não encontrado para user_id={user_id}, empresa_id={empresa_id}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar chat: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_chat_last_message(empresa_id, chat_id, message):
    """Atualiza a última mensagem e timestamp do chat"""
    try:
        supabase.table('whatsapp_chats').update({
            'ultima_mensagem': message,
            'ultima_atualizacao': datetime.now().isoformat()
        }).eq('id_empresa', empresa_id).eq('id', chat_id).execute()
    except Exception as e:
        print(f"Erro ao atualizar chat: {e}")

def update_unread_count(empresa_id, chat_id):
    """Atualiza o contador de mensagens não lidas"""
    try:
        # Conta mensagens recebidas e não lidas
        messages_response = supabase.table('whatsapp_messages').select('id').eq('id_empresa', empresa_id).eq('chat_id', chat_id).eq('direcao', 'recebida').eq('lida', False).execute()
        
        unread_count = len(messages_response.data) if messages_response.data else 0
        
        # Atualiza o chat com a contagem real
        supabase.table('whatsapp_chats').update({
            'mensagens_nao_lidas': unread_count
        }).eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
    except Exception as e:
        print(f"Erro ao atualizar contador de não lidas: {e}")

def send_automatic_message(empresa_id, chat_id, message_type):
    """Envia mensagem automática baseada na configuração"""
    try:
        # Buscar configurações
        config_response = supabase.table('whatsapp_crm_config').select('*').eq('id_empresa', empresa_id).execute()
        
        if not config_response.data:
            print(f"❌ Configurações não encontradas para empresa {empresa_id}")
            return False
        
        config = config_response.data[0]
        
        # Determinar mensagem baseada no tipo
        message = ""
        should_send = False
        
        if message_type == 'boas_vindas':
            message = config.get('mensagem_boas_vindas', '')
            should_send = config.get('ativar_mensagem_boas_vindas', False)
        elif message_type == 'finalizacao':
            message = config.get('mensagem_finalizacao', '')
            should_send = config.get('ativar_mensagem_finalizacao', False)
        elif message_type == 'ausente':
            message = config.get('mensagem_ausente', '')
            should_send = config.get('ativar_mensagem_ausente', False)
        
        if not should_send or not message.strip():
            print(f"⚠️ Mensagem automática {message_type} não está ativada ou vazia")
            return False
        
        # Buscar dados do chat e usuário
        chat_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        if not chat_response.data:
            print(f"❌ Chat {chat_id} não encontrado")
            return False
        
        chat = chat_response.data[0]
        
        user_response = supabase.table('whatsapp_users').select('telefone').eq('id', chat['user_id']).execute()
        if not user_response.data:
            print(f"❌ Usuário do chat {chat_id} não encontrado")
            return False
        
        phone = user_response.data[0]['telefone']
        
        # Enviar mensagem via Baileys
        try:
            import requests
            baileys_url = f"{get_whatsapp_api_url()}/send/{empresa_id}"
            
            print(f"🤖 Enviando mensagem automática ({message_type}):")
            print(f"   URL: {baileys_url}")
            print(f"   Telefone: {phone}")
            print(f"   Mensagem: {message[:50]}...")
            
            response = requests.post(baileys_url, json={
                'phone': phone,
                'message': message
            }, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Mensagem automática enviada com sucesso")
                    
                    # Salvar mensagem no banco
                    message_data = {
                        'id_empresa': empresa_id,
                        'chat_id': chat_id,
                        'direcao': 'enviada',
                        'mensagem': message,
                        'timestamp': datetime.now().isoformat(),
                        'lida': True,
                        'tipo_mensagem': 'texto',
                        'status_envio': 'enviada'
                    }
                    
                    supabase.table('whatsapp_messages').insert(message_data).execute()
                    
                    # Atualizar última mensagem do chat
                    update_chat_last_message(empresa_id, chat_id, message)
                    
                    return True
                else:
                    print(f"❌ Erro no Baileys: {result.get('error')}")
            else:
                print(f"❌ Erro HTTP do Baileys: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na comunicação com Baileys: {e}")
        
        return False
        
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem automática: {e}")
        import traceback
        traceback.print_exc()
        return False

def mark_messages_as_read(empresa_id, chat_id):
    """Marca todas as mensagens de um chat como lidas"""
    try:
        # Marca mensagens recebidas como lidas
        supabase.table('whatsapp_messages').update({
            'lida': True
        }).eq('id_empresa', empresa_id).eq('chat_id', chat_id).eq('direcao', 'recebida').eq('lida', False).execute()
        
        # Reseta contador do chat
        supabase.table('whatsapp_chats').update({
            'mensagens_nao_lidas': 0
        }).eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        print(f"✅ Mensagens do chat {chat_id} marcadas como lidas")
        
    except Exception as e:
        print(f"Erro ao marcar mensagens como lidas: {e}")

# ============= ROTAS =============

@whatsapp_bp.route('/whatsapp/config')
def whatsapp_config():
    """Página de configurações do CRM WhatsApp"""
    return render_template('whatsapp/config.html')

@whatsapp_bp.route('/whatsapp')
def whatsapp_dashboard():
    """Página principal do WhatsApp CRM"""
    # Verifica se o usuário está logado
    user_id = verificar_login()
    if not user_id:
        return redirect(url_for('login.login'))
    
    empresa_id = obter_id_empresa()
    if not empresa_id:
        return redirect(url_for('login.login'))
    
    return render_template('whatsapp/dashboard.html')

@whatsapp_bp.route('/whatsapp/chat/<int:chat_id>')
def whatsapp_chat(chat_id):
    """Página de conversa específica"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return redirect(url_for('login.login'))
        
        # Busca o chat
        chat_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        if not chat_response.data:
            return redirect(url_for('whatsapp.whatsapp_dashboard'))
        
        chat_info = chat_response.data[0]
        
        # Busca o usuário do chat
        user_response = supabase.table('whatsapp_users').select('*').eq('id', chat_info['user_id']).execute()
        
        if not user_response.data:
            return redirect(url_for('whatsapp.whatsapp_dashboard'))
        
        user_info = user_response.data[0]
        
        # Marca mensagens como lidas
        mark_messages_as_read(empresa_id, chat_id)
        
        return render_template('whatsapp/chat.html', chat={
            'chat_id': chat_info['id'],
            'user_id': user_info['id'],
            'name': user_info['nome_cliente'],
            'phone': user_info['telefone'],
            'avatar': user_info.get('avatar')
        })
        
    except Exception as e:
        print(f"❌ Erro ao carregar chat: {e}")
        return redirect(url_for('whatsapp.whatsapp_dashboard'))

@whatsapp_bp.route('/api/whatsapp/messages/<int:chat_id>')
def get_whatsapp_messages(chat_id):
    """Retorna todas as mensagens de um chat"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        messages_response = supabase.table('whatsapp_messages').select('''
            id,
            direcao,
            mensagem,
            timestamp,
            lida,
            tipo_mensagem,
            media_url,
            media_filename,
            thumbnail_url
        ''').eq('id_empresa', empresa_id).eq('chat_id', chat_id).order('timestamp', desc=False).execute()
        
        messages = []
        if messages_response.data:
            for msg in messages_response.data:
                messages.append({
                    'id': msg['id'],
                    'direction': 'sent' if msg['direcao'] == 'enviada' else 'received',
                    'message': msg['mensagem'],
                    'timestamp': msg['timestamp'],
                    'read_status': 1 if msg['lida'] else 0,
                    'message_type': msg['tipo_mensagem'] or 'text',
                    'media_url': msg['media_url'],
                    'media_filename': msg['media_filename'],
                    'thumbnail_url': msg['thumbnail_url']
                })
        
        return jsonify(messages)
        
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens: {e}")
        return jsonify({'error': 'Erro ao buscar mensagens'}), 500

@whatsapp_bp.route('/api/whatsapp/send', methods=['POST'])
def send_whatsapp_message():
    """Envia mensagem via WhatsApp"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        data = request.get_json()
        
        if not data or 'chat_id' not in data or 'message' not in data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        chat_id = data['chat_id']
        message = data['message'].strip()
        
        if not message:
            return jsonify({'error': 'Mensagem vazia'}), 400
        
        # Verificar se assinatura está ativada e adicionar nome do usuário
        try:
            config_response = supabase.table('whatsapp_crm_config').select('ativar_assinatura').eq('id_empresa', empresa_id).execute()
            
            if config_response.data and config_response.data[0].get('ativar_assinatura'):
                # Buscar nome do usuário logado
                user_id = verificar_login()
                
                if user_id:
                    user_response = supabase.table('usuarios').select('nome_usuario').eq('id', user_id).execute()
                    
                    if user_response.data:
                        user_name = user_response.data[0]['nome_usuario']
                        # Adicionar assinatura: nome com asterisco + quebra de linha + mensagem
                        message = f"*{user_name}*\n{message}"
                        print(f"✍️ Assinatura adicionada: {user_name}")
        except Exception as e:
            print(f"⚠️ Erro ao adicionar assinatura: {e}")
            # Continuar sem assinatura se houver erro
        
        # Busca o chat
        chat_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        if not chat_response.data:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        chat = chat_response.data[0]
        
        # Busca o usuário do chat
        user_response = supabase.table('whatsapp_users').select('telefone').eq('id', chat['user_id']).execute()
        
        if not user_response.data:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        phone = user_response.data[0]['telefone']
        
        # Envia mensagem via Baileys
        try:
            import requests
            baileys_url = f"{get_whatsapp_api_url()}/send/{empresa_id}"
            
            print(f"📤 Enviando mensagem via Baileys:")
            print(f"   URL: {baileys_url}")
            print(f"   Empresa ID: {empresa_id}")
            print(f"   Telefone: {phone}")
            print(f"   Mensagem: {message[:50]}...")
            
            response = requests.post(baileys_url, json={
                'phone': phone,
                'message': message
            }, timeout=10)
            
            print(f"📤 Response status: {response.status_code}")
            print(f"📤 Response text: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print(f"✅ Mensagem enviada via Baileys com sucesso")
                else:
                    print(f"❌ Erro no Baileys: {result.get('error')}")
            else:
                print(f"❌ Erro HTTP do Baileys: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro na comunicação com Baileys: {e}")
            import traceback
            traceback.print_exc()
        
        # Salva mensagem no banco
        message_data = {
            'id_empresa': empresa_id,
            'chat_id': chat_id,
            'direcao': 'enviada',
            'mensagem': message,
            'timestamp': datetime.now().isoformat(),
            'lida': True,
            'tipo_mensagem': 'texto',
            'status_envio': 'enviada'
        }
        
        supabase.table('whatsapp_messages').insert(message_data).execute()
        
        # Atualiza última mensagem do chat
        update_chat_last_message(empresa_id, chat_id, message)
        
        # Atualiza status para 'atendendo' quando atendente envia mensagem
        supabase.table('whatsapp_chats').update({
            'status': 'atendendo',
            'ultima_atualizacao': datetime.now().isoformat()
        }).eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        print(f"✅ Mensagem enviada para chat {chat_id}: {message[:50]}...")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Erro ao enviar mensagem: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Webhook chamado pelo Baileys quando chega mensagem nova"""
    try:
        print(f"🔔 Webhook recebido!")
        print(f"📊 Headers: {dict(request.headers)}")
        print(f"📊 Content-Type: {request.content_type}")
        
        data = request.get_json()
        print(f"📊 Dados recebidos: {data}")
        
        if not data or 'phone' not in data or 'message' not in data:
            print(f"❌ Dados inválidos no webhook")
            return jsonify({'error': 'Dados inválidos'}), 400
        
        phone = data['phone']
        message = data['message']
        message_type = data.get('message_type', 'texto')
        media_url = data.get('media_url')
        media_filename = data.get('media_filename')
        profile_name = data.get('profile_name')
        profile_picture = data.get('profile_picture')
        
        print(f"📱 Telefone: {phone}")
        print(f"💬 Mensagem: {message}")
        print(f"📄 Tipo: {message_type}")
        print(f"👤 Nome do perfil: {profile_name}")
        print(f"📸 Foto do perfil: {profile_picture}")
        
        # Obter empresa_id dos dados ou usar padrão
        empresa_id = data.get('empresa_id', 1)
        
        # Verificar se a empresa existe, se não, usar uma empresa existente
        try:
            empresa_response = supabase.table('empresa').select('id').eq('id', empresa_id).execute()
            if not empresa_response.data:
                # Buscar primeira empresa disponível
                empresas_response = supabase.table('empresa').select('id').limit(1).execute()
                if empresas_response.data:
                    empresa_id = empresas_response.data[0]['id']
                    print(f"🔄 Usando empresa ID: {empresa_id}")
                else:
                    print(f"❌ Nenhuma empresa encontrada no sistema")
                    return jsonify({'error': 'Nenhuma empresa encontrada'}), 500
        except Exception as e:
            print(f"❌ Erro ao verificar empresa: {e}")
            return jsonify({'error': 'Erro ao verificar empresa'}), 500
        
        print(f"📨 Webhook recebido de {phone}")
        if profile_name:
            print(f"👤 Nome do perfil: {profile_name}")
        else:
            print(f"👤 Sem nome do perfil para {phone}")
        if profile_picture:
            print(f"📸 Foto de perfil: {profile_picture}")
        else:
            print(f"📸 Sem foto de perfil para {phone}")
        
        # Busca ou cria usuário com informações do perfil
        print(f"🔍 Buscando/criando usuário para {phone} na empresa {empresa_id}")
        user = get_or_create_whatsapp_user(empresa_id, phone, profile_name, profile_picture)
        
        if not user:
            print(f"❌ Falha ao criar usuário para {phone}")
            return jsonify({'error': 'Erro ao criar usuário'}), 500
        
        print(f"✅ Usuário encontrado/criado: {user['nome_cliente']} (ID: {user['id']})")
        
        # Verificar se usuário foi criado corretamente
        print(f"🔍 Dados do usuário: {user}")
        
        # Busca chat do usuário
        print(f"🔍 Buscando chat para usuário {user['id']} na empresa {empresa_id}")
        chat = get_chat_by_user_id(empresa_id, user['id'])
        
        if not chat:
            print(f"❌ Chat não encontrado para usuário {user['id']}")
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        print(f"✅ Chat encontrado: ID={chat['id']}, Status={chat.get('status', 'N/A')}")
        
        # Salva mensagem no banco como NÃO LIDA
        message_data = {
            'id_empresa': empresa_id,
            'chat_id': chat['id'],
            'direcao': 'recebida',
            'mensagem': message,
            'timestamp': datetime.now().isoformat(),
            'lida': False,
            'tipo_mensagem': message_type,
            'media_url': media_url,
            'media_filename': media_filename,
            'status_envio': 'recebida'
        }
        
        supabase.table('whatsapp_messages').insert(message_data).execute()
        
        # Enviar notificação global
        send_global_notification(empresa_id, user['nome_cliente'], message, user.get('avatar'), phone)
        
        # Atualiza última mensagem
        update_chat_last_message(empresa_id, chat['id'], message)
        
        # Atualiza contador de não lidas
        update_unread_count(empresa_id, chat['id'])
        
        # Atualiza status: apenas conversas finalizadas voltam para 'aguardando'
        current_status = chat.get('status', 'aguardando')
        
        if current_status == 'finalizado':
            new_status = 'aguardando'  # Conversa finalizada volta para aguardando
            print(f"🔄 Conversa finalizada recebeu nova mensagem: {current_status} → {new_status}")
        else:
            new_status = current_status  # Mantém o status atual (aguardando ou atendendo)
            print(f"🔄 Conversa em {current_status} recebeu mensagem: mantém status {new_status}")
        
        print(f"🔄 Atualizando status da conversa {chat['id']}: {current_status} → {new_status}")
        
        supabase.table('whatsapp_chats').update({
            'status': new_status,
            'ultima_atualizacao': datetime.now().isoformat()
        }).eq('id_empresa', empresa_id).eq('id', chat['id']).execute()
        
        print(f"✅ Status atualizado com sucesso: {current_status} → {new_status}")
        
        # Enviar mensagem de boas-vindas se for primeira mensagem do chat
        try:
            # Verificar se é a primeira mensagem do chat
            messages_count = supabase.table('whatsapp_messages').select('id').eq('id_empresa', empresa_id).eq('chat_id', chat['id']).execute()
            
            if messages_count.data and len(messages_count.data) == 1:  # Primeira mensagem
                print(f"🎉 Primeira mensagem do chat {chat['id']}, enviando boas-vindas...")
                send_automatic_message(empresa_id, chat['id'], 'boas_vindas')
        except Exception as e:
            print(f"⚠️ Erro ao enviar mensagem de boas-vindas: {e}")
        
        emoji = {'image': '📷', 'audio': '🎵', 'video': '🎥', 'document': '📄'}.get(message_type, '📨')
        print(f"{emoji} Mensagem recebida de {user['nome_cliente']} ({phone}): {message[:50]}...")
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Erro no webhook: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/chats')
def get_whatsapp_chats():
    """Retorna lista de chats com status"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Busca todos os usuários primeiro (mais eficiente)
        users_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).execute()
        users_dict = {user['id']: user for user in users_response.data} if users_response.data else {}
        
        # Busca os chats
        chats_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).order('ultima_atualizacao', desc=True).execute()
        
        chats = []
        if chats_response.data:
            for chat in chats_response.data:
                user = users_dict.get(chat['user_id'])
                if user:
                    chats.append({
                        'chat_id': chat['id'],
                        'user_id': user['id'],
                        'name': user['nome_cliente'],
                        'phone': user['telefone'],
                        'avatar': user.get('avatar'),
                        'last_message': chat['ultima_mensagem'] or 'Sem mensagens',
                        'last_update': chat['ultima_atualizacao'],
                        'unread_count': chat['mensagens_nao_lidas'],
                        'status': chat.get('status', 'aguardando')
                    })
        
        return jsonify(chats)
        
    except Exception as e:
        print(f"❌ Erro ao buscar chats: {e}")
        return jsonify({'error': 'Erro ao buscar chats'}), 500

@whatsapp_bp.route('/api/whatsapp/chats/aguardando')
def get_whatsapp_chats_aguardando():
    """Retorna lista de chats aguardando atendimento"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Busca todos os usuários primeiro (mais eficiente)
        users_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).execute()
        users_dict = {user['id']: user for user in users_response.data} if users_response.data else {}
        
        # Busca os chats aguardando
        chats_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('status', 'aguardando').order('ultima_atualizacao', desc=True).execute()
        
        chats = []
        if chats_response.data:
            for chat in chats_response.data:
                user = users_dict.get(chat['user_id'])
                if user:
                    chats.append({
                        'chat_id': chat['id'],
                        'user_id': user['id'],
                        'name': user['nome_cliente'],
                        'phone': user['telefone'],
                        'avatar': user.get('avatar'),
                        'last_message': chat['ultima_mensagem'] or 'Sem mensagens',
                        'last_update': chat['ultima_atualizacao'],
                        'unread_count': chat['mensagens_nao_lidas'],
                        'status': chat.get('status', 'aguardando')
                    })
        
        return jsonify(chats)
        
    except Exception as e:
        print(f"❌ Erro ao buscar chats aguardando: {e}")
        return jsonify({'error': 'Erro ao buscar chats aguardando'}), 500

@whatsapp_bp.route('/api/whatsapp/chats/atendendo')
def get_whatsapp_chats_atendendo():
    """Retorna lista de chats em atendimento"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Busca todos os usuários primeiro (mais eficiente)
        users_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).execute()
        users_dict = {user['id']: user for user in users_response.data} if users_response.data else {}
        
        # Busca os chats em atendimento
        chats_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('status', 'atendendo').order('ultima_atualizacao', desc=True).execute()
        
        chats = []
        if chats_response.data:
            for chat in chats_response.data:
                user = users_dict.get(chat['user_id'])
                if user:
                    chats.append({
                        'chat_id': chat['id'],
                        'user_id': user['id'],
                        'name': user['nome_cliente'],
                        'phone': user['telefone'],
                        'avatar': user.get('avatar'),
                        'last_message': chat['ultima_mensagem'] or 'Sem mensagens',
                        'last_update': chat['ultima_atualizacao'],
                        'unread_count': chat['mensagens_nao_lidas'],
                        'status': chat.get('status', 'atendendo')
                    })
        
        return jsonify(chats)
        
    except Exception as e:
        print(f"❌ Erro ao buscar chats em atendimento: {e}")
        return jsonify({'error': 'Erro ao buscar chats em atendimento'}), 500

@whatsapp_bp.route('/api/whatsapp/chats/<int:chat_id>/status', methods=['PUT'])
def update_chat_status(chat_id):
    """Atualiza o status de uma conversa"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({'error': 'Status é obrigatório'}), 400
        
        new_status = data['status']
        valid_statuses = ['aguardando', 'atendendo', 'finalizado']
        
        if new_status not in valid_statuses:
            return jsonify({'error': f'Status inválido. Use: {", ".join(valid_statuses)}'}), 400
        
        # Verificar se o chat existe e pertence à empresa
        chat_response = supabase.table('whatsapp_chats').select('*').eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        if not chat_response.data:
            return jsonify({'error': 'Chat não encontrado'}), 404
        
        # Atualizar status
        update_response = supabase.table('whatsapp_chats').update({
            'status': new_status,
            'ultima_atualizacao': datetime.now().isoformat()
        }).eq('id_empresa', empresa_id).eq('id', chat_id).execute()
        
        if update_response.data:
            print(f"✅ Status do chat {chat_id} atualizado para {new_status}")
            
            # Enviar mensagem de finalização se status for 'finalizado'
            if new_status == 'finalizado':
                try:
                    print(f"🏁 Conversa finalizada, enviando mensagem de finalização...")
                    send_automatic_message(empresa_id, chat_id, 'finalizacao')
                except Exception as e:
                    print(f"⚠️ Erro ao enviar mensagem de finalização: {e}")
            
            return jsonify({
                'success': True,
                'message': f'Status atualizado para {new_status}',
                'chat_id': chat_id,
                'status': new_status
            })
        else:
            return jsonify({'error': 'Erro ao atualizar status'}), 500
        
    except Exception as e:
        print(f"❌ Erro ao atualizar status do chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/test-supabase')
def test_supabase():
    """Testa a conexão com o Supabase"""
    try:
        # Testar conexão com Supabase
        response = supabase.table('whatsapp_users').select('count').execute()
        print(f"✅ Conexão com Supabase OK: {response}")
        
        return jsonify({
            'success': True,
            'message': 'Conexão com Supabase funcionando',
            'response': str(response)
        })
        
    except Exception as e:
        print(f"❌ Erro na conexão com Supabase: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@whatsapp_bp.route('/api/whatsapp/list-empresas')
def list_empresas():
    """Lista empresas existentes"""
    try:
        # Buscar empresas existentes
        empresas_response = supabase.table('empresa').select('id, nome_empresa').execute()
        
        if empresas_response.data:
            empresas = empresas_response.data
            print(f"🏢 Empresas encontradas: {len(empresas)}")
            for emp in empresas:
                print(f"   ID: {emp['id']}, Nome: {emp['nome_empresa']}")
            
            return jsonify({
                'success': True,
                'empresas': empresas
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nenhuma empresa encontrada'
            }), 404
        
    except Exception as e:
        print(f"❌ Erro ao listar empresas: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@whatsapp_bp.route('/api/whatsapp/test-direct-user')
def test_direct_user():
    """Testa criação direta de usuário"""
    try:
        # Testar criação direta sem webhook
        empresa_id = 1
        phone = '5534999999999'
        name = 'João Silva Teste'
        
        print(f"🧪 Testando criação direta de usuário...")
        
        # Limpar usuário existente primeiro
        try:
            supabase.table('whatsapp_users').delete().eq('id_empresa', empresa_id).eq('telefone', phone).execute()
            print(f"🗑️ Usuário existente removido")
        except:
            pass
        
        # Criar usuário
        user_data = {
            'id_empresa': empresa_id,
            'nome_cliente': name,
            'telefone': phone,
            'avatar': 'https://ui-avatars.com/api/?name=João+Silva+Teste&background=007bff&color=fff&size=128'
        }
        
        print(f"📝 Dados do usuário: {user_data}")
        
        user_response = supabase.table('whatsapp_users').insert(user_data).execute()
        
        if user_response.data:
            user = user_response.data[0]
            print(f"✅ Usuário criado: {user}")
            
            # Criar chat
            chat_data = {
                'id_empresa': empresa_id,
                'user_id': user['id']
            }
            
            chat_response = supabase.table('whatsapp_chats').insert(chat_data).execute()
            
            if chat_response.data:
                chat = chat_response.data[0]
                print(f"✅ Chat criado: {chat}")
                
                return jsonify({
                    'success': True,
                    'message': 'Usuário e chat criados com sucesso',
                    'user': user,
                    'chat': chat
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Erro ao criar chat',
                    'user': user
                }), 500
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao criar usuário',
                'response': str(user_response)
            }), 500
        
    except Exception as e:
        print(f"❌ Erro no teste direto: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@whatsapp_bp.route('/api/whatsapp/test-create-user')
def test_create_user():
    """Testa a criação de usuário"""
    try:
        empresa_id = 1
        phone = '5534999999999'
        name = 'João Silva Teste'
        
        # Testar criação de usuário
        user_data = {
            'id_empresa': empresa_id,
            'nome_cliente': name,
            'telefone': phone,
            'avatar': 'https://ui-avatars.com/api/?name=João+Silva+Teste&background=007bff&color=fff&size=128'
        }
        
        print(f"🧪 Testando criação de usuário: {user_data}")
        
        user_response = supabase.table('whatsapp_users').insert(user_data).execute()
        
        if user_response.data:
            print(f"✅ Usuário criado: {user_response.data[0]}")
            return jsonify({
                'success': True,
                'message': 'Usuário criado com sucesso',
                'user': user_response.data[0]
            })
        else:
            print(f"❌ Erro ao criar usuário: {user_response}")
            return jsonify({
                'success': False,
                'error': 'Erro ao criar usuário',
                'response': str(user_response)
            }), 500
        
    except Exception as e:
        print(f"❌ Erro no teste de criação: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@whatsapp_bp.route('/api/whatsapp/config')
def get_crm_config():
    """Retorna configurações do CRM"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Buscar configurações
        config_response = supabase.table('whatsapp_crm_config').select('*').eq('id_empresa', empresa_id).execute()
        
        if config_response.data:
            config = config_response.data[0]
            return jsonify(config)
        else:
            # Criar configurações padrão se não existir
            default_config = {
                'id_empresa': empresa_id,
                'mensagem_boas_vindas': 'Olá! Como posso ajudá-lo hoje?',
                'mensagem_finalizacao': 'Obrigado por entrar em contato! Tenha um ótimo dia!',
                'mensagem_ausente': 'Desculpe, não estou disponível no momento. Deixe sua mensagem que retornarei em breve.',
                'mensagem_rapida_1': 'Obrigado pelo contato!',
                'mensagem_rapida_2': 'Em que posso ajudá-lo?',
                'mensagem_rapida_3': 'Precisa de mais alguma coisa?',
                'mensagem_rapida_4': 'Tenha um ótimo dia!',
                'mensagem_rapida_5': 'Volte sempre!',
                'tempo_resposta_automatica': 30,
                'ativar_mensagem_boas_vindas': True,
                'ativar_mensagem_finalizacao': True,
                'ativar_mensagem_ausente': False,
                'horario_atendimento_inicio': '08:00:00',
                'horario_atendimento_fim': '18:00:00',
                'dias_atendimento': 'segunda,terca,quarta,quinta,sexta',
                'ativar_assinatura': False,
                'notificar_nova_mensagem': True,
                'notificar_mensagem_nao_lida': True,
                'som_notificacao': 'padrao',
                'tema_interface': 'claro',
                'mostrar_online': True,
                'mostrar_ultima_vez': True
            }
            
            create_response = supabase.table('whatsapp_crm_config').insert(default_config).execute()
            if create_response.data:
                return jsonify(create_response.data[0])
            else:
                return jsonify({'error': 'Erro ao criar configurações'}), 500
        
    except Exception as e:
        print(f"❌ Erro ao buscar configurações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/config', methods=['PUT'])
def update_crm_config():
    """Atualiza configurações do CRM"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Remover campos que não devem ser atualizados
        data.pop('id', None)
        data.pop('id_empresa', None)
        data.pop('created_at', None)
        data.pop('updated_at', None)
        
        # Atualizar configurações
        update_response = supabase.table('whatsapp_crm_config').update(data).eq('id_empresa', empresa_id).execute()
        
        if update_response.data:
            print(f"✅ Configurações atualizadas para empresa {empresa_id}")
            return jsonify({
                'success': True,
                'message': 'Configurações atualizadas com sucesso',
                'config': update_response.data[0]
            })
        else:
            return jsonify({'error': 'Erro ao atualizar configurações'}), 500
        
    except Exception as e:
        print(f"❌ Erro ao atualizar configurações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@whatsapp_bp.route('/static/uploads/whatsapp/<path:filename>')
def serve_whatsapp_media(filename):
    """Serve arquivos de mídia do WhatsApp"""
    try:
        # Caminho para os arquivos de mídia do Node.js
        media_path = os.path.join('..', 'node_whatsapp', 'static', 'uploads', 'whatsapp', filename)
        
        if os.path.exists(media_path):
            return send_from_directory(os.path.dirname(media_path), os.path.basename(media_path))
        else:
            return jsonify({'error': 'Arquivo não encontrado'}), 404
            
    except Exception as e:
        print(f"❌ Erro ao servir mídia: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/config/mensagens-rapidas')
def get_mensagens_rapidas():
    """Retorna mensagens rápidas configuradas"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Buscar configurações
        config_response = supabase.table('whatsapp_crm_config').select('mensagem_rapida_1, mensagem_rapida_2, mensagem_rapida_3, mensagem_rapida_4, mensagem_rapida_5').eq('id_empresa', empresa_id).execute()
        
        if config_response.data:
            config = config_response.data[0]
            mensagens = [
                config.get('mensagem_rapida_1', ''),
                config.get('mensagem_rapida_2', ''),
                config.get('mensagem_rapida_3', ''),
                config.get('mensagem_rapida_4', ''),
                config.get('mensagem_rapida_5', '')
            ]
            # Filtrar mensagens vazias
            mensagens = [msg for msg in mensagens if msg.strip()]
            return jsonify(mensagens)
        else:
            return jsonify([])
        
    except Exception as e:
        print(f"❌ Erro ao buscar mensagens rápidas: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/chats/stats')
def get_chats_stats():
    """Retorna estatísticas das conversas por status"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Buscar contagem por status
        chats_response = supabase.table('whatsapp_chats').select('status').eq('id_empresa', empresa_id).execute()
        
        stats = {
            'aguardando': 0,
            'atendendo': 0,
            'finalizado': 0,
            'total': 0
        }
        
        if chats_response.data:
            for chat in chats_response.data:
                status = chat.get('status', 'aguardando')
                if status in stats:
                    stats[status] += 1
                stats['total'] += 1
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"❌ Erro ao buscar estatísticas: {e}")
        return jsonify({'error': 'Erro ao buscar estatísticas'}), 500

@whatsapp_bp.route('/api/whatsapp/create_chat', methods=['POST'])
def create_whatsapp_chat():
    """Cria um novo chat/usuário"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        data = request.get_json()
        
        if not data or 'phone' not in data:
            return jsonify({'error': 'Telefone é obrigatório'}), 400
        
        phone = data['phone']
        
        # Busca ou cria usuário
        user = get_or_create_whatsapp_user(empresa_id, phone)
        
        if not user:
            return jsonify({'error': 'Erro ao criar usuário'}), 500
        
        # Busca chat do usuário
        chat = get_chat_by_user_id(empresa_id, user['id'])
        
        if not chat:
            return jsonify({'error': 'Erro ao criar chat'}), 500
        
        print(f"✅ Chat criado/encontrado para {user['nome_cliente']} ({phone})")
        return jsonify({'chat_id': chat['id'], 'user': user})
        
    except Exception as e:
        print(f"❌ Erro ao criar chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/update_user', methods=['PUT'])
def update_whatsapp_user():
    """Atualiza o nome de um usuário"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'name' not in data:
            return jsonify({'error': 'user_id e name são obrigatórios'}), 400
        
        user_id = data['user_id']
        name = data['name'].strip()
        
        if not name:
            return jsonify({'error': 'Nome não pode ser vazio'}), 400
        
        # Verifica se usuário existe
        user_response = supabase.table('whatsapp_users').select('*').eq('id_empresa', empresa_id).eq('id', user_id).execute()
        
        if not user_response.data:
            return jsonify({'error': 'Usuário não encontrado'}), 404
        
        # Atualiza o nome
        supabase.table('whatsapp_users').update({
            'nome_cliente': name,
            'updated_at': datetime.now().isoformat()
        }).eq('id_empresa', empresa_id).eq('id', user_id).execute()
        
        print(f"✅ Nome do usuário {user_id} atualizado para: {name}")
        return jsonify({'success': True, 'name': name})
        
    except Exception as e:
        print(f"❌ Erro ao atualizar usuário: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/mark_as_read/<int:chat_id>', methods=['POST'])
def mark_whatsapp_as_read(chat_id):
    """Marca mensagens de um chat como lidas"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        mark_messages_as_read(empresa_id, chat_id)
        return jsonify({'success': True})
        
    except Exception as e:
        print(f"❌ Erro ao marcar como lido: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/whatsapp/health')
def whatsapp_health_check():
    """Endpoint para verificar se o servidor está funcionando"""
    return jsonify({'status': 'ok', 'service': 'whatsapp-crm-multitenant'})

@whatsapp_bp.route('/whatsapp/test-api-connection')
def test_api_connection():
    """Testa a conexão com a API Node.js (endpoint público para testes)"""
    try:
        import requests
        api_url = get_whatsapp_api_url()
        
        # Testar health da API
        response = requests.get(f'{api_url}/health', timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            
            # Testar status da API
            status_response = requests.get(f'{api_url}/status', timeout=10)
            status_data = status_response.json() if status_response.status_code == 200 else None
            
            return jsonify({
                'success': True,
                'api_url': api_url,
                'environment': os.getenv('FLASK_ENV', 'development'),
                'health': health_data,
                'status': status_data,
                'message': 'Conexão com API Node.js funcionando perfeitamente!'
            })
        else:
            return jsonify({
                'success': False,
                'api_url': api_url,
                'error': f'API retornou status {response.status_code}',
                'message': 'Erro na conexão com a API Node.js'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'api_url': get_whatsapp_api_url(),
            'error': str(e),
            'message': 'Erro ao conectar com a API Node.js'
        }), 500

@whatsapp_bp.route('/api/whatsapp/status')
def api_whatsapp_status():
    """API para verificar status da conexão WhatsApp"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 401
        
        # Verificar status no servidor Baileys
        import requests
        try:
            response = requests.get(f'{get_whatsapp_api_url()}/status', timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('connections'):
                    connection = data['connections'].get(str(empresa_id))
                    if connection and connection.get('connected'):
                        return jsonify({
                            'success': True,
                            'connected': True,
                            'user': connection.get('user', {})
                        })
                    else:
                        return jsonify({
                            'success': True,
                            'connected': False,
                            'user': None
                        })
                else:
                    return jsonify({
                        'success': True,
                        'connected': False,
                        'user': None
                    })
            else:
                return jsonify({
                    'success': False,
                    'connected': False,
                    'error': 'Servidor Baileys não disponível'
                })
        except requests.exceptions.RequestException as e:
            return jsonify({
                'success': False,
                'connected': False,
                'error': 'Servidor Baileys não disponível'
            })
        
    except Exception as e:
        print(f"❌ Erro ao verificar status: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@whatsapp_bp.route('/api/whatsapp/webhook/status', methods=['POST'])
def webhook_status():
    """Webhook para receber atualizações de status do Baileys"""
    try:
        data = request.get_json()
        empresa_id = data.get('empresa_id')
        status = data.get('status')
        qr_code = data.get('qr_code')
        timestamp = data.get('timestamp')
        
        print(f"📡 Webhook status recebido - Empresa: {empresa_id}, Status: {status}")
        
        # Aqui você pode implementar:
        # 1. Salvar no banco de dados
        # 2. Enviar notificação via WebSocket
        # 3. Atualizar cache
        
        # Por enquanto, apenas log
        print(f"✅ Status atualizado: Empresa {empresa_id} -> {status}")
        
        return jsonify({'success': True, 'message': 'Status recebido'})
        
    except Exception as e:
        print(f"❌ Erro no webhook de status: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@whatsapp_bp.route('/api/whatsapp/notifications', methods=['GET'])
def get_notifications():
    """Busca notificações não lidas para a empresa"""
    try:
        empresa_id = obter_id_empresa()
        if not empresa_id:
            return jsonify({'error': 'Empresa não identificada'}), 400
        
        # Buscar notificações não lidas dos últimos 5 minutos
        five_minutes_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        
        try:
            response = supabase.table('whatsapp_notifications')\
                .select('*')\
                .eq('id_empresa', empresa_id)\
                .eq('read', False)\
                .gte('timestamp', five_minutes_ago)\
                .order('timestamp', desc=True)\
                .limit(10)\
                .execute()
            
            notifications = response.data if response.data else []
            
            # Marcar como lidas
            if notifications:
                notification_ids = [n['id'] for n in notifications]
                supabase.table('whatsapp_notifications')\
                    .update({'read': True})\
                    .in_('id', notification_ids)\
                    .execute()
            
            return jsonify({
                'success': True,
                'notifications': notifications
            })
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar notificações (tabela pode não existir): {e}")
            # Fallback: buscar conversas com mensagens não lidas
            try:
                response = supabase.table('whatsapp_chats')\
                    .select('*')\
                    .eq('id_empresa', empresa_id)\
                    .gt('mensagens_nao_lidas', 0)\
                    .order('ultima_atualizacao', desc=True)\
                    .limit(5)\
                    .execute()
                
                chats = response.data if response.data else []
                
                # Converter chats em formato de notificação
                notifications = []
                for chat in chats:
                    # Buscar dados do usuário
                    user_response = supabase.table('whatsapp_users')\
                        .select('nome_cliente, avatar, telefone')\
                        .eq('id', chat['user_id'])\
                        .execute()
                    
                    if user_response.data:
                        user = user_response.data[0]
                        notifications.append({
                            'name': user['nome_cliente'],
                            'message': chat.get('ultima_mensagem', 'Nova mensagem'),
                            'avatar': user.get('avatar'),
                            'phone': user['telefone'],
                            'timestamp': chat['ultima_atualizacao']
                        })
                
                return jsonify({
                    'success': True,
                    'notifications': notifications
                })
                
            except Exception as fallback_error:
                print(f"❌ Erro no fallback de notificações: {fallback_error}")
                return jsonify({
                    'success': True,
                    'notifications': []
                })
        
    except Exception as e:
        print(f"❌ Erro ao buscar notificações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
