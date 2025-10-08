from flask import Blueprint, jsonify, request, render_template, session, redirect, url_for
from supabase_config import supabase
from utils.email_service import EmailService
from utils.servico_financeiro import obter_servico_padrao_financeiro
from routes.push import agendar_notificacao_push, cancelar_notificacao_push, agendar_notificacao_push_cliente, cancelar_notificacao_push_cliente
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# Criação do Blueprint
agenda_bp = Blueprint('agenda_bp', __name__)

def verificar_login():
    """Verifica se o usuário está logado - retorna True se não estiver logado"""
    return not request.cookies.get('user_id') or not request.cookies.get('empresa_id')
    
# Validação de Login
def obter_id_usuario():
    return request.cookies.get('user_id')

def obter_id_empresa():
    return request.cookies.get('empresa_id')


@agenda_bp.route('/api/empresa/logada', methods=['GET'])
def obter_dados_empresa_logada():
    # Verifica se os cookies estão presentes
    empresa_id = request.cookies.get('empresa_id')
    
    if not empresa_id:
        return jsonify({"erro": "Empresa não encontrada nos cookies"}), 401

    # Consulta a tabela para obter os dados da empresa logada
    response = supabase.table("empresa").select("logo, cor_emp,nome_empresa").eq("id", empresa_id).execute()

    if response.data:
        empresa = response.data[0]
        return jsonify({
            "logo": empresa.get("logo", "/static/img/logo.png"),
            "cor_emp": empresa.get("cor_emp", "#343a40"),
            "nome_empresa": empresa.get("nome_empresa", "Empresa não identificada")  # Inclui o nome da empresa
        }), 200
    else:
        return jsonify({"erro": "Dados da empresa não encontrados"}), 404


# Função para enviar e-mails
def enviar_email(destinatario, assunto, mensagem, email_remetente, senha_remetente):
    try:
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        servidor = smtplib.SMTP(servidor_smtp, porta_smtp)
        servidor.starttls()
        servidor.login(email_remetente, senha_remetente)
        servidor.sendmail(email_remetente, destinatario, msg.as_string())
        servidor.quit()

        print("E-mail enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para realizar o agendamento

@agenda_bp.route('/api/agendar', methods=['POST'])
def agendar():
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    dados = request.get_json()
    empresa_id = obter_id_empresa()

    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    # Inserindo no banco de dados com status "ativo"
    response = supabase.table("agenda").insert({
        "cliente_id": dados["cliente_id"],
        "usuario_id": dados["usuario_id"],
        "servico_id": dados["servico_id"],
        "data": dados["data"],
        "horario": dados["horario"],
        "descricao": dados.get("descricao"),
        "id_empresa": empresa_id,  # Associa o agendamento à empresa logada
        "status": "ativo",  # Definindo o status como "ativo"
        "visto": "True"
    }).execute()

    if response.data:
        empresa = supabase.table('empresa').select("email, senha_app, envia_email").eq('id', empresa_id).execute().data[0]
        # Buscar nome_cliente e id_usuario_cliente
        cliente = supabase.table("clientes").select("nome_cliente, id_usuario_cliente").eq("id", dados["cliente_id"]).execute().data[0]
        
        # Verificar se o cliente tem id_usuario_cliente antes de buscar o email
        email_cliente = None
        if cliente and cliente.get("id_usuario_cliente"):
            try:
                usuario_cliente = supabase.table("usuarios_clientes").select("email").eq("id", cliente["id_usuario_cliente"]).execute().data[0]
                email_cliente = usuario_cliente.get("email") if usuario_cliente else None
            except Exception as e:
                print(f"Erro ao buscar email do cliente: {e}")
                email_cliente = None
        
        usuario = supabase.table("usuarios").select("email, nome_usuario").eq("id", dados["usuario_id"]).execute().data[0]
        servico = supabase.table("servicos").select("nome_servico").eq("id", dados["servico_id"]).execute().data[0]

        nome_servico = servico["nome_servico"]
        descricao = dados.get("descricao", "Sem descrição")  # Obtem a descrição ou usa um valor padrão

        # Mensagem para o cliente
        assunto_cliente = f"Confirmação de Agendamento - {cliente['nome_cliente']}"
        mensagem_cliente = f"""
        Olá {cliente['nome_cliente']},

        Seu agendamento foi confirmado! Aqui estão os detalhes:

        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Profissional Responsável**: {usuario['nome_usuario']}
        - **Descrição**: {descricao}

        Em caso de dúvidas ou alterações no agendamento, entre em contato conosco.

        Atenciosamente,
        Equipe de Agendamento.
        """

        # Mensagem para o usuário
        assunto_usuario = f"Novo Agendamento - {usuario['nome_usuario']}"
        mensagem_usuario = f"""
        Olá {usuario['nome_usuario']},

        Você recebeu um novo agendamento! Confira os detalhes abaixo:

        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Cliente**: {cliente['nome_cliente']}
        - **Descrição**: {descricao}

        Lembre-se de verificar sua agenda regularmente para acompanhar todos os compromissos.

        Atenciosamente,
        Equipe de Agendamento.
        """

        # Preparar dados para email
        dados_email = {
            "servico": nome_servico,
            "data": dados['data'],
            "horario": dados['horario'],
            "cliente": cliente['nome_cliente'],
            "profissional": usuario['nome_usuario'],
            "descricao": descricao,
            "email_cliente": email_cliente,
            "email_profissional": usuario['email']
        }

        # Enviar e-mails usando o novo serviço (apenas se a empresa permitir)
        email_enviado_cliente = False
        email_enviado_profissional = False

        # Verificar se a empresa permite envio de emails
        if empresa.get('envia_email', True):  # Default True para compatibilidade
            if email_cliente:
                email_enviado_cliente = EmailService.enviar_agendamento_cliente(
                    dados_email, empresa['email'], empresa['senha_app']
                )

            email_enviado_profissional = EmailService.enviar_agendamento_profissional(
                dados_email, empresa['email'], empresa['senha_app']
            )
        else:
            print(f"[EMAIL] Envio de emails desabilitado para a empresa {empresa_id}")

        # Enviar notificação push para o profissional
        try:
            agendar_notificacao_push(
                dados["usuario_id"],
                response.data[0]["id"],
                dados['data'],
                dados['horario'],
                nome_servico
            )
        except Exception as e:
            print(f"Erro ao enviar notificação push: {e}")

        # Enviar notificação push para o cliente (se tiver id_usuario_cliente)
        if cliente and cliente.get('id_usuario_cliente'):
            try:
                agendar_notificacao_push_cliente(
                    cliente['id_usuario_cliente'],
                    response.data[0]["id"],
                    dados['data'],
                    dados['horario'],
                    nome_servico
                )
            except Exception as e:
                print(f"Erro ao enviar notificação push para cliente: {e}")

        return jsonify({"message": "Agendamento realizado com sucesso e e-mails enviados!"}), 201
    else:
        return jsonify({"error": "Erro ao criar agendamento"}), 400


# Função para obter o ID do usuário a partir do cookie
def obter_id_usuario():
    return request.cookies.get('user_id')

# Função para obter o ID da empresa logada a partir do cookie
def obter_id_empresa():
    return request.cookies.get('empresa_id')

# Rota para retornar JSON com agendamentos
@agenda_bp.route('/agenda/data', methods=['GET'])
def listar_agendamentos():
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    empresa_id = obter_id_empresa()
    usuario_id = obter_id_usuario()
    filtro = request.args.get('filtro', 'meus')

    if not empresa_id or not usuario_id:
        return jsonify({'error': 'Dados de autenticação incompletos'}), 401
    # Obtém informações da empresa logada
    response_empresa = supabase.table("empresa").select("nome_empresa").eq("id", empresa_id).execute()

    if not response_empresa.data:
        return jsonify({"erro": "Empresa não encontrada"}), 404

    # Filtro para buscar agendamentos
    if filtro == 'todos':
        response = supabase.table("agenda").select(
            "id, data, horario, descricao, cliente_id, servico_id, conta_receber, "
            "clientes!agendamentos_cliente_id_fkey(nome_cliente, telefone), "
            "servicos!agendamentos_servico_id_fkey(nome_servico, preco)"
        ).eq("id_empresa", empresa_id).neq("status", "finalizado").neq("status", "cancelado").execute()
    else:
        response = supabase.table("agenda").select(
            "id, data, horario, descricao, cliente_id, servico_id, conta_receber, "
            "clientes!agendamentos_cliente_id_fkey(nome_cliente, telefone), "
            "servicos!agendamentos_servico_id_fkey(nome_servico, preco)"
        ).eq("id_empresa", empresa_id).eq("usuario_id", usuario_id).neq("status", "finalizado").neq("status", "cancelado").execute()

    # Estruturando os dados para o retorno
    agendamentos = []
    for item in response.data:
        valor_servico = item["servicos"]["preco"]
        # Se for conta a receber, buscar o valor na tabela contas_receber
        if item.get("conta_receber", False):
            contas_receber_resp = supabase.table("contas_receber").select("valor").eq("id_agendamento", item["id"]).eq("id_empresa", empresa_id).execute()
            if contas_receber_resp.data and len(contas_receber_resp.data) > 0:
                valor_servico = contas_receber_resp.data[0]["valor"]
        agendamentos.append({
            "id": item["id"],
            "data": item["data"],
            "horario": item["horario"],
            "descricao": item.get("descricao", "Sem descrição"),
            "cliente_nome": item["clientes"]["nome_cliente"],
            'telefone': item["clientes"]["telefone"],
            "servico_nome": item["servicos"]["nome_servico"],
            "servico_preco": valor_servico,
            "nome_empresa": response_empresa.data[0]["nome_empresa"],
            "conta_receber": item.get("conta_receber", False)
        })
    return jsonify(agendamentos), 200

# Rota para retornar os clientes com busca
@agenda_bp.route('/api/clientes', methods=['GET'])
def listar_clientes():
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    empresa_id = obter_id_empresa()
    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    busca = request.args.get('busca', '').strip()

    if busca:
        # Busca apenas por nome_cliente (telefone é numérico)
        response = supabase.table("clientes").select("id, nome_cliente, telefone").eq("id_empresa", empresa_id).ilike("nome_cliente", f"%{busca}%").order("nome_cliente").limit(20).execute()
    else:
        # Retorna apenas os primeiros 20 clientes se não houver busca
        response = supabase.table("clientes").select("id, nome_cliente, telefone").eq("id_empresa", empresa_id).order("nome_cliente").limit(20).execute()
    
    return jsonify(response.data), 200

# Rota para retornar os profissionais (usuários)
@agenda_bp.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    empresa_id = obter_id_empresa()
    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    response = supabase.table("usuarios").select("id, nome_usuario").eq("id_empresa", empresa_id).execute()
    return jsonify(response.data), 200


# Rota para retornar os serviços com busca
@agenda_bp.route('/api/servicos', methods=['GET'])
def listar_servicos():
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    empresa_id = obter_id_empresa()
    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    busca = request.args.get('busca', '').strip()

    if busca:
        # Busca com ilike para nome_servico
        response = supabase.table("servicos").select("id, nome_servico, preco").eq("id_empresa", empresa_id).ilike("nome_servico", f"%{busca}%").order("nome_servico").limit(20).execute()
    else:
        # Retorna apenas os primeiros 20 serviços se não houver busca
        response = supabase.table("servicos").select("id, nome_servico, preco").eq("id_empresa", empresa_id).order("nome_servico").limit(20).execute()
    
    return jsonify(response.data), 200

# Rota para checar a disponibilidade de horário
@agenda_bp.route('/api/checagem-horario/<int:usuario_id>/<string:data>/<string:horario>', methods=['GET'])
def checar_horario(usuario_id, data, horario):
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    empresa_id = obter_id_empresa()
    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    response = supabase.table("agenda").select("*").eq("usuario_id", usuario_id).eq("data", data).eq("horario", horario).eq("id_empresa", empresa_id).execute()
    
    if response.data:
        return jsonify({"exists": True}), 200
    else:
        return jsonify({"exists": False}), 200



# Rota para renderizar a página HTML
@agenda_bp.route('/agenda', methods=['GET'])
def renderizar_agenda():
    if verificar_login():
        return verificar_login()

    empresa_id = obter_id_empresa()
    usuario_id = obter_id_usuario()

    if not empresa_id or not usuario_id:
        return redirect(url_for('login_bp.login'))

    # Verifica notificações
    resposta = supabase.table('agenda').select('id').eq('usuario_id', usuario_id).eq('visto', False).execute()
    total_nao_vistos = len(resposta.data) if resposta.data else 0

    return render_template('agenda.html', total_nao_vistos=total_nao_vistos)



@agenda_bp.route('/api/agendamento/<int:id>', methods=['DELETE'])
def cancelar_agendamento(id):
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    # Obter ID da empresa e usuário a partir dos cookies
    empresa_id = obter_id_empresa()
    if not empresa_id:
        return jsonify({'error': 'Empresa não identificada'}), 401

    try:
        # Buscar informações do agendamento antes de removê-lo
        agendamento = supabase.table("agenda").select(
            "cliente_id, usuario_id, servico_id, data, horario"
        ).eq("id", id).eq("id_empresa", empresa_id).execute()

        if not agendamento.data:
            return jsonify({"error": "Agendamento não encontrado."}), 404

        agendamento = agendamento.data[0]

        # Buscar informações adicionais com tratamento de erro
        try:
            cliente_response = supabase.table("clientes").select("nome_cliente, id_usuario_cliente").eq("id", agendamento["cliente_id"]).execute()
            cliente = cliente_response.data[0] if cliente_response.data else None
            
            # Buscar email do cliente na tabela usuarios_clientes
            email_cliente = None
            if cliente and cliente.get('id_usuario_cliente'):
                usuario_cliente_response = supabase.table("usuarios_clientes").select("email").eq("id", cliente['id_usuario_cliente']).execute()
                if usuario_cliente_response.data:
                    email_cliente = usuario_cliente_response.data[0]['email']
            
            usuario_response = supabase.table("usuarios").select("email, nome_usuario").eq("id", agendamento["usuario_id"]).execute()
            usuario = usuario_response.data[0] if usuario_response.data else None
            
            servico_response = supabase.table("servicos").select("nome_servico").eq("id", agendamento["servico_id"]).execute()
            servico = servico_response.data[0] if servico_response.data else None
            
            empresa_response = supabase.table("empresa").select("email, senha_app, envia_email").eq("id", empresa_id).execute()
            empresa = empresa_response.data[0] if empresa_response.data else None
            
        except Exception as e:
            print(f"Erro ao buscar dados relacionados: {e}")
            return jsonify({"error": "Erro ao buscar informações do agendamento."}), 500

        if not all([cliente, usuario, servico, empresa]):
            return jsonify({"error": "Dados incompletos para cancelamento."}), 400

        # Atualizar status para cancelado em vez de deletar
        update_response = supabase.table("agenda").update({
            "status": "cancelado"
        }).eq("id", id).eq("id_empresa", empresa_id).execute()

        if not update_response.data:
            return jsonify({"error": "Erro ao atualizar status do agendamento."}), 500

        # Preparar dados para email
        dados_email = {
            "servico": servico['nome_servico'],
            "data": agendamento['data'],
            "horario": agendamento['horario'],
            "cliente": cliente['nome_cliente'],
            "profissional": usuario['nome_usuario'],
            "descricao": agendamento.get('descricao', ''),
            "email_cliente": email_cliente,
            "email_profissional": usuario['email']
        }

        # Enviar e-mails usando o novo serviço (apenas se a empresa permitir)
        email_enviado_cliente = False
        email_enviado_profissional = False

        # Verificar se a empresa permite envio de emails
        if empresa.get('envia_email', True):  # Default True para compatibilidade
            if email_cliente:
                email_enviado_cliente = EmailService.enviar_cancelamento_cliente(
                    dados_email, empresa['email'], empresa['senha_app']
                )

            if usuario['email']:
                email_enviado_profissional = EmailService.enviar_cancelamento_profissional(
                    dados_email, empresa['email'], empresa['senha_app']
                )
        else:
            print(f"[EMAIL] Envio de emails desabilitado para a empresa {empresa_id}")

        # Enviar notificação push para o profissional sobre o cancelamento
        try:
            cancelar_notificacao_push(
                agendamento["usuario_id"],
                id,
                agendamento['data'],
                agendamento['horario'],
                servico['nome_servico']
            )
        except Exception as e:
            print(f"Erro ao enviar notificação push de cancelamento: {e}")

        # Enviar notificação push para o cliente sobre o cancelamento (se tiver id_usuario_cliente)
        if cliente and cliente.get('id_usuario_cliente'):
            try:
                cancelar_notificacao_push_cliente(
                    cliente['id_usuario_cliente'],
                    id,
                    agendamento['data'],
                    agendamento['horario'],
                    servico['nome_servico']
                )
            except Exception as e:
                print(f"Erro ao enviar notificação push de cancelamento para cliente: {e}")

        # Retornar sucesso mesmo se alguns emails falharem
        mensagem = "Agendamento cancelado com sucesso!"
        if email_enviado_cliente and email_enviado_profissional:
            mensagem += " E-mails enviados para cliente e profissional."
        elif email_enviado_cliente:
            mensagem += " E-mail enviado para cliente."
        elif email_enviado_profissional:
            mensagem += " E-mail enviado para profissional."
        else:
            mensagem += " (E-mails não puderam ser enviados)"

        return jsonify({"message": mensagem}), 200
    except Exception as e:
        print(f"Erro ao cancelar agendamento: {e}")
        return jsonify({"error": "Erro ao cancelar agendamento."}), 500


@agenda_bp.route('/api/agendamento/finalizar/<int:id>', methods=['POST'])
def finalizar_agendamento(id):
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    dados = request.get_json()
    print("JSON recebido:", dados)
    valor = dados.get("valor")
    meio_pagamento = dados.get("meio_pagamento")
    data_vencimento = dados.get("data_vencimento")
    empresa_id = obter_id_empresa()
    usuario = obter_id_usuario()

    if not empresa_id:
        return jsonify({"error": "Empresa não encontrada na sessão."}), 401

    try:
        # Verificar se o agendamento existe e buscar dados completos
        agendamento = supabase.table("agenda")\
            .select("id, cliente_id, usuario_id, servico_id, data, horario, descricao")\
            .eq("id", id).eq("id_empresa", empresa_id).execute()

        print("agendamento dados", agendamento)

        if not agendamento.data:
            return jsonify({"error": "Agendamento não encontrado."}), 404

        agendamento_data = agendamento.data[0]
        cliente_id = agendamento_data["cliente_id"]
        servico_id = agendamento_data["servico_id"]
        
        # Buscar dados do serviço para obter o valor
        servico_response = supabase.table("servicos").select("nome_servico, preco").eq("id", servico_id).execute()
        servico_data = servico_response.data[0] if servico_response.data else None
        
        # Usar valor do serviço se não foi informado valor personalizado
        valor_final = valor if valor and valor > 0 else (servico_data['preco'] if servico_data else 0)
        
        # Formatar data para descrição
        data_agendamento = datetime.strptime(agendamento_data['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
        nome_servico = servico_data['nome_servico'] if servico_data else 'Serviço'
        descricao_agendamento = f"Atendimento finalizado em {data_agendamento} - {nome_servico}"

        # Finalizar o agendamento
        supabase.table("finalizados").insert({
            "id_agenda": id,
            "meio_pagamento": meio_pagamento,
            "valor": valor_final,
            "data_hora_finalizacao": datetime.now().isoformat(),
            "id_empresa": empresa_id
        }).execute()

        # Atualizar status do agendamento para "finalizado"
        supabase.table("agenda").update({
            "status": "finalizado"
        }).eq("id", id).eq("id_empresa", empresa_id).execute()

        # Se for pagamento a prazo, criar conta a receber
        if meio_pagamento == 'prazo' and data_vencimento:
            # Obter serviço padrão para contas a receber
            servico_id_financeiro = obter_servico_padrao_financeiro(supabase, empresa_id, "conta_receber")
            if not servico_id_financeiro:
                return jsonify({'error': 'Não foi possível criar serviço padrão para conta a receber'}), 500
            
            # Criar agendamento para data de vencimento
            insert_agendamento_pagamento = supabase.table("agenda").insert({
                "data": data_vencimento,
                "horario": "12:00",
                "id_empresa": empresa_id,
                "usuario_id": usuario,
                "cliente_id": cliente_id,
                "descricao": descricao_agendamento,
                "servico_id": servico_id_financeiro,
                "status": "ativo",
                "conta_receber": True
            }).execute()

            id_agendamento_pagamento = insert_agendamento_pagamento.data[0]['id']

            # Criar conta a receber
            supabase.table("contas_receber").insert({
                "id_empresa": empresa_id,
                "id_cliente": cliente_id,
                "id_usuario": usuario,
                "valor": valor_final,
                "descricao": descricao_agendamento,
                "plano_contas": "Agendamento a prazo",
                "data_emissao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "data_vencimento": data_vencimento,
                "id_agendamento_pagamento": id_agendamento_pagamento,
                "status": "Pendente",
                "baixa": False
            }).execute()

            return jsonify({"message": "Agendamento finalizado e conta a receber criada com sucesso!"}), 200
        else:
            # Lançar no financeiro (pagamento à vista)
            supabase.table("financeiro_entrada").insert({
                "id_agenda": id,
                "valor_entrada": valor_final,
                "data": datetime.now().isoformat(),
                "id_usuario": usuario,
                "meio_pagamento": meio_pagamento,
                "motivo": descricao_agendamento,
                "id_empresa": empresa_id,
                "id_cliente": cliente_id,
                "id_servico": servico_id
            }).execute()

            return jsonify({"message": "Agendamento finalizado com sucesso!"}), 200

    except Exception as e:
        print(f"Erro ao finalizar agendamento: {e}")
        return jsonify({"error": "Erro ao finalizar agendamento."}), 500



@agenda_bp.route('/notificacoes', methods=['GET', 'POST'])
def verificar_notificacoes():
    # Verifica se o usuário está autenticado pelos cookies
    usuario_id = obter_id_usuario()
    print(f"[DEBUG] ID do usuário obtido dos cookies: {usuario_id}")

    if not usuario_id:
        print("[ERROR] Cookie 'user_id' não encontrado. Redirecionando para login.")
        return redirect(url_for('login.login'))

    # Consulta os agendamentos não vistos para o usuário logado
    try:
        response = supabase.table('agenda').select('id').eq('usuario_id', usuario_id).eq('visto', False).execute()
        agendamentos_nao_vistos = response.data or []
       
    except Exception as e:
       
        return jsonify({"erro": "Erro ao acessar agendamentos"}), 500

    if request.method == 'POST':
        # Atualiza todos os agendamentos para 'visto = True'
        ids_para_atualizar = [agendamento['id'] for agendamento in agendamentos_nao_vistos]
       

        if ids_para_atualizar:
            try:
                supabase.table('agenda').update({'visto': True}).in_('id', ids_para_atualizar).execute()
             
            except Exception as e:
                
                return jsonify({"erro": "Erro ao atualizar agendamentos"}), 500

        # Redireciona para a página desejada após a atualização
        return redirect(url_for('agenda_bp.renderizar_agenda'))  # Altere para a página correta

    # Retorna o número de agendamentos não vistos
    total_nao_vistos = len(agendamentos_nao_vistos)
   
    return render_template('agenda.html', total_nao_vistos=total_nao_vistos)


@agenda_bp.route('/api/usuario/logado', methods=['GET'])
def obter_dados_usuario_logado():
    """Retorna os dados do usuário logado."""
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    usuario_id = obter_id_usuario()
    if not usuario_id:
        return jsonify({"erro": "Usuário não encontrado nos cookies"}), 401

    # Consulta ao banco de dados para obter os dados do usuário
    response = supabase.table("usuarios").select("nome_usuario, email").eq("id", usuario_id).execute()

    if response.data:
        usuario = response.data[0]
        return jsonify({
            "nome_usuario": usuario.get("nome_usuario"),
            "email": usuario.get("email")
        }), 200
    else:
        return jsonify({"erro": "Dados do usuário não encontrados"}), 404

@agenda_bp.route('/api/notificacoes/agendamentos', methods=['GET'])
def obter_agendamentos_nao_vistos():
    """Retorna os agendamentos não vistos do usuário logado."""
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    usuario_id = obter_id_usuario()
    if not usuario_id:
        return jsonify({"erro": "Usuário não encontrado nos cookies"}), 401

    try:
        # Busca agendamentos não vistos
        response = supabase.table('agenda').select('id, data, horario, descricao, cliente_id, servico_id').eq('usuario_id', usuario_id).eq('visto', False).eq('status', 'ativo').order('data', desc=False).order('horario', desc=False).execute()

        agendamentos = []
        if response.data:
            for agendamento in response.data:
                # Buscar dados do cliente
                cliente_nome = 'Cliente não identificado'
                if agendamento.get('cliente_id'):
                    cliente_response = supabase.table('clientes').select('nome_cliente').eq('id', agendamento['cliente_id']).execute()
                    if cliente_response.data:
                        cliente_nome = cliente_response.data[0]['nome_cliente']
                
                # Buscar dados do serviço
                servico_nome = 'Serviço não identificado'
                servico_preco = 0
                if agendamento.get('servico_id'):
                    servico_response = supabase.table('servicos').select('nome_servico, preco').eq('id', agendamento['servico_id']).execute()
                    if servico_response.data:
                        servico_nome = servico_response.data[0]['nome_servico']
                        servico_preco = servico_response.data[0]['preco'] or 0
                
                agendamentos.append({
                    'id': agendamento['id'],
                    'data': agendamento['data'],
                    'horario': agendamento['horario'],
                    'descricao': agendamento.get('descricao', ''),
                    'cliente_nome': cliente_nome,
                    'servico_nome': servico_nome,
                    'servico_preco': servico_preco
                })

        return jsonify({
            'total': len(agendamentos),
            'agendamentos': agendamentos
        }), 200

    except Exception as e:
        print(f"Erro ao buscar agendamentos não vistos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@agenda_bp.route('/api/notificacoes/marcar-visto', methods=['POST'])
def marcar_agendamentos_como_vistos():
    """Marca todos os agendamentos não vistos como vistos."""
    if verificar_login():
        return jsonify({'error': 'Usuário não autenticado'}), 401

    usuario_id = obter_id_usuario()
    if not usuario_id:
        return jsonify({"erro": "Usuário não encontrado nos cookies"}), 401

    try:
        # Atualiza todos os agendamentos não vistos para visto = True
        response = supabase.table('agenda').update({'visto': True}).eq('usuario_id', usuario_id).eq('visto', False).execute()
        
        return jsonify({'message': 'Agendamentos marcados como vistos'}), 200

    except Exception as e:
        print(f"Erro ao marcar agendamentos como vistos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500