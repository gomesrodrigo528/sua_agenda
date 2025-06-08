from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask import flash, session
from flask import current_app as app
from datetime import datetime
from supabase import create_client, Client

import os
import datetime

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
            "data": datetime.datetime.now().isoformat(),
            "id_usuario": id_usuario,
            "id_empresa": id_empresa,
            "valor": valor_total,
            "observacao": observacao,
            "plano_contas": plano_contas,
            "meio_pagamento": meio_pagamento
        }).execute()

        id_venda = response.data[0]['id']

        # Registra a entrada no financeiro
        supabase.table("financeiro_entrada").insert({
            "data": datetime.datetime.now().isoformat(),
            "valor_entrada": valor_total,
            "motivo": "Venda de Produtos",
            "id_empresa": id_empresa,
            "id_usuario": id_usuario,
            "id_cliente": None,  # Cliente não identificado
            "meio_pagamento": meio_pagamento,
            "id_servico": None  # Não é um serviço
        }).execute()

        # Registra os itens e atualiza o estoque
        for item in produtos:
            id_produto = item['id']
            quantidade = item['quantidade']
            valor_unitario = item['valor_unitario']
            subtotal = quantidade * valor_unitario

            # Atualiza estoque
            produto = supabase.table("produtos").select("estoque").eq("id", id_produto).single().execute()
            estoque_atual = produto.data['estoque']

            novo_estoque = estoque_atual - quantidade
            supabase.table("produtos").update({
                "estoque": novo_estoque
            }).eq("id", id_produto).execute()

            # Insere item da venda
            supabase.table("venda_itens").insert({
                "id_venda": id_venda,
                "id_produto": id_produto,
                "quantidade": quantidade,
                "valor_unitario": valor_unitario,
                "subtotal": subtotal
            }).execute()

        return jsonify({"message": "Venda registrada com sucesso!"}), 201

    except Exception as e:
        print("Erro ao registrar venda:", str(e))
        return jsonify({"error": str(e)}), 500
    

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