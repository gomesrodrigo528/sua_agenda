from flask import Flask, Blueprint, render_template, request, redirect, url_for, jsonify
from flask import flash, session
from flask import current_app as app
from datetime import datetime
from supabase import create_client, Client

import os
import datetime
produtos_bp = Blueprint('produtos_bp', __name__)

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



@produtos_bp.route('/produtos', methods=['GET'])
def render_produtos():
    return render_template('produtos.html')

@produtos_bp.route('/produtos/cadastro', methods=['POST'])
def iserir_produtos():
    try:
        if verificar_login():
            return verificar_login()
        
        data = request.get_json()
        print("JSON recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401

        response = supabase.table("produtos").insert({
        "nome_produto": data.get('nome_produto'),
        "preco": data.get('preco'),
        "estoque": data.get('estoque'),
        "id_empresa": id_empresa,
        "grupo":"sem grupo definido"
        }).execute()

        return jsonify({"message": "Produto cadastrado com sucesso!"}), 201

    except Exception as e:
        print("ERRO:", str(e))
        return jsonify({"error": str(e)}), 500
    


@produtos_bp.route('/produtos/listar', methods=['GET'])
def listar_produtos():
    try:
        empresa_id = request.cookies.get('empresa_id')
        response = (supabase.table('produtos')
                    .select('*')
                    .eq('id_empresa', empresa_id)
                    .execute())
        produtos = response.data if response.data else []
        return jsonify(produtos)
    except Exception as e:
        return jsonify([]), 500
    

@produtos_bp.route('/produtos/excluir/<int:id>', methods=['DELETE'])
def excluir(id):
    try:
        if verificar_login():
            return verificar_login()
        
        # Verifica se o produto existe
        produto = supabase.table("produtos").select("*").eq("id", id).execute()
        if not produto.data:
            return jsonify({"error": "Produto não encontrado"}), 404

        # TODO: Aqui poderia verificar se o produto está em alguma venda antes de excluir
        
        # Exclui o produto
        supabase.table("produtos").delete().eq("id", id).execute()
        return jsonify({"message": "Produto excluído com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@produtos_bp.route('/produtos/editar/<int:id>', methods=['PUT'])
def editar(id):
    try:
        if verificar_login():
            return verificar_login()
        
        data = request.get_json()
        
        # Validação dos dados
        if not data.get('nome_produto'):
            return jsonify({"error": "Nome do produto é obrigatório"}), 400
        
        if not isinstance(data.get('preco'), (int, float)) or data['preco'] < 0:
            return jsonify({"error": "Preço inválido"}), 400
        
        if not isinstance(data.get('estoque'), (int, float)) or data['estoque'] < 0:
            return jsonify({"error": "Estoque inválido"}), 400

        # Busca o produto atual
        produto = supabase.table("produtos").select("*").eq("id", id).execute()
        if not produto.data:
            return jsonify({"error": "Produto não encontrado"}), 404

        # Atualiza o produto
        supabase.table("produtos").update({
            "nome_produto": data['nome_produto'],
            "preco": float(data['preco']),
            "estoque": int(data['estoque'])
        }).eq("id", id).execute()

        return jsonify({"message": "Produto alterado com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    


@produtos_bp.route('/produtos/venda/<int:id>/<int:quantidade>', methods=['GET'])
def venda(id,quantidade):
    try:
        if verificar_login():
            return verificar_login()
        
        data = request.get_json()
        supabase.table("produtos").update(data).eq("id", id).execute()
        return jsonify({"message": "Produto alterado com sucesso!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
      
        

    
@produtos_bp.route('/produtos/consultar', methods=['POST'])
def consultar_produto():
    try:
        if verificar_login():
            return verificar_login()

        data = request.get_json()
        id_produto = data.get("id_produto")
        quantidade = int(data.get("quantidade", 1))

        if not id_produto or quantidade <= 0:
            return jsonify({"error": "Dados inválidos: informe id_produto e quantidade > 0"}), 400

        # Busca o produto
        response = supabase.table("produtos").select("*").eq("id", id_produto).single().execute()

        if not response.data:
            return jsonify({"error": "Produto não encontrado"}), 404

        produto = response.data
        estoque_disponivel = produto.get("estoque", 0)

        if estoque_disponivel < quantidade:
            return jsonify({
                "error": "Estoque insuficiente",
                "estoque_disponivel": estoque_disponivel
            }), 400

        # Retorna os dados do produto (para preencher no carrinho/PDV)
        return jsonify({
            "id": produto["id"],
            "nome": produto["nome_produto"],
            "preco": produto["preco"],
            "estoque_disponivel": estoque_disponivel
        }), 200

    except Exception as e:
        print(f"Erro ao consultar produto: {e}")
        return jsonify({"error": str(e)}), 500

@produtos_bp.route('/produtos/buscar', methods=['GET'])
def buscar_produtos():
    try:
        if verificar_login():
            return verificar_login()

        termo = request.args.get('termo', '').strip()
        id_empresa = request.cookies.get('empresa_id')

        # Se o termo for '*', retorna todos os produtos
        if termo == '*':
            response = supabase.table("produtos") \
                .select("id, nome_produto, preco, estoque") \
                .eq("id_empresa", id_empresa) \
                .execute()
        else:
            if not termo:
                return jsonify([])

            # Busca produtos que contenham o termo no nome
            response = supabase.table("produtos") \
                .select("id, nome_produto, preco, estoque") \
                .eq("id_empresa", id_empresa) \
                .ilike("nome_produto", f"%{termo}%") \
                .execute()

        produtos = response.data if response.data else []
        
        # Formata os dados para o frontend
        produtos_formatados = [{
            'id': p['id'],
            'nome': p['nome_produto'],
            'preco': p['preco'],
            'estoque': p['estoque']
        } for p in produtos]

        print(produtos_formatados)

        return jsonify(produtos_formatados)

    except Exception as e:
        print("Erro ao buscar produtos:", str(e))
        return jsonify({"error": str(e)}), 500



dataatual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
@produtos_bp.route('/produtos/compras',methods=['POST'])
def comprar_produtos():
    try:
        if verificar_login():
            return verificar_login()
        
        data = request.get_json()
        print("JSON recebido:", data)

        id_empresa = request.cookies.get('empresa_id')
        id_usuario = request.cookies.get('user_id')

        if not id_empresa or not id_usuario:
            return jsonify({"error": "Usuário não autenticado"}), 401
        
        if not data.get('produtos') or not data.get('data_vencimento'):
            return jsonify({"error": "Dados incompletos"}), 400

        valor_total = 0
        
        # Processa cada produto
        for produto in data['produtos']:
            try:
                id_produto = int(produto['id'])
                quantidade = int(produto['quantidade'])
                preco = float(produto['preco'])
                
                # Calcula o valor total
                valor_total += quantidade * preco
                
                # Atualiza o estoque do produto
                produto_atual = supabase.table("produtos").select("estoque").eq("id", id_produto).execute()
                if not produto_atual.data:
                    return jsonify({"error": f"Produto {id_produto} não encontrado"}), 404
                
                novo_estoque = produto_atual.data[0]["estoque"] + quantidade
                supabase.table("produtos").update({
                    "estoque": novo_estoque
                }).eq("id", id_produto).execute()
                
            except ValueError as e:
                return jsonify({"error": f"Dados inválidos para o produto {produto}"}), 400
            except Exception as e:
                return jsonify({"error": f"Erro ao processar produto {produto}: {str(e)}"}), 500

        # Cria a conta a pagar
        supabase.table('contas_pagar').insert({
            "id_empresa": id_empresa,
            "id_usuario": id_usuario,
            "data_vencimento": data["data_vencimento"],
            "valor": valor_total,
            "descricao": "Compra de produtos",
            "status": "pendente",
            "plano_contas": "compra de produtos para revenda",
            "data_emissao": dataatual,
            "data_vencimento": data["data_vencimento"]
        }).execute()

        return jsonify({"message": "Compra realizada com sucesso", "valor_total": valor_total}), 200

    except Exception as e:
        print("Erro ao realizar compra:", str(e))
        return jsonify({"error": str(e)}), 500