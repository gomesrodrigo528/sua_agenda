from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify, send_file
from io import BytesIO
from PIL import Image
import requests
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from flask import current_app as app
from datetime import datetime


from supabase import create_client, Client

import os


supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase=create_client(supabase_url,supabase_key)

vendas_bp = Blueprint('vendas_bp', __name__)

def verificar_login():
    if not request.cookies.get('user_id') or not request.cookies.get('empresa_id'):
        return redirect(url_for('login.login'))  # Redireciona para a página de login se não estiver autenticado
    return None

@vendas_bp.route('/vendas', methods= ['GET'])
def vendas():
    return render_template('pdv.html')


@vendas_bp.route('/vender', methods=['POST'])
def vender():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        data = request.get_json()
        produtos = data.get('produtos', [])
        observacao = data.get('observacao')
        plano_contas = data.get('plano_contas')
        meio_pagamento = data.get('meio_pagamento')
        id_cliente = data.get('id_cliente') or 238



        if not produtos:
            return jsonify({"error": "Nenhum produto informado."}), 400

        # Verifica todos os produtos antes de continuar
        for item in produtos:
            id_produto = item['id']
            quantidade = item['quantidade']

            produto = supabase.table("produtos").select("estoque").eq("id", id_produto).single().execute()
            if not produto.data:
                return jsonify({"error": f"Produto ID {id_produto} não encontrado"}), 404

            estoque_atual = produto.data['estoque']
            if estoque_atual < quantidade:
                return jsonify({
                    "error": f"Estoque insuficiente para o produto {id_produto}",
                    "estoque_atual": estoque_atual
                }), 400

        # Calcula valor total da venda
        valor_total = sum(p['quantidade'] * p['valor_unitario'] for p in produtos)

        # Cria a venda
        response = supabase.table("vendas").insert({
            "data": datetime.now().isoformat(),
            "id_usuario": id_usuario,
            "id_empresa": id_empresa,
            "valor": valor_total,
            "observacao": observacao,
            "plano_contas": plano_contas,
            "id_cliente": id_cliente,
            "meio_pagamento": meio_pagamento
        }).execute()

        supabase.table("venda_itens").insert([
            {
                "id_venda": response.data[0]['id'],
                "id_produto": item['id'],
                "quantidade": item['quantidade'],
                "valor_unitario": item['valor_unitario'],
                "subtotal": item['quantidade'] * item['valor_unitario']
            } for item in produtos
        ]).execute()

        supabase.table("produtos").update({
            "estoque": supabase.table("produtos").select("estoque").eq("id", item['id']).single().execute().data['estoque'] - item['quantidade']
        }).eq("id", item['id']).execute()


        if not response.data or 'id' not in response.data[0]:
            raise Exception("Erro ao obter o ID da venda")

        id_venda = response.data[0]['id']

        if meio_pagamento == 'prazo':
            # Chama a API vendaprazo
            vencimento = data.get('data_vencimento')  # precisa vir do frontend
            if not vencimento:
                return jsonify({"error": "Data de vencimento obrigatória para venda a prazo"}), 400

            response_prazo = requests.post(
                f"{request.host_url}/contas_receber/vendaprazo",
                json={
                    "id_venda": id_venda,
                    "data_vencimento": vencimento,
                    "id_cliente": id_cliente,
                    "id_usuario": id_usuario,
                    "valor": valor_total
                },
                cookies=request.cookies
            )

            if response_prazo.status_code != 200:
                return jsonify({"error": "Erro ao registrar contas a receber"}), 500

        else:
            # Registra a entrada no financeiro (somente se não for prazo)
            supabase.table("financeiro_entrada").insert({
                "data": datetime.now().isoformat(),
                "valor_entrada": valor_total,
                "motivo": "Venda de Produtos",
                "id_empresa": id_empresa,
                "id_usuario": id_usuario,
                "id_cliente": id_cliente,
                "meio_pagamento": meio_pagamento,
                "id_servico": None
            }).execute()

        # RETORNO FELIZÃO!
        return jsonify({
            "message": "Venda registrada com sucesso!",
            "id_venda": id_venda,
            "cupom_url": url_for('vendas_bp.gerar_cupom_venda_pdf', id_venda=id_venda)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@vendas_bp.route('/venda/<int:id_venda>/cupom', methods=['GET'])
def gerar_cupom_venda_pdf(id_venda):
    try:
        empresa_id = request.cookies.get('empresa_id')
        data_venda =datetime.now().isoformat()
        data_venda_formatada = datetime.strptime(data_venda, "%Y-%m-%dT%H:%M:%S.%f").strftime("%d/%m/%Y %H:%M:%S")

        # Busca dados da empresa
        empresa = supabase.table("empresa").select("*").eq("id", empresa_id).single().execute().data
        if not empresa:
            return jsonify({"error": "Empresa não encontrada"}), 404

        # Busca dados da venda
        venda = supabase.table("vendas").select("*").eq("id", id_venda).eq("id_empresa", empresa_id).single().execute().data
        if not venda:
            return jsonify({"error": "Venda não encontrada"}), 404

        # Busca cliente
        cliente = supabase.table("clientes").select("*").eq("id", venda['id_cliente']).single().execute().data

        # Busca itens da venda
        itens = supabase.table("venda_itens").select("*, produtos(nome_produto)").eq("id_venda", id_venda).execute().data

        # Formatar data bonitinho
        

        buffer = BytesIO()
        largura = 250
        altura = 600
        p = canvas.Canvas(buffer, pagesize=(largura, altura))

        y = altura - 20



        # Cabeçalho empresa
        p.setFont("Helvetica-Bold", 12)

        p.drawCentredString(largura/2, y, empresa['nome_empresa'] or empresa['razao_social'])
        y -= 18

        p.setFont("Helvetica", 7)
        p.drawCentredString(largura/2, y, empresa.get('endereco', 'Endereço não cadastrado'))
        y -= 12
        p.drawCentredString(largura/2, y, f"CNPJ: {empresa.get('cnpj', '---')}")
        y -= 20

        # Dados da venda
        p.setFont("Helvetica-Bold", 9)
        p.drawString(10, y, "CUPOM NÃO FISCAL")
        y -= 14

        p.setFont("Helvetica", 8)
        p.drawString(10, y, f"Data: {data_venda_formatada}")
        y -= 12
        p.drawString(10, y, f"Venda Nº: {venda['id']}")
        y -= 12

        if cliente:
            p.drawString(10, y, f"Cliente: {cliente.get('nome_cliente', 'Cliente não identificado')}")
            y -= 12

        # Meio de pagamento
        meio_pagamento = venda.get('meio_pagamento', 'Não informado')
        p.drawString(10, y, f"Pagamento: {meio_pagamento}")
        y -= 18

        p.drawString(10, y, "Itens:")
        y -= 14

        total = 0
        p.setFont("Helvetica", 7)
        for item in itens:
            nome = item['produtos']['nome_produto'][:25]
            qtd = item['quantidade']
            unit = item['valor_unitario']
            subtotal = item['subtotal']
            total += subtotal

            p.drawString(10, y, f"{nome}")
            y -= 10
            p.drawString(12, y, f"{qtd} x R$ {unit:.2f} = R$ {subtotal:.2f}")
            y -= 12

        y -= 10
        p.line(10, y, largura - 10, y)
        y -= 14

        p.setFont("Helvetica-Bold", 9)
        p.drawString(10, y, f"TOTAL: R$ {total:.2f}")
        y -= 20

        p.setFont("Helvetica", 8)
        p.drawCentredString(largura/2, y, "Obrigado pela preferência! Volte sempre :)")
        y -= 45
        logo_url = empresa.get('logo') 
        if logo_url:
            try:
                response_logo = requests.get(logo_url)
                logo_img = ImageReader(BytesIO(response_logo.content))
                
                largura_logo = 100
                altura_logo = 60
                x_logo = (largura - largura_logo) / 2  # aqui o segredo da centralização
                
                p.drawImage(logo_img, x_logo, y - 40, width=largura_logo, height=altura_logo, preserveAspectRatio=True)
            except Exception as e:
                print("Erro ao carregar logo:", e)
        y -= 50
        p.setFont("Helvetica", 8)
        p.drawCentredString(largura/2, y, "Acesse suaagenda.fun ")
        y -= 10
        p.drawCentredString(largura/2, y, "A melhor solução de agendamentos e vendas online")
        p.showPage()
        p.save()

        buffer.seek(0)
        print("Cupom PDF gerado com sucesso!")
        return send_file(
            buffer,
            as_attachment=False,
            download_name=f'cupom_venda_{id_venda}.pdf',
            mimetype='application/pdf'
        )

    except Exception as e:
        print(f"Erro ao gerar cupom: {e}")
        return jsonify({"error": "Erro interno ao gerar cupom"}), 500
    


@vendas_bp.route('/vendas/listar', methods=['GET'])
def listar_vendas():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        response = supabase.table("vendas").select("*").eq("id_empresa", id_empresa).execute()
        vendas = response.data

        return jsonify(vendas), 200

    except Exception as e:
        print("Erro ao listar vendas:", str(e))
        return jsonify({"error": str(e)}), 500
    
@vendas_bp.route('/vendas/listar/filtro', methods=['GET'])
def listar_vendas_com_filtro():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')
        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        # Pega as datas dos parâmetros da URL
        data_inicio = request.args.get('data_inicio', '')
        data_fim = request.args.get('data_fim', '')

        if not data_inicio or not data_fim:
            return jsonify({"error": "Parâmetros 'data_inicio' e 'data_fim' são obrigatórios"}), 400

        # Converte as datas para datetime
        try:
            # Remove o 'Z' do final e os milissegundos se existirem
            data_inicio = data_inicio.split('.')[0].replace('Z', '')
            data_fim = data_fim.split('.')[0].replace('Z', '')
            
            # Converte para datetime
            data_inicio = datetime.datetime.strptime(data_inicio, '%Y-%m-%dT%H:%M:%S')
            data_fim = datetime.datetime.strptime(data_fim, '%Y-%m-%dT%H:%M:%S')
        except ValueError as e:
            print(f"Erro ao converter data: {e}")
            return jsonify({"error": "Formato de data inválido. Use o formato ISO (YYYY-MM-DDTHH:MM:SS)"}), 400

        # Busca as vendas dentro do intervalo
        response = supabase.table("vendas") \
            .select("*") \
            .eq("id_empresa", id_empresa) \
            .gte("data", data_inicio.isoformat()) \
            .lte("data", data_fim.isoformat()) \
            .order("data", desc=True) \
            .execute()

        vendas = response.data if response.data else []

        return jsonify({"vendas": vendas}), 200

    except Exception as e:
        print(f"Erro em /vendas/listar/filtro: {e}")
        return jsonify({"error": str(e)}), 500