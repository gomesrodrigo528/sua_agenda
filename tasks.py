from flask import Blueprint, render_template, request, flash, redirect, url_for
from supabase import create_client
import os
import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# Configuração do Supabase
supabase_url = 'https://gccxbkoejigwkqwyvcav.supabase.co'
supabase_key = os.getenv(
    'SUPABASE_KEY',
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdjY3hia29lamlnd2txd3l2Y2F2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzM2OTg5OTYsImV4cCI6MjA0OTI3NDk5Nn0.ADRY3SLagP-NjhAAvRRP8A4Ogvo7AbWvcW-J5gAbyr4'
)

supabase = create_client(supabase_url, supabase_key)

tasks_bp = Blueprint('tasks', __name__)

# Variável de controle para garantir que o loop só seja executado uma vez
loop_started = False

def update_dias_restantes():
    try:
        # Busca todas as linhas da tabela "empresa"
        response = supabase.table('empresa').select('*').execute()

        # Verificando se a resposta contém dados
        if response.data is None:
            pass
        else:
            empresas = response.data

            # Atualiza o valor de "dias_restantes" para cada linha
            for empresa in empresas:
                dias_restantes = empresa.get('dias_restantes', 0)
                if dias_restantes > 0:
                    novo_valor = dias_restantes - 1  # Subtrai um dia
                    # Atualiza a coluna "dias_restantes" com o novo valor
                    supabase.table('empresa').update({'dias_restantes': novo_valor}).eq('id', empresa['id']).execute()
                else:
                    # Se os dias_restantes forem 0, altera 'acesso' para False
                    supabase.table('empresa').update({'acesso': False}).eq('id', empresa['id']).execute()

    except Exception as e:
        print("Erro durante a atualização:", str(e))


# Função que roda o loop de verificação periódica
def loop_update_dias_restantes():
    global loop_started  # Referência à variável global
    if loop_started:
        return  # Evita que o loop seja iniciado novamente

    loop_started = True

    while True:
        try:
            update_dias_restantes()  # Chama a função para atualizar os dias restantes
        except Exception as e:
            print(f"Erro ao executar a atualização: {e}")

        # Aguarda 1 dia antes de rodar novamente
        time.sleep(86400)  #86400 segundos = 1 dia


# Inicia a execução do loop em uma thread separada para não bloquear o Flask
def start_update_thread():
    update_thread = threading.Thread(target=loop_update_dias_restantes, daemon=True)
    update_thread.start()

# Chama a função para iniciar a thread ao carregar o blueprint ou servidor
start_update_thread()
