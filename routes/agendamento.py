from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from supabase import create_client
import os
from datetime import datetime
import smtplib
from zoneinfo import ZoneInfo
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)

# Criação do Blueprint
agendamento_bp = Blueprint('agendamento_bp', __name__)

# Função auxiliar para verificar se o cliente está logado
def verificar_cliente_logado():
    cliente_id = request.cookies.get('cliente_id')
    cliente_email = request.cookies.get('cliente_email')
    return cliente_id and cliente_email

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
    except smtplib.SMTPAuthenticationError:
        print("Erro de autenticação: verifique o e-mail e a senha fornecidos.")
    except smtplib.SMTPException as e:
        print(f"Erro ao enviar e-mail: {e}")

@agendamento_bp.route('/api/agendar-cliente', methods=['POST'])
def agendar_cliente():
    dados = request.get_json()

    # Buscar informações do cliente nos cookies
    cliente_id = request.cookies.get('cliente_id')
    cliente_name = request.cookies.get('cliente_name')
    cliente_email = request.cookies.get('cliente_email')
    cliente_empresa = request.cookies.get('cliente_empresa')

    # VALIDAÇÃO 0: Verificar se o cliente está logado
    if not verificar_cliente_logado():
        return jsonify({"error": "Cliente não está logado. Faça login para continuar."}), 401

    # Validação simples: verifica se todos os campos obrigatórios estão presentes
    campos_obrigatorios = ["nome", "email", "usuario_id", "servico_id", "data", "horario"]
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
    agendamentos_existentes = supabase.table("agenda").select("horario, servico_id").eq("usuario_id", dados["usuario_id"]).eq("data", dados["data"]).neq("status", "finalizado").execute()
    
    if agendamentos_existentes.data:
        # Buscar duração do serviço
        duracao_servico = supabase.table("servicos").select("tempo").eq("id", dados["servico_id"]).execute()
        duracao_minutos = int(duracao_servico.data[0]["tempo"]) if duracao_servico.data and duracao_servico.data[0]["tempo"] else 60
        
        # Verificar conflitos de horário
        for agendamento in agendamentos_existentes.data:
            horario_existente = agendamento["horario"]
            servico_existente_id = agendamento["servico_id"]
            
            # Buscar duração do serviço existente
            duracao_existente = supabase.table("servicos").select("tempo").eq("id", servico_existente_id).execute()
            duracao_existente_minutos = int(duracao_existente.data[0]["tempo"]) if duracao_existente.data and duracao_existente.data[0]["tempo"] else 60
            
            # Calcular sobreposição de horários
            hora_existente, minuto_existente = map(int, horario_existente.split(':')[:2])
            hora_nova, minuto_novo = map(int, horario.split(':')[:2])
            
            inicio_existente = hora_existente * 60 + minuto_existente
            fim_existente = inicio_existente + duracao_existente_minutos
            inicio_novo = hora_nova * 60 + minuto_novo
            fim_novo = inicio_novo + duracao_minutos
            
            # Verificar se há sobreposição
            if (inicio_novo < fim_existente and fim_novo > inicio_existente):
                return jsonify({"error": f"Horário {horario} conflita com agendamento existente às {horario_existente}."}), 400

    # VALIDAÇÃO 7: Verificar dados do cliente
    if cliente_id and cliente_email:
        # Cliente logado, usar dados dos cookies
        nome_cliente = cliente_name
        email_cliente = cliente_email
        
        # Verificar se o cliente ainda existe
        cliente_existente = supabase.table("clientes").select("id").eq("id", cliente_id).execute()
        if not cliente_existente.data:
            return jsonify({"error": "Cliente não encontrado. Faça login novamente."}), 404
    else:
        # Cliente não logado, usar dados do formulário
        nome_cliente = dados.get("nome")
        email_cliente = dados.get("email")
        
        # VALIDAÇÃO 8: Validar dados do formulário
        if not nome_cliente or len(nome_cliente.strip()) < 2:
            return jsonify({"error": "Nome deve ter pelo menos 2 caracteres."}), 400
        
        if not email_cliente or '@' not in email_cliente:
            return jsonify({"error": "Email inválido."}), 400

    # VALIDAÇÃO 9: Verificar telefone (se fornecido)
    telefone = dados.get("telefone")
    if telefone:
        # Remover caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        if len(telefone_limpo) < 10:
            return jsonify({"error": "Telefone deve ter pelo menos 10 dígitos."}), 400

    # VALIDAÇÃO 10: Verificar se a empresa está ativa
    empresa = supabase.table("empresa").select("status").eq("id", id_empresa).execute()
    if not empresa.data:
        return jsonify({"error": "Empresa não encontrada."}), 404
    
    if not empresa.data[0]["status"]:
        return jsonify({"error": "Empresa não está ativa no momento."}), 400

    # Busca ou criação do cliente baseado no email
    if cliente_id:
        # Cliente já logado, usar o ID do cookie
        pass
    else:
        # Buscar cliente pelo email ou criar novo
        cliente = supabase.table("clientes").select("id").eq("email", email_cliente).execute()
        if cliente.data:
            cliente_id = cliente.data[0]["id"]  # Cliente já existe, usa o ID
        else:
            # Cria um novo cliente se não existir
            # NOTA: Não incluímos id_empresa aqui, pois o cliente pode agendar em várias empresas
            cliente_response = supabase.table("clientes").insert({
                "nome_cliente": nome_cliente,
                "email": email_cliente,
                "telefone": dados.get("telefone")
                # Removido id_empresa para permitir agendamentos em múltiplas empresas
            }).execute()
            if cliente_response.data:
                cliente_id = cliente_response.data[0]["id"]
            else:
                return jsonify({"error": "Erro ao registrar o cliente"}), 500

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
        # Log de sucesso do agendamento
        print(f"Agendamento criado com sucesso: Cliente {nome_cliente} ({email_cliente}) - Serviço: {nome_servico} - Profissional: {nome_usuario} - Data: {dados['data']} - Horário: {dados['horario']}")
        
        empresa = supabase.table('empresa').select("email, senha_app").eq('id', id_empresa).execute().data[0]
        cliente = supabase.table("clientes").select("email, nome_cliente").eq("id", cliente_id).execute().data[0]
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

        # Enviar os e-mails
        enviar_email(cliente['email'], assunto_cliente, mensagem_cliente, empresa['email'], empresa['senha_app'])
        enviar_email(usuario['email'], assunto_usuario, mensagem_usuario, empresa['email'], empresa['senha_app'])

        return jsonify({"message": "Agendamento realizado com sucesso"}), 201
    else:
        print(f"Erro ao criar agendamento: Resposta vazia do banco de dados")
        return jsonify({"error": "Erro interno ao criar agendamento. Tente novamente."}), 500





@agendamento_bp.route('/api/empresas', methods=['GET'])
def listar_empresas():
    try:
        nome_empresa = request.args.get('nome_empresa', '').strip()
        cidade = request.args.get('cidade', '').strip().lower()

        

        query = supabase.table("empresa").select(
            "id, nome_empresa, logo, descricao, setor, horario, kids, acessibilidade, estacionamento, wifi, tel_empresa, cidade,endereco"
        ).eq("status", True)

        # Adicionar filtro de cidade apenas se ela não for vazia
      

        if nome_empresa:
            query = query.ilike("nome_empresa", f"%{nome_empresa}%")

        if cidade:
            query = query.ilike("cidade", cidade)  # Filtro de cidade

        response = query.execute()

     

        return jsonify(response.data), 200  

    except Exception as e:
        print(f"[ERRO] Falha ao buscar empresas: {e}")
        return jsonify([]), 500  


@agendamento_bp.route('/api/empresa/<int:empresa_id>', methods=['GET'])
def obter_empresa(empresa_id):
    try:
        # Busca os detalhes da empresa com o ID especificado
        response = supabase.table("empresa").select("id, nome_empresa, logo, descricao, setor, horario, kids, acessibilidade, estacionamento, wifi, tel_empresa,endereco").eq("id", empresa_id).execute()

        # Verifica se a empresa foi encontrada
        if not response.data:
            return jsonify({"error": "Empresa não encontrada"}), 404

        return jsonify(response.data[0]), 200  # Retorna os dados da empresa como JSON

    except Exception as e:
        print(f"Erro ao buscar informações da empresa: {e}")
        return jsonify({"error": "Erro ao buscar informações da empresa"}), 500

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
    
    # Cliente está logado, renderizar a página HTML para o agendamento
    return render_template('agendamento_cli.html')



@agendamento_bp.route('/api/produtos-empresa/<int:empresa_id>', methods=['GET'])
def listar_produtos_empresa(empresa_id):
    try:
        response = (
            supabase.table('produtos')
            .select('id, nome_produto, preco, estoque, un_medida, grupo, status, UUID_IMG')
            .eq('id_empresa', empresa_id)
            .eq('status', True)
            .neq('grupo', 'uso e consumo')
            .gt('estoque', 0)
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
            "horario, servico_id"
        ).eq("usuario_id", usuario_id).eq("data", data).neq("status", "finalizado").execute()

        if not response_agenda.data:
            response_agenda.data = []

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
        # Buscar dados para e-mail
        cliente = supabase.table('clientes').select('email, nome_cliente').eq('id', agendamento.data['cliente_id']).single().execute().data
        usuario = supabase.table('usuarios').select('email, nome_usuario').eq('id', agendamento.data['usuario_id']).single().execute().data
        servico = supabase.table('servicos').select('nome_servico').eq('id', agendamento.data['servico_id']).single().execute().data
        # Enviar e-mail para cliente
        assunto_cliente = f'Agendamento Cancelado - {servico["nome_servico"]}'
        mensagem_cliente = f"""
        Olá {cliente['nome_cliente']},\n\nSeu agendamento para o serviço '{servico['nome_servico']}' foi cancelado.\nJustificativa: {justificativa}\n\nSe tiver dúvidas, entre em contato com o profissional.\n"""
        # Enviar e-mail para profissional
        assunto_prof = f'Agendamento Cancelado - {servico["nome_servico"]}'
        mensagem_prof = f"""
        Olá {usuario['nome_usuario']},\n\nO cliente {cliente['nome_cliente']} cancelou o agendamento do serviço '{servico['nome_servico']}'.\nJustificativa: {justificativa}\n\nVerifique sua agenda.\n"""
        # Envio de e-mail (reutiliza função existente)
        empresa = supabase.table('empresa').select('email, senha_app').eq('id', agendamento.data['id_empresa']).single().execute().data
        enviar_email(cliente['email'], assunto_cliente, mensagem_cliente, empresa['email'], empresa['senha_app'])
        enviar_email(usuario['email'], assunto_prof, mensagem_prof, empresa['email'], empresa['senha_app'])
        return jsonify({'message': 'Agendamento cancelado e e-mails enviados.'})
    except Exception as e:
        print('Erro ao cancelar agendamento:', str(e))
        return jsonify({'error': 'Erro ao cancelar agendamento.'}), 500

@agendamento_bp.route('/api/meus-agendamentos', methods=['GET'])
def meus_agendamentos():
    cliente_id = request.cookies.get('cliente_id')
    if not cliente_id:
        return jsonify([]), 401

    # Buscar agendamentos do cliente
    response = (
        supabase.table('agenda')
        .select('*')
        .eq('cliente_id', cliente_id)
        .eq('status', 'ativo')
        .eq('conta_pagar', 'False')
        .eq('conta_receber', 'False')
        .order('data', desc=False)
        .execute()
    )
    agendamentos = response.data if response.data else []

    # Buscar nomes dos serviços e profissionais
    for ag in agendamentos:
        servico = supabase.table('servicos').select('nome_servico').eq('id', ag['servico_id']).single().execute().data
        usuario = supabase.table('usuarios').select('nome_usuario, telefone').eq('id', ag['usuario_id']).single().execute().data
        empresa = supabase.table('empresa').select('nome_empresa').eq('id', ag.get('id_empresa') or 0).single().execute().data if ag.get('id_empresa') else None
        ag['nome_servico'] = servico['nome_servico'] if servico else ''
        ag['nome_profissional'] = usuario['nome_usuario'] if usuario else ''
        ag['telefone_profissional'] = usuario['telefone'] if usuario and 'telefone' in usuario else ''
        ag['nome_empresa'] = empresa['nome_empresa'] if empresa else ''

    return jsonify(agendamentos)




