from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask import flash, session
from flask import current_app as app
from supabase import create_client, Client
import os
import datetime



financeiro_bp = Blueprint('financeiro_bp' , __name__)

dataatual = datetime.datetime.now().strftime('%Y-%m-%d')

supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase=create_client(supabase_url,supabase_key)


@financeiro_bp.route('/financeiro')
def render_financeiro():
    return render_template('financeiro.html')


def verificar_login():
    if not request.cookies.get('user_id') or not request.cookies.get('empresa_id'):
        return redirect(url_for('login.login'))  # Redireciona para a página de login se não estiver autenticado
    return None


@financeiro_bp.route('/financeiro/entrada', methods=['POST'])
def receber():
    try:
        if verificar_login():
            return verificar_login()

        data = request.get_json()
        print("JSON recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401

        print("Dados inserção Supabase:", {
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_entrada": float(data.get('valor')),
            "motivo": data.get('motivo'),
            "id_usuario": id_usuario
        })

        response = supabase.table("financeiro_entrada").insert({
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_entrada": float(data.get('valor')),
            "motivo": data.get('motivo'),
            "id_usuario": id_usuario
        }).execute()

        return jsonify({"message": "Entrada registrada com sucesso!"}), 201

    except Exception as e:
    
        return jsonify({"error": str(e)}), 500



@financeiro_bp.route('/financeiro/saida', methods=['POST'])
def despesa():
    try:
        if verificar_login():
            return verificar_login()

        data = request.get_json()
        print("JSON recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401

        print("Dados inserção Supabase:", {
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_saida": float(data.get('valor')),
            "motivo": data.get('motivo'),
            "id_usuario": id_usuario
        })

        response = supabase.table("financeiro_saida").insert({
            "data": dataatual,
            "id_empresa": id_empresa,
            "valor_saida": float(data.get('valor')),
            "motivo": data.get('motivo'),
            "id_usuario": id_usuario
        }).execute()

        return jsonify({"message": "Despesa registrada com sucesso!"}), 201

    except Exception as e:
        print("ERRO:", str(e))
        return jsonify({"error": str(e)}), 500
    


@financeiro_bp.route('/financeiro/listar', methods=['GET'])
def listar_financeiro():
    try:
        if verificar_login():
            return verificar_login()

        id_empresa = request.cookies.get('empresa_id')

        if not id_empresa:
            return jsonify({"error": "Usuário não autenticado"}), 401

        response_entrada = supabase.table("financeiro_entrada").select("*").eq("id_empresa", id_empresa).execute()
        response_saida = supabase.table("financeiro_saida").select("*").eq("id_empresa", id_empresa).execute()

        entradas = response_entrada.data
        saidas = response_saida.data

        return jsonify({
            "entradas": entradas,
            "saidas": saidas
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500