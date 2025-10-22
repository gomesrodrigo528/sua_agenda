"""
Configuração centralizada do Supabase
"""

from config import Config
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do Supabase usando variáveis de ambiente
supabase_url = Config.SUPABASE_URL
supabase_key = Config.SUPABASE_KEY

if not supabase_key:
    raise ValueError("SUPABASE_KEY não encontrada nas variáveis de ambiente")

# Criar cliente Supabase padrão
# O timeout será gerenciado pela função de retry
supabase: Client = create_client(supabase_url, supabase_key)

# Função de retry para operações do Supabase
def supabase_with_retry(operation, max_retries=3, delay=1):
    """
    Executa uma operação do Supabase com retry automático
    """
    import time
    import random
    
    for attempt in range(max_retries):
        try:
            return operation()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            # Backoff exponencial com jitter
            wait_time = delay * (2 ** attempt) + random.uniform(0, 1)
            print(f"⚠️ Erro na operação Supabase (tentativa {attempt + 1}/{max_retries}): {e}")
            print(f"🔄 Tentando novamente em {wait_time:.2f} segundos...")
            time.sleep(wait_time)
    
    return None
