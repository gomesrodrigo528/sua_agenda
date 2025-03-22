from flask import Blueprint, render_template, request, flash, redirect, url_for
from supabase import create_client
import os

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)
supabase = create_client(supabase_url, supabase_key)
# Blueprint para renovação
renovacao_bp = Blueprint('renovacao', __name__)

@renovacao_bp.route('/renovacaoconfirmada', methods=['GET', 'POST'])
def renovacao():
    if request.method == 'POST':
        cnpj = request.form.get('cnpj').strip()
        
        if not cnpj:
            flash("CNPJ é obrigatório!", "danger")
            return redirect(url_for('renovacao.renovacao'))

        try:
            # Buscar empresa pelo CNPJ
            response = supabase.table("empresa").select("id, nome_empresa, dias_restantes").eq("cnpj", cnpj).execute()
            empresa = response.data

            if not empresa:
                flash("Empresa não encontrada!", "danger")
                return redirect(url_for('renovacao.renovacao'))

            empresa_id = empresa[0]['id']
            dias_atual = empresa[0]['dias_restantes']

            # Atualizar os dias restantes adicionando 30 dias
            novo_total_dias = dias_atual + 30
            supabase.table("empresa").update({"dias_restantes": novo_total_dias, "acesso": True}).eq("id", empresa_id).execute()


            flash("Plano renovado com sucesso!", "success")
            return redirect(url_for('renovacao.sucesso'))
        except Exception as e:
            flash(f"Erro ao renovar plano: {e}", "danger")

    return render_template('renovacao.html')

@renovacao_bp.route('/renovacao/sucesso', methods=['GET'])
def sucesso():
    return render_template('renovacao_sucesso.html')


