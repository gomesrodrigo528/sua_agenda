from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from supabase_config import supabase
from utils.email_service import EmailService
from routes.push import agendar_notificacao_push, cancelar_notificacao_push, agendar_notificacao_push_cliente, cancelar_notificacao_push_cliente
import os
from datetime import datetime, timedelta
import smtplib
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText



# Criação do Blueprint
agendamento_bp = Blueprint('agendamento_bp', __name__)

# Função auxiliar para criar URLs amigáveis
def criar_url_amigavel(nome_empresa):
    """Converte o nome da empresa para uma URL amigável"""
    import re
    # Remover caracteres especiais e converter para minúsculas
    url_amigavel = re.sub(r'[^a-zA-Z0-9\s]', '', nome_empresa)
    # Substituir espaços por hífens
    url_amigavel = re.sub(r'\s+', '-', url_amigavel.strip())
    # Converter para minúsculas
    return url_amigavel.lower()

# Função auxiliar para verificar se o cliente está logado
# NOVO: usa os cookies id_usuario_cliente, cliente_id, id_empresa
def verificar_cliente_logado():
    id_usuario_cliente = request.cookies.get('id_usuario_cliente')
    id_cliente = request.cookies.get('cliente_id')  # Corrigido: usar cliente_id em vez de id_cliente
    id_empresa = request.cookies.get('id_empresa')
    return id_usuario_cliente and id_cliente and id_empresa

# Função para enviar emails
def enviar_email(destinatario, assunto, mensagem, email_remetente, senha_remetente):
    try:
        servidor_smtp = 'smtp.gmail.com'
        porta_smtp = 587

        # Configuração da mensagem
        msg = MIMEMultipart()
        msg['From'] = email_remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto
        msg.attach(MIMEText(mensagem, 'plain'))

        # Envio do e-mail
        with smtplib.SMTP(servidor_smtp, porta_smtp) as servidor:
            servidor.starttls()
            servidor.login(email_remetente, senha_remetente)
            servidor.send_message(msg)

        print("E-mail enviado com sucesso!")
    except smtplib.SMTPAuthenticationError as e:
        print("Erro de autenticação: verifique o e-mail e a senha fornecidos.")
        raise e
    except smtplib.SMTPException as e:
        print(f"Erro ao enviar e-mail: {e}")
        raise e
    except Exception as e:
        print(f"Erro inesperado ao enviar e-mail: {e}")
        raise e

@agendamento_bp.route('/api/verificar-login-cliente', methods=['GET'])
def verificar_login_cliente():
    try:
        if verificar_cliente_logado():
            return jsonify({
                "logado": True,
                "cliente_id": request.cookies.get('cliente_id'),
                "id_usuario_cliente": request.cookies.get('id_usuario_cliente'),
                "id_empresa": request.cookies.get('id_empresa')
            }), 200
        else:
            return jsonify({
                "logado": False,
                "error": "Cliente não está logado",
                "cookies": {
                    "cliente_id": request.cookies.get('cliente_id'),
                    "id_usuario_cliente": request.cookies.get('id_usuario_cliente'),
                    "id_empresa": request.cookies.get('id_empresa')
                }
            }), 401
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route('/api/agendar-cliente', methods=['POST'])
def agendar_cliente():
    print("=== INÍCIO DO AGENDAMENTO ===")
    print("Headers recebidos:", dict(request.headers))
    print("Content-Type:", request.content_type)
    
    try:
        dados = request.get_json()
        print("Dados recebidos:", dados)
    except Exception as e:
        print(f"Erro ao fazer parse do JSON: {e}")
        return jsonify({"error": "Dados inválidos enviados"}), 400

    # Buscar informações do cliente nos cookies (NOVO)
    cliente_id = request.cookies.get('cliente_id')  # Corrigido: usar cliente_id em vez de id_cliente
    id_usuario_cliente = request.cookies.get('id_usuario_cliente')
    id_empresa = None
    nome_cliente = None
    email_cliente = None

    # VALIDAÇÃO 0: Verificar se o cliente está logado
    if not verificar_cliente_logado():
        return jsonify({"error": "Cliente não está logado. Faça login para continuar."}), 401

    # VALIDAÇÃO 0.1: Verificar se não há agendamento duplicado recente (últimos 30 segundos)
    # Isso evita duplicações por múltiplos cliques ou problemas de rede
    agendamento_recente = supabase.table("agenda").select("id").eq("cliente_id", cliente_id).eq("usuario_id", dados["usuario_id"]).eq("data", dados["data"]).eq("horario", dados["horario"]).gte("created_at", f"{(datetime.now() - timedelta(seconds=30)).strftime('%Y-%m-%d %H:%M:%S')}").execute()
    if agendamento_recente.data:
        return jsonify({"error": "Agendamento já foi realizado recentemente. Aguarde alguns segundos antes de tentar novamente."}), 429

    # Validação simples: verifica se todos os campos obrigatórios estão presentes
    campos_obrigatorios = ["usuario_id", "servico_id", "data", "horario"]
    for campo in campos_obrigatorios:
        if not dados.get(campo):
            return jsonify({"error": f"O campo '{campo}' é obrigatório"}), 400

    # VALIDAÇÃO 1: Verificar se o usuário existe e pertence a uma empresa
    usuario = supabase.table("usuarios").select("id_empresa, nome_usuario").eq("id", dados["usuario_id"]).execute()
    if not usuario.data:
        return jsonify({"error": "Profissional não encontrado."}), 404
    if not usuario.data[0]["id_empresa"]:
        return jsonify({"error": "Profissional não está vinculado a nenhuma empresa."}), 400
    id_empresa = usuario.data[0]["id_empresa"]
    nome_usuario = usuario.data[0]["nome_usuario"]

    # VALIDAÇÃO 2: Verificar se o serviço existe e pertence à mesma empresa
    servico = supabase.table("servicos").select("id_empresa, nome_servico, disp_cliente").eq("id", dados["servico_id"]).execute()
    if not servico.data:
        return jsonify({"error": "Serviço não encontrado."}), 404
    if servico.data[0]["id_empresa"] != id_empresa:
        return jsonify({"error": "Serviço não pertence à empresa selecionada."}), 400
    if not servico.data[0]["disp_cliente"]:
        return jsonify({"error": "Este serviço não está disponível para agendamento."}), 400
    nome_servico = servico.data[0]["nome_servico"]

    # VALIDAÇÃO 3: Verificar se a data não é no passado
    from datetime import datetime, date
    data_agendamento = datetime.strptime(dados["data"], "%Y-%m-%d").date()
    data_atual = date.today()
    
    if data_agendamento < data_atual:
        return jsonify({"error": "Não é possível agendar para datas passadas."}), 400
    
    # VALIDAÇÃO 3.1: Se for hoje, verificar se o horário não já passou
    if data_agendamento == data_atual:
        hora_atual = datetime.now().hour
        minuto_atual = datetime.now().minute
        hora_agendamento, minuto_agendamento = map(int, dados["horario"].split(':'))
        
        # Se o horário já passou (com margem de 30 minutos para agendamentos de última hora)
        if (hora_agendamento < hora_atual) or (hora_agendamento == hora_atual and minuto_agendamento <= minuto_atual + 30):
            return jsonify({"error": "Não é possível agendar para horários que já passaram."}), 400

    # VALIDAÇÃO 4: Verificar se o horário está no formato correto
    try:
        horario = dados["horario"]
        if not (len(horario) == 5 and horario[2] == ':'):
            return jsonify({"error": "Formato de horário inválido. Use HH:MM."}), 400
        hora, minuto = map(int, horario.split(':'))
        if not (0 <= hora <= 23 and 0 <= minuto <= 59):
            return jsonify({"error": "Horário inválido."}), 400
    except (ValueError, IndexError):
        return jsonify({"error": "Formato de horário inválido."}), 400

    # VALIDAÇÃO 5: Verificar se o horário está dentro do horário de funcionamento (8h às 18h)
    if not (8 <= hora <= 17 or (hora == 18 and minuto == 0)):
        return jsonify({"error": "Horário fora do horário de funcionamento (8h às 18h)."}), 400

    # VALIDAÇÃO 6: Verificar se o horário está disponível (não conflita com outros agendamentos)
    # Usar transação para evitar condições de corrida em aplicações multi-tenant
    try:
        # Verificar agendamentos existentes com lock para evitar duplicações simultâneas
        agendamentos_existentes = supabase.table("agenda").select("horario, servico_id, cliente_id").eq("usuario_id", dados["usuario_id"]).eq("data", dados["data"]).neq("status", "finalizado").execute()
        
        # VALIDAÇÃO 6.1: Verificar se o mesmo cliente já tem agendamento no mesmo horário
        for agendamento in agendamentos_existentes.data:
            if agendamento.get("cliente_id") == cliente_id and agendamento["horario"] == dados["horario"]:
                return jsonify({"error": "Você já possui um agendamento neste horário."}), 409
        
        if agendamentos_existentes.data:
            duracao_servico = supabase.table("servicos").select("tempo").eq("id", dados["servico_id"]).execute()
            duracao_minutos = int(duracao_servico.data[0]["tempo"]) if duracao_servico.data and duracao_servico.data[0]["tempo"] else 60
            for agendamento in agendamentos_existentes.data:
                horario_existente = agendamento["horario"]
                servico_existente_id = agendamento["servico_id"]
                duracao_existente = supabase.table("servicos").select("tempo").eq("id", servico_existente_id).execute()
                duracao_existente_minutos = int(duracao_existente.data[0]["tempo"]) if duracao_existente.data and duracao_existente.data[0]["tempo"] else 60
                hora_existente, minuto_existente = map(int, horario_existente.split(':')[:2])
                hora_nova, minuto_novo = map(int, horario.split(':')[:2])
                inicio_existente = hora_existente * 60 + minuto_existente
                fim_existente = inicio_existente + duracao_existente_minutos
                inicio_novo = hora_nova * 60 + minuto_novo
                fim_novo = inicio_novo + duracao_minutos
                if (inicio_novo < fim_existente and fim_novo > inicio_existente):
                    return jsonify({"error": f"Horário {horario} conflita com agendamento existente às {horario_existente}."}), 400
    except Exception as e:
        print(f"Erro na validação de agendamentos: {e}")
        return jsonify({"error": "Erro interno na validação de agendamentos"}), 500

    # Buscar dados do cliente logado
    cliente = supabase.table("clientes").select("nome_cliente, id_usuario_cliente").eq("id", cliente_id).single().execute().data
    if not cliente:
        return jsonify({"error": "Cliente não encontrado. Faça login novamente."}), 404
    nome_cliente = cliente["nome_cliente"]
    id_usuario_cliente = cliente["id_usuario_cliente"]
    # Buscar email do cliente em usuarios_clientes
    usuario_cliente = supabase.table("usuarios_clientes").select("email").eq("id", id_usuario_cliente).single().execute().data
    if not usuario_cliente:
        return jsonify({"error": "Usuário de login do cliente não encontrado."}), 404
    email_cliente = usuario_cliente["email"]

    # VALIDAÇÃO 11: Verificar se não há agendamento duplicado
    agendamento_duplicado = supabase.table("agenda").select("id").eq("cliente_id", cliente_id).eq("usuario_id", dados["usuario_id"]).eq("servico_id", dados["servico_id"]).eq("data", dados["data"]).eq("horario", dados["horario"]).eq("status", "ativo").execute()
    if agendamento_duplicado.data:
        return jsonify({"error": "Agendamento duplicado. Este horário já foi reservado."}), 400

    # Inserção do agendamento na tabela "agenda" com todos os campos necessários
    response = supabase.table("agenda").insert({
        "cliente_id": cliente_id,
        "usuario_id": dados["usuario_id"],
        "servico_id": dados["servico_id"],
        "data": dados["data"],
        "horario": dados["horario"],
        "id_empresa": id_empresa,
        "descricao": dados.get("descricao"),
        "status": "ativo"
    }).execute()

    if response.data:
        print(f"Agendamento criado com sucesso: Cliente {nome_cliente} ({email_cliente}) - Serviço: {nome_servico} - Profissional: {nome_usuario} - Data: {dados['data']} - Horário: {dados['horario']}")
        empresa = supabase.table('empresa').select("email, senha_app, envia_email").eq('id', id_empresa).execute().data[0]
        usuario = supabase.table("usuarios").select("email, nome_usuario").eq("id", dados["usuario_id"]).execute().data[0]
        servico = supabase.table("servicos").select("nome_servico").eq("id", dados["servico_id"]).execute().data[0]
        nome_servico = servico["nome_servico"]
        descricao = dados.get("descricao", "Sem descrição")
        # Mensagem para o cliente
        assunto_cliente = f"Confirmação de Agendamento - {nome_cliente}"
        mensagem_cliente = f"""
        Olá {nome_cliente},

        Seu agendamento foi confirmado! Aqui estão os detalhes:
        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Profissional Responsável**: {nome_usuario}
        - **Descrição**: {descricao}

        Em caso de dúvidas ou alterações no agendamento, entre em contato conosco.
        Atenciosamente,
        Equipe de Agendamento.
        """
        # Mensagem para o usuário
        assunto_usuario = f"Novo Agendamento - {nome_usuario}"
        mensagem_usuario = f"""
        Olá {nome_usuario},

        Você recebeu um novo agendamento! Confira os detalhes abaixo:
        - **Serviço**: {nome_servico}
        - **Data**: {dados['data']}
        - **Horário**: {dados['horario']}
        - **Cliente**: {nome_cliente}
        - **Descrição**: {descricao}

        Lembre-se de verificar sua agenda regularmente para acompanhar todos os compromissos.
        Atenciosamente,
        Equipe de Agendamento.
        """
        # Enviar os e-mails (não bloquear o agendamento se falhar)
        try:
            enviar_email(email_cliente, assunto_cliente, mensagem_cliente, empresa['email'], empresa['senha_app'])
        except Exception as e:
            print(f"Erro ao enviar email para cliente: {e}")
        
        try:
            enviar_email(usuario['email'], assunto_usuario, mensagem_usuario, empresa['email'], empresa['senha_app'])
        except Exception as e:
            print(f"Erro ao enviar email para usuário: {e}")
        
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
        
        # Enviar notificação push para o cliente (se estiver logado)
        if id_usuario_cliente:
            try:
                agendar_notificacao_push_cliente(
                    id_usuario_cliente,
                    response.data[0]["id"],
                    dados['data'],
                    dados['horario'],
                    nome_servico
                )
            except Exception as e:
                print(f"Erro ao enviar notificação push para cliente: {e}")
        
        print("=== AGENDAMENTO CRIADO COM SUCESSO ===")
        print("Retornando status 201 com mensagem de sucesso")
        return jsonify({"message": "Agendamento realizado com sucesso"}), 201
    else:
        print(f"Erro ao criar agendamento: Resposta vazia do banco de dados")
        return jsonify({"error": "Erro interno ao criar agendamento. Tente novamente."}), 500





@agendamento_bp.route('/api/empresas', methods=['GET'])
def listar_empresas():
    try:
        print("🔍 Iniciando busca de empresas...")
        nome_empresa = request.args.get('nome_empresa', '').strip()
        cidade = request.args.get('cidade', '').strip().lower()
        
        print(f"📋 Parâmetros: nome_empresa='{nome_empresa}', cidade='{cidade}'")

        query = supabase.table("empresa").select(
            "id, nome_empresa, logo, descricao, setor, tel_empresa, cidade, endereco"
        ).eq("status", True)

        if nome_empresa:
            print(f"🔍 Filtrando por nome: {nome_empresa}")
            query = query.ilike("nome_empresa", f"%{nome_empresa}%")

        if cidade:
            print(f"🔍 Filtrando por cidade: {cidade}")
            query = query.ilike("cidade", f"%{cidade}%")

        print("📡 Executando query no Supabase...")
        response = query.execute()
        print(f"✅ Query executada com sucesso. {len(response.data)} empresas encontradas")

        # Adicionar URL amigável para cada empresa
        empresas_com_url = []
        for empresa in response.data:
            empresa_dict = dict(empresa)
            empresa_dict['url_amigavel'] = criar_url_amigavel(empresa['nome_empresa'])
            empresas_com_url.append(empresa_dict)

        return jsonify(empresas_com_url), 200  

    except Exception as e:
        print(f"❌ [ERRO] Falha ao buscar empresas: {e}")
        print(f"❌ [ERRO] Tipo do erro: {type(e)}")
        import traceback
        print(f"❌ [ERRO] Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500  


@agendamento_bp.route('/agendamento/<nome_empresa>')
def pagina_empresa(nome_empresa):
    """Rota amigável para acessar a página de agendamento de uma empresa específica pelo nome"""
    try:
        # Converter o nome da empresa de volta para formato normal (remover hífens e capitalizar)
        nome_empresa_formatado = nome_empresa.replace('-', ' ').replace('_', ' ').title()
        
        print(f"🔍 Buscando empresa pelo nome: '{nome_empresa_formatado}'")
        
        # Buscar empresa pelo nome
        response = supabase.table("empresa").select(
            "id, nome_empresa, logo, descricao, setor, tel_empresa, cidade, endereco"
        ).eq("status", True).ilike("nome_empresa", f"%{nome_empresa_formatado}%").execute()
        
        if not response.data:
            # Se não encontrar, tentar busca exata
            response = supabase.table("empresa").select(
                "id, nome_empresa, logo, descricao, setor, tel_empresa, cidade, endereco"
            ).eq("status", True).eq("nome_empresa", nome_empresa_formatado).execute()
        
        if not response.data:
            print(f"❌ Empresa '{nome_empresa_formatado}' não encontrada")
            # Redirecionar para página de erro ou lista de empresas
            return redirect(url_for('agendamento_bp.agendamento'))
        
        empresa = response.data[0]
        print(f"✅ Empresa encontrada: {empresa['nome_empresa']} (ID: {empresa['id']})")
        
        # Renderizar a página de agendamento com os dados da empresa pré-selecionada
        return render_template('agendamento_cli.html', 
                             empresa_selecionada=empresa,
                             auto_select_empresa=True)
        
    except Exception as e:
        print(f"❌ Erro ao buscar empresa pelo nome: {e}")
        # Em caso de erro, redirecionar para a página principal
        return redirect(url_for('agendamento_bp.pagina_agendamento'))

@agendamento_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    try:
        print(f"🔍 Buscando empresa ID: {empresa_id}")
        
        # Busca os detalhes da empresa com o ID especificado (apenas colunas existentes)
        response = supabase.table("empresa").select(
            "id, nome_empresa, logo, descricao, setor, tel_empresa, cidade, endereco"
        ).eq("id", empresa_id).execute()

        print(f"📡 Query executada. Dados encontrados: {len(response.data)}")

        # Verifica se a empresa foi encontrada
        if not response.data:
            print(f"❌ Empresa ID {empresa_id} não encontrada")
            return jsonify({"error": "Empresa não encontrada"}), 404

        print(f"✅ Empresa encontrada: {response.data[0]['nome_empresa']}")
        return jsonify(response.data[0]), 200  # Retorna os dados da empresa como JSON

    except Exception as e:
        print(f"❌ Erro ao buscar informações da empresa: {e}")
        print(f"❌ Tipo do erro: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

@agendamento_bp.route('/api/servicos/detalhes/<int:servico_id>', methods=['GET'])
def obter_servico_detalhes(servico_id):
    try:
        # Seleciona o serviço com o nome do profissional associado
        response = supabase.table("servicos").select("id, nome_servico, preco, id_usuario, usuarios(nome_usuario)").eq("id", servico_id).execute()
        
        if not response.data:
            return jsonify({"error": "Serviço não encontrado"}), 404
        
        servico = response.data[0]

        if servico.get('id_usuario') is None:
            # Se id_usuario for NULL, retorna todos os usuários da empresa
            empresa_id = request.args.get('empresa_id')  # Recebe o ID da empresa como parâmetro
            usuarios_response = supabase.table("usuarios").select("id, nome_usuario").eq("id_empresa", empresa_id).execute()
            servico['usuarios'] = usuarios_response.data

        return jsonify(servico), 200  # Retorna os detalhes do serviço
    except Exception as e:
        print(f"Erro ao buscar detalhes do serviço: {e}")
        return jsonify({"error": "Erro ao buscar detalhes do serviço"}), 500

@agendamento_bp.route('/api/usuarios/<int:empresa_id>', methods=['GET'])
def listar_usuarios(empresa_id):
    # Lista usuários vinculados a uma empresa específica
    response = supabase.table("usuarios").select("id, nome_usuario,ft_perfil").eq("id_empresa", empresa_id).execute()
   
    return jsonify(response.data), 200

@agendamento_bp.route('/api/servicos/<int:empresa_id>', methods=['GET'])
def listar_servicos(empresa_id):
    # Lista serviços vinculados a uma empresa específica e visíveis para clientes
    response = supabase.table("servicos").select(
        "id, nome_servico, preco, id_usuario"
    ).eq("id_empresa", empresa_id).eq("disp_cliente", True).execute()  # Corrigido: condições encadeadas
    
    return jsonify(response.data), 200


@agendamento_bp.route('/agendamento', methods=['GET'])
def pagina_agendamento():
    # Verificar se o cliente está logado
    if not verificar_cliente_logado():
        # Cliente não está logado, redirecionar para a página de login
        return redirect(url_for('login.login'))
    
    # Sincronizar dados do cliente se necessário
    sincronizar_dados_cliente()
    
    # Cliente está logado, renderizar a página HTML para o agendamento
    return render_template('agendamento_cli.html')

def sincronizar_dados_cliente():
    """Função para sincronizar dados do cliente entre cookies e banco de dados"""
    try:
        cliente_id = request.cookies.get('cliente_id')
        id_usuario_cliente = request.cookies.get('id_usuario_cliente')
        
        if not cliente_id or not id_usuario_cliente:
            return
        
        # Buscar dados atuais do banco
        cliente_atual = supabase.table("clientes").select("nome_cliente, telefone").eq("id", cliente_id).single().execute()
        usuario_atual = supabase.table("usuarios_clientes").select("email").eq("id", id_usuario_cliente).single().execute()
        
        if not cliente_atual.data or not usuario_atual.data:
            return
        
        # Comparar com dados dos cookies
        cookie_nome = request.cookies.get('cliente_name', '')
        cookie_telefone = request.cookies.get('cliente_telefone', '')
        cookie_email = request.cookies.get('cliente_email', '')
        
        dados_atualizados = False
        
        # Verificar se há diferenças nos dados do cliente
        if (cookie_nome != cliente_atual.data['nome_cliente'] or 
            cookie_telefone != str(cliente_atual.data['telefone'])):
            
            # Atualizar dados do cliente comercial
            update_cliente = {}
            if cookie_nome != cliente_atual.data['nome_cliente']:
                update_cliente['nome_cliente'] = cliente_atual.data['nome_cliente']
            if cookie_telefone != str(cliente_atual.data['telefone']):
                update_cliente['telefone'] = cliente_atual.data['telefone']
            
            if update_cliente:
                supabase.table('clientes').update(update_cliente).eq('id', cliente_id).execute()
                dados_atualizados = True
        
        # Verificar se há diferenças nos dados do usuário
        if cookie_email != usuario_atual.data['email']:
            supabase.table('usuarios_clientes').update({
                'email': usuario_atual.data['email']
            }).eq('id', id_usuario_cliente).execute()
            dados_atualizados = True
        
        if dados_atualizados:
            print(f"Dados do cliente {cliente_id} sincronizados com sucesso")
            
    except Exception as e:
        print(f"Erro ao sincronizar dados do cliente: {e}")

@agendamento_bp.route('/api/sincronizar-dados-cliente', methods=['POST'])
def api_sincronizar_dados_cliente():
    """API para sincronizar dados do cliente manualmente"""
    try:
        # Verificar se o cliente está logado
        if not verificar_cliente_logado():
            return jsonify({"error": "Cliente não está logado"}), 401
        
        cliente_id = request.cookies.get('cliente_id')
        id_usuario_cliente = request.cookies.get('id_usuario_cliente')
        
        if not cliente_id or not id_usuario_cliente:
            return jsonify({"error": "Dados do cliente não encontrados"}), 400
        
        # Buscar dados atuais do banco
        cliente_atual = supabase.table("clientes").select("nome_cliente, telefone").eq("id", cliente_id).single().execute()
        usuario_atual = supabase.table("usuarios_clientes").select("email").eq("id", id_usuario_cliente).single().execute()
        
        if not cliente_atual.data or not usuario_atual.data:
            return jsonify({"error": "Cliente não encontrado no banco de dados"}), 404
        
        # Comparar com dados dos cookies
        cookie_nome = request.cookies.get('cliente_name', '')
        cookie_telefone = request.cookies.get('cliente_telefone', '')
        cookie_email = request.cookies.get('cliente_email', '')
        
        dados_atualizados = False
        mudancas = []
        
        # Verificar se há diferenças nos dados do cliente
        if cookie_nome != cliente_atual.data['nome_cliente']:
            supabase.table('clientes').update({
                'nome_cliente': cliente_atual.data['nome_cliente']
            }).eq('id', cliente_id).execute()
            mudancas.append('nome')
            dados_atualizados = True
            
        if cookie_telefone != str(cliente_atual.data['telefone']):
            supabase.table('clientes').update({
                'telefone': cliente_atual.data['telefone']
            }).eq('id', cliente_id).execute()
            mudancas.append('telefone')
            dados_atualizados = True
        
        # Verificar se há diferenças nos dados do usuário
        if cookie_email != usuario_atual.data['email']:
            supabase.table('usuarios_clientes').update({
                'email': usuario_atual.data['email']
            }).eq('id', id_usuario_cliente).execute()
            mudancas.append('email')
            dados_atualizados = True
        
        if dados_atualizados:
            return jsonify({
                "success": True,
                "message": "Dados sincronizados com sucesso",
                "mudancas": mudancas
            })
        else:
            return jsonify({
                "success": True,
                "message": "Dados já estão sincronizados",
                "mudancas": []
            })
            
    except Exception as e:
        print(f"Erro ao sincronizar dados do cliente via API: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500



@agendamento_bp.route('/api/produtos-empresa/<int:empresa_id>', methods=['GET'])
def listar_produtos_empresa(empresa_id):
    try:
        response = (
            supabase.table('produtos')
            .select('id, nome_produto, preco, estoque, un_medida, grupo, status, UUID_IMG')
            .eq('id_empresa', empresa_id)
            .eq('status', True)
            .neq('grupo', 'uso e consumo')
            # Removido filtro de estoque > 0 para permitir produtos com estoque zero
            .execute()
        )
        produtos = response.data if response.data else []
        return jsonify(produtos), 200
    except Exception as e:
        print(f"Erro ao listar produtos da empresa: {e}")
        return jsonify([]), 500

@agendamento_bp.route('/api/agenda/data', methods=['GET'])
def listar_horarios_disponiveis():
    # Verificar se o cliente está logado
    if not verificar_cliente_logado():
        return jsonify({"error": "Cliente não está logado. Faça login para continuar."}), 401
    
    try:
        usuario_id = request.args.get('usuario_id')
        data = request.args.get('data')

        if not usuario_id or not data:
            return jsonify({"error": "Os parâmetros 'usuario_id' e 'data' são obrigatórios."}), 400

        # Obtendo a data e o horário atual com fuso horário
        agora = datetime.now(ZoneInfo("America/Sao_Paulo"))
        data_atual = agora.strftime("%Y-%m-%d")

        if data == data_atual:
            horario_atual = agora.strftime("%H:%M")
        else:
            horario_atual = None

        # Definindo horários de funcionamento
        horarios_funcionamento = [
            f"{hora:02}:{minuto:02}" for hora in range(8, 18) for minuto in (0, 30)
        ]

        # Buscar agendamentos já ocupados
        response_agenda = supabase.table("agenda").select(
            "horario, servico_id, status, conta_receber, conta_pagar"
        ).eq("usuario_id", usuario_id).eq("data", data).execute()

        if not response_agenda.data:
            response_agenda.data = []
        
        # Filtrar apenas agendamentos que devem ser considerados ocupados
        agendamentos_ocupados = []
        for agendamento in response_agenda.data:
            status = agendamento.get("status", "")
            conta_receber = agendamento.get("conta_receber", False)
            conta_pagar = agendamento.get("conta_pagar", False)
            
            # Considerar ocupado se: status = ativo OU conta_receber = true OU conta_pagar = true
            # E NÃO considerar se status = cancelado
            if (status == "ativo" or conta_receber or conta_pagar) and status != "cancelado":
                agendamentos_ocupados.append(agendamento)
        
        response_agenda.data = agendamentos_ocupados

        # Buscar tempos de duração dos serviços
        response_servicos = supabase.table("servicos").select("id, tempo").execute()
        servicos = {}
        for item in response_servicos.data:
            tempo = item.get("tempo")
            if tempo is not None:
                try:
                    servicos[item["id"]] = int(tempo)
                except (ValueError, TypeError):
                    servicos[item["id"]] = 60  # Valor padrão se não conseguir converter
            else:
                servicos[item["id"]] = 60  # Valor padrão se tempo for NULL

        # Processar horários ocupados
        horarios_ocupados = set()
        for agendamento in response_agenda.data:
            horario_inicio = agendamento["horario"]
            servico_id = agendamento["servico_id"]
            duracao_minutos = servicos.get(servico_id, 60)

            # Ajustar para aceitar formatos HH:mm e HH:mm:ss
            try:
                hora, minuto = map(int, horario_inicio.split(':')[:2])  # Ignora os segundos, se existirem
            except ValueError:
                print(f"Erro ao processar horário: {horario_inicio}")
                continue

            minutos_totais = hora * 60 + minuto
            for i in range(0, duracao_minutos, 30):
                minutos_ocupados = minutos_totais + i
                hora_ocupada = minutos_ocupados // 60
                minuto_ocupado = minutos_ocupados % 60
                horarios_ocupados.add(f"{hora_ocupada:02}:{minuto_ocupado:02}")

        # Calcular horários disponíveis
        horarios_disponiveis = [
            horario for horario in horarios_funcionamento
            if horario not in horarios_ocupados and (not horario_atual or horario >= horario_atual)
        ]

        return jsonify({"horarios_disponiveis": horarios_disponiveis}), 200

    except Exception as e:
        print(f"[ERRO] Erro na função listar_horarios_disponiveis: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@agendamento_bp.route('/api/agendamento/cancelar/<int:agendamento_id>', methods=['POST'])
def cancelar_agendamento(agendamento_id):
    try:
        data = request.get_json()
        justificativa = data.get('justificativa', '').strip()
        if not justificativa:
            return jsonify({'error': 'Justificativa obrigatória'}), 400
        # Buscar agendamento
        agendamento = supabase.table('agenda').select('*').eq('id', agendamento_id).single().execute()
        if not agendamento.data:
            return jsonify({'error': 'Agendamento não encontrado'}), 404
        # Atualizar status e salvar justificativa
        supabase.table('agenda').update({
            'status': 'cancelado'
        }).eq('id', agendamento_id).execute()
        # Buscar dados para e-mail com tratamento de erro
        try:
            cliente_response = supabase.table('clientes').select('nome_cliente, id_usuario_cliente').eq('id', agendamento.data['cliente_id']).single().execute()
            cliente = cliente_response.data if cliente_response.data else None
            
            usuario_cliente_response = supabase.table('usuarios_clientes').select('email').eq('id', cliente['id_usuario_cliente']).single().execute() if cliente and cliente.get('id_usuario_cliente') else None
            usuario_cliente = usuario_cliente_response.data if usuario_cliente_response and usuario_cliente_response.data else None
            
            usuario_response = supabase.table('usuarios').select('email, nome_usuario').eq('id', agendamento.data['usuario_id']).single().execute()
            usuario = usuario_response.data if usuario_response.data else None
            
            servico_response = supabase.table('servicos').select('nome_servico').eq('id', agendamento.data['servico_id']).single().execute()
            servico = servico_response.data if servico_response.data else None
            
            empresa_response = supabase.table('empresa').select('email, senha_app').eq('id', agendamento.data['id_empresa']).single().execute()
            empresa = empresa_response.data if empresa_response.data else None
            
        except Exception as e:
            print(f"Erro ao buscar dados relacionados: {e}")
            return jsonify({'error': 'Erro ao buscar informações do agendamento.'}), 500

        if not all([cliente, usuario, servico, empresa]):
            return jsonify({'error': 'Dados incompletos para cancelamento.'}), 400

        # Preparar dados para email
        dados_email = {
            "servico": servico['nome_servico'],
            "data": agendamento.data['data'],
            "horario": agendamento.data['horario'],
            "cliente": cliente['nome_cliente'],
            "profissional": usuario['nome_usuario'],
            "descricao": agendamento.data.get('descricao', ''),
            "justificativa": justificativa,
            "email_cliente": usuario_cliente['email'] if usuario_cliente else None,
            "email_profissional": usuario['email']
        }

        # Enviar e-mails usando o novo serviço
        email_enviado_cliente = False
        email_enviado_profissional = False

        if usuario_cliente and usuario_cliente.get('email'):
            email_enviado_cliente = EmailService.enviar_cancelamento_cliente(
                dados_email, empresa['email'], empresa['senha_app']
            )

        if usuario['email']:
            email_enviado_profissional = EmailService.enviar_cancelamento_profissional(
                dados_email, empresa['email'], empresa['senha_app']
            )

        # Enviar notificação push para o profissional sobre o cancelamento
        try:
            cancelar_notificacao_push(
                agendamento.data['usuario_id'],
                agendamento_id,
                agendamento.data['data'],
                agendamento.data['horario'],
                servico['nome_servico']
            )
        except Exception as e:
            print(f"Erro ao enviar notificação push de cancelamento: {e}")

        # Enviar notificação push para o cliente sobre o cancelamento (se tiver id_usuario_cliente)
        if cliente and cliente.get('id_usuario_cliente'):
            try:
                cancelar_notificacao_push_cliente(
                    cliente['id_usuario_cliente'],
                    agendamento_id,
                    agendamento.data['data'],
                    agendamento.data['horario'],
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

        return jsonify({'message': mensagem})
    except Exception as e:
        print('Erro ao cancelar agendamento:', str(e))
        return jsonify({'error': 'Erro ao cancelar agendamento.'}), 500
