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


contas_receber_bp = Blueprint('contas_receber_bp', __name__)

supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase=create_client(supabase_url,supabase_key)

def verificar_login():
    if not request.cookies.get('user_id') or not request.cookies.get('empresa_id'):
        return redirect(url_for('login.login'))  # Redireciona para a página de login se não estiver autenticado
    return None


@contas_receber_bp.route('/contas_receber/listar', methods=['GET'])
def listar_contas_receber():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        # Busca contas a receber da empresa
        response = supabase.table("contas_receber").select("*").eq("id_empresa", id_empresa).execute()
        contas_receber = response.data

        response_formatado = []

        for conta in contas_receber:
            cliente_nome = "Não identificado"

            if conta.get("id_cliente"):
                cliente = supabase.table("clientes").select("nome_cliente").eq("id", conta["id_cliente"]).single().execute()
                if cliente.data:
                    cliente_nome = cliente.data.get("nome_cliente", "Não identificado")

            response_formatado.append({
                "id": conta.get("id"),
                "id_empresa": conta.get("id_empresa"),
                "id_venda": conta.get("id_venda"),
                "id_cliente": cliente_nome,
                "id_usuario": conta.get("id_usuario"),
                "descricao": conta.get("descricao"),
                "plano_contas": conta.get("plano_contas"),
                "status": conta.get("status"),
                "valor": conta.get("valor"),
                "data_emissao": conta.get("data_emissao"),
                "data_vencimento": conta.get("data_vencimento"),
                "baixa": conta.get("baixa", False),
                "id_agendamento": conta.get("id_agendamento"),
                "id_agendamento_pagamento": conta.get("id_agendamento_pagamento")
                
            })

        return jsonify(response_formatado), 200

    except Exception as e:
        print(f"Erro ao listar contas a receber: {e}")
        return jsonify({"error": "Erro interno ao listar contas"}), 500


       

    except Exception as e:
        print("Erro ao listar contas a receber:", str(e))
        return jsonify({"error": str(e)}), 500
    

@contas_receber_bp.route('/contas_receber/vendaprazo', methods=['POST'])
def vendaprazo():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')
        data = request.get_json()

  

        # Inserção no agendamento
        insert_agendamento_pagamento = supabase.table("agenda").insert({
            "data": data['data_vencimento'],
            "horario": "12:00",
            "id_empresa": id_empresa,
            "usuario_id": data['id_usuario'],
            "cliente_id": data['id_cliente'],
            "descricao": "Referente a venda n° " + str(data['id_venda']),
            "servico_id": "145",
            "status": "ativo",
            "conta_receber": True
        }).execute()

        id_agendamento_pagamento = insert_agendamento_pagamento.data[0]['id']

        # Inserção em contas a receber
        supabase.table("contas_receber").insert({
            "id_empresa": id_empresa,
            "id_venda": data['id_venda'],
            "data_vencimento": data['data_vencimento'],
            "id_cliente": data['id_cliente'],
            "id_usuario": data['id_usuario'],
            "valor": data['valor'],
            "descricao": "Referente a venda n° " + str(data['id_venda']),
            "plano_contas": "Venda a prazo",
            "data_emissao": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "id_agendamento_pagamento": id_agendamento_pagamento
        }).execute()

        return jsonify({"success": True}), 200

    except Exception as e:
        print("Erro ao inserir venda a prazo:", str(e))
        return jsonify({"error": str(e)}), 500
    
@contas_receber_bp.route('/contas_receber/baixar/<int:id>', methods=['POST'])
def baixar(id):
    try:
        if verificar_login():
            return verificar_login()
        
        id_empresa = request.cookies.get('empresa_id')
        data = supabase.table("contas_receber").select("*").eq("id", id).single().execute()
        responsedata = request.get_json()
        pagamento = responsedata.get('pagamento')


        print(pagamento)
        
        supabase.table("contas_receber").update({"baixa": True, "status": "Recebido"}).eq("id", id).execute()

        supabase.table("financeiro_entrada").insert({
            "id_empresa": id_empresa,
            "motivo": "Referente a venda a prazo n° " + str(data.data['id_venda']),
            "id_servico": "145",
            "data": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "valor_entrada": data.data['valor'],
            "meio_pagamento":pagamento ,
       
            "id_usuario": data.data['id_usuario'],
            "id_cliente": data.data['id_cliente'],
            "id_agenda":data.data['id_agendamento_pagamento']
        }).execute()

        supabase.table("agenda").update({"status": "finalizado"}).eq("id", data.data['id_agendamento_pagamento']).execute()
        return jsonify({"success": True}), 200
            
    except Exception as e:
        print("Erro ao baixar venda a prazo:", str(e))
        return jsonify({"error": str(e)}), 500




