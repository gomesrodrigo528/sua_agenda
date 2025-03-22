from flask import Blueprint, jsonify, request, render_template
from supabase import create_client, Client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase: Client = create_client(supabase_url, supabase_key)

# Criação do Blueprint
agenda_cliente_bp = Blueprint('agenda_cliente_bp', __name__)

# Rota para renderizar a página agenda_cliente.html
@agenda_cliente_bp.route('/agenda_cliente')
def render_agendamentos_page():
    return render_template('agenda_cliente.html')

@agenda_cliente_bp.route('/agenda_cliente/<email>', methods=['GET'])
def get_agendamentos_por_email(email):
    try:
        print(f"Buscando cliente com o email: {email}")
        # Buscar ID e nome do cliente usando o email
        cliente_result = supabase.table('clientes').select('id, nome_cliente').eq('email', email).execute()
        if not cliente_result.data:
            return jsonify({"erro": "Cliente não encontrado."}), 404

        cliente_id = cliente_result.data[0]['id']
        nome_cliente = cliente_result.data[0]['nome_cliente']

        # Buscar os agendamentos do cliente
        agendamentos_result = supabase.table('agenda').select('data', 'horario', 'servico_id', 'usuario_id', 'id_empresa').eq('cliente_id', cliente_id).neq('status', 'finalizado').execute()
        if not agendamentos_result.data:
            return jsonify({"mensagem": "Nenhum agendamento encontrado para este cliente."}), 404

        agendamentos = []

        for agendamento in agendamentos_result.data:
            # Buscar nome do serviço
            servico_result = supabase.table('servicos').select('nome_servico').eq('id', agendamento['servico_id']).execute()
            servico = servico_result.data[0]['nome_servico'] if servico_result.data else 'Desconhecido'

            # Buscar nome do profissional (usuário)
            usuario_result = supabase.table('usuarios').select('nome_usuario').eq('id', agendamento['usuario_id']).execute()
            usuario = usuario_result.data[0]['nome_usuario'] if usuario_result.data else 'Desconhecido'

            # Buscar informações da empresa (nome, logo e telefone)
            empresa_result = supabase.table('empresa').select('nome_empresa, logo, tel_empresa').eq('id', agendamento['id_empresa']).execute()
            empresa_info = {
                "nome": empresa_result.data[0]['nome_empresa'] if empresa_result.data and 'nome_empresa' in empresa_result.data[0] else 'Empresa desconhecida',
                "logo": empresa_result.data[0]['logo'] if empresa_result.data and 'logo' in empresa_result.data[0] else None,
                "telefone": empresa_result.data[0]['tel_empresa'] if empresa_result.data and 'tel_empresa' in empresa_result.data[0] else None
            }

            # Adicionar informações ao agendamento
            agendamentos.append({
                "data": agendamento['data'],
                "horario": agendamento['horario'],
                "servico": servico,
                "usuario": usuario,
                "empresa": empresa_info
            })

        # Retornar cliente e agendamentos
        return jsonify({
            "cliente": {
                "nome": nome_cliente
            },
            "agendamentos": agendamentos
        }), 200
    except Exception as e:
        print(f"Erro ao buscar agendamentos: {str(e)}")
        return jsonify({"erro": str(e)}), 500
