"""
Configuração centralizada do Supabase
"""

from config import Config
from supabase import create_client, Client

# Configuração do Supabase usando variáveis de ambiente
supabase_url = Config.SUPABASE_URL
supabase_key = Config.SUPABASE_KEY

if not supabase_key:
    raise ValueError("SUPABASE_KEY não encontrada nas variáveis de ambiente")

supabase: Client = create_client(supabase_url, supabase_key)
