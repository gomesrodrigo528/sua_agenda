from flask import Blueprint, render_template, request, flash, redirect, url_for
from supabase_config import supabase
from utils.empresa_helper import EmpresaHelper
import os
import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo



tasks_bp = Blueprint('tasks', __name__)

# Variável de controle para garantir que o loop só seja executado uma vez
loop_started = False

def update_dias_restantes():
    try:
        # Busca todas as linhas da tabela "config_emp"
        response = supabase.table('config_emp').select('*').execute()

        # Verificando se a resposta contém dados
        if response.data is None:
            pass
        else:
            configs = response.data

            # Atualiza o valor de "dias_restantes" para cada linha
            for config in configs:
                dias_restantes = config.get('dias_restantes', 0)
                empresa_id = config.get('id_empresa')
                
                if dias_restantes > 0:
                    novo_valor = dias_restantes - 1  # Subtrai um dia
                    # Atualiza a coluna "dias_restantes" com o novo valor
                    EmpresaHelper.atualizar_config_empresa(empresa_id, {'dias_restantes': novo_valor})
                else:
                    # Se os dias_restantes forem 0, altera 'acesso' para False
                    EmpresaHelper.atualizar_config_empresa(empresa_id, {'acesso': False})

    except Exception as e:
        print("Erro durante a atualização:", str(e))


# Função que roda o loop de verificação periódica
def loop_update_dias_restantes():
    global loop_started  # Referência à variável global
    if loop_started:
        return  # Evita que o loop seja iniciado novamente

    loop_started = True
    
    # Aguarda 1 hora antes da primeira execução para evitar execução imediata no restart
    print("⏰ Aguardando 1 hora antes da primeira verificação de dias restantes...")
    time.sleep(3600)  # 3600 segundos = 1 hora

    while True:
        try:
            print("🔄 Executando verificação de dias restantes...")
            update_dias_restantes()  # Chama a função para atualizar os dias restantes
            print("✅ Verificação de dias restantes concluída")
        except Exception as e:
            print(f"❌ Erro ao executar a atualização: {e}")

        # Aguarda 1 dia antes de rodar novamente
        print("⏰ Aguardando 24 horas para próxima verificação...")
        time.sleep(86400)  #86400 segundos = 1 dia


# Inicia a execução do loop em uma thread separada para não bloquear o Flask
def start_update_thread():
    update_thread = threading.Thread(target=loop_update_dias_restantes, daemon=True)
    update_thread.start()

# Chama a função para iniciar a thread ao carregar o blueprint ou servidor
start_update_thread()
