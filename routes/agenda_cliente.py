from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from supabase_config import supabase
import os

# Criação do Blueprint
agenda_cliente_bp = Blueprint('agenda_cliente_bp', __name__)

# Função auxiliar para verificar se o cliente está logado
def verificar_cliente_logado():
    id_usuario_cliente = request.cookies.get('id_usuario_cliente')
    id_cliente = request.cookies.get('cliente_id')  # Corrigido: usar cliente_id em vez de id_cliente
    id_empresa = request.cookies.get('id_empresa')
    return id_usuario_cliente and id_cliente and id_empresa

# Rota para renderizar a página agenda_cliente.html
@agenda_cliente_bp.route('/agenda_cliente')
def render_agendamentos_page():
    # Remover verificação de autenticação aqui para permitir que a página carregue
    # A verificação será feita no JavaScript quando tentar buscar os agendamentos
    return render_template('agenda_cliente.html')

# Rota para API que retorna agendamentos em JSON
@agenda_cliente_bp.route('/api/agenda_cliente', methods=['GET'])
def api_agendamentos_cliente():
    return get_agendamentos_por_cookies()

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
        agendamentos_result = supabase.table('agenda').select('id, data, horario, servico_id, usuario_id, id_empresa').eq('cliente_id', cliente_id).eq('status', 'ativo').execute()
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
                "id": agendamento['id'],
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

def get_agendamentos_por_cookies():
    try:
        # Debug: imprimir todos os cookies recebidos
        print("=== DEBUG: Cookies recebidos ===")
        for cookie_name, cookie_value in request.cookies.items():
            print(f"  {cookie_name}: {cookie_value}")
        
        # Debug: imprimir todos os headers recebidos
        print("=== DEBUG: Headers recebidos ===")
        for header_name, header_value in request.headers.items():
            if 'usuario' in header_name.lower() or 'cliente' in header_name.lower():
                print(f"  {header_name}: {header_value}")
        
        # Buscar id_usuario_cliente do cookie ou header
        id_usuario_cliente = request.cookies.get('id_usuario_cliente') or request.headers.get('X-Usuario-Cliente')
        
        if not id_usuario_cliente:
            print("❌ Nenhum id_usuario_cliente encontrado")
            return jsonify({"erro": "Cliente não logado. Faça login novamente."}), 401
        
        print(f"✅ id_usuario_cliente encontrado: {id_usuario_cliente}")
        
        # Buscar todos os clientes comerciais vinculados a esse usuário
        clientes_resp = supabase.table('clientes').select('id, nome_cliente').eq('id_usuario_cliente', id_usuario_cliente).execute()
        clientes = clientes_resp.data if clientes_resp and clientes_resp.data else []
        
        print(f"🔍 Busca de clientes para id_usuario_cliente {id_usuario_cliente}: {len(clientes)} encontrados")
        
        if not clientes:
            print("❌ Nenhum cliente encontrado para este id_usuario_cliente")
            return jsonify({"erro": "Cliente não encontrado."}), 404
        
        ids_clientes = [c['id'] for c in clientes]
        nome_cliente = clientes[0]['nome_cliente']
        
        print(f"✅ Clientes encontrados: {ids_clientes} (nome: {nome_cliente})")
        
        # Buscar todos os agendamentos desses clientes
        agendamentos = []
        if ids_clientes:
            # Buscar agendamentos ativos
            agendamentos_result = supabase.table('agenda').select('id, data, horario, servico_id, usuario_id, id_empresa').in_('cliente_id', ids_clientes).eq('status', 'ativo').execute()
            
            print(f"🔍 Busca de agendamentos para clientes {ids_clientes}: {len(agendamentos_result.data) if agendamentos_result.data else 0} encontrados")
            
            if agendamentos_result.data:
                for agendamento in agendamentos_result.data:
                    print(f"  📅 Processando agendamento: {agendamento}")
                    
                    # Buscar nome do serviço
                    servico_result = supabase.table('servicos').select('nome_servico').eq('id', agendamento['servico_id']).execute()
                    servico = servico_result.data[0]['nome_servico'] if servico_result.data else 'Desconhecido'
                    
                    # Buscar nome do profissional (usuário)
                    usuario_result = supabase.table('usuarios').select('nome_usuario').eq('id', agendamento['usuario_id']).execute()
                    usuario = usuario_result.data[0]['nome_usuario'] if usuario_result.data else 'Desconhecido'
                    
                    # Buscar informações da empresa
                    empresa_result = supabase.table('empresa').select('nome_empresa, logo, tel_empresa').eq('id', agendamento['id_empresa']).execute()
                    empresa_info = {
                        "nome": empresa_result.data[0]['nome_empresa'] if empresa_result.data and 'nome_empresa' in empresa_result.data[0] else 'Empresa desconhecida',
                        "logo": empresa_result.data[0]['logo'] if empresa_result.data and 'logo' in empresa_result.data[0] else None,
                        "telefone": empresa_result.data[0]['tel_empresa'] if empresa_result.data and 'tel_empresa' in empresa_result.data[0] else None
                    }
                    
                    agendamento_processado = {
                        "id": agendamento['id'],
                        "data": agendamento['data'],
                        "horario": agendamento['horario'],
                        "servico": servico,
                        "usuario": usuario,
                        "empresa": empresa_info
                    }
                    
                    agendamentos.append(agendamento_processado)
                    print(f"  ✅ Agendamento processado: {agendamento_processado}")
        
        if not agendamentos:
            print("⚠️ Nenhum agendamento encontrado")
            return jsonify({"mensagem": "Nenhum agendamento encontrado para este cliente."}), 404
        
        resultado = {
            "cliente": {
                "nome": nome_cliente
            },
            "agendamentos": agendamentos
        }
        
        print(f"✅ Retornando {len(agendamentos)} agendamentos para {nome_cliente}")
        print(f"📋 Resultado final: {resultado}")
        
        return jsonify(resultado), 200
    except Exception as e:
        print(f"❌ Erro ao buscar agendamentos: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500
