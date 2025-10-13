# Helper para consultas de empresa com configurações
# Este arquivo deve ser importado nos outros módulos

from supabase_config import supabase

class EmpresaHelper:
    """Helper para consultas de empresa com configurações"""
    
    @staticmethod
    def obter_empresa_completa(empresa_id):
        """
        Obtém dados da empresa com suas configurações usando a view empresa_completa
        
        Args:
            empresa_id (int): ID da empresa
            
        Returns:
            dict: Dados completos da empresa ou None se não encontrada
        """
        try:
            response = supabase.table("empresa_completa").select("*").eq("id", empresa_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao obter empresa completa: {e}")
            return None
    
    @staticmethod
    def obter_dados_empresa(empresa_id):
        """
        Obtém apenas os dados essenciais da empresa (sem configurações)
        
        Args:
            empresa_id (int): ID da empresa
            
        Returns:
            dict: Dados da empresa ou None se não encontrada
        """
        try:
            response = supabase.table("empresa").select("*").eq("id", empresa_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao obter dados da empresa: {e}")
            return None
    
    @staticmethod
    def obter_config_empresa(empresa_id):
        """
        Obtém apenas as configurações da empresa
        
        Args:
            empresa_id (int): ID da empresa
            
        Returns:
            dict: Configurações da empresa ou None se não encontrada
        """
        try:
            response = supabase.table("config_emp").select("*").eq("id_empresa", empresa_id).execute()
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"Erro ao obter configurações da empresa: {e}")
            return None
    
    @staticmethod
    def atualizar_config_empresa(empresa_id, dados_config):
        """
        Atualiza as configurações da empresa
        
        Args:
            empresa_id (int): ID da empresa
            dados_config (dict): Dados de configuração para atualizar
            
        Returns:
            bool: True se atualizado com sucesso
        """
        try:
            response = supabase.table("config_emp").update(dados_config).eq("id_empresa", empresa_id).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Erro ao atualizar configurações da empresa: {e}")
            return False
    
    @staticmethod
    def criar_config_empresa(empresa_id, dados_config=None):
        """
        Cria configurações para uma empresa (se não existirem)
        
        Args:
            empresa_id (int): ID da empresa
            dados_config (dict): Dados de configuração (opcional)
            
        Returns:
            bool: True se criado com sucesso
        """
        try:
            config_data = dados_config or {}
            config_data['id_empresa'] = empresa_id
            
            response = supabase.table("config_emp").insert(config_data).execute()
            return bool(response.data)
        except Exception as e:
            print(f"Erro ao criar configurações da empresa: {e}")
            return False

# Funções de compatibilidade para migração gradual
def obter_empresa_logada():
    """
    Função de compatibilidade para obter dados da empresa logada
    Retorna dados completos incluindo configurações
    """
    from flask import request
    
    empresa_id = request.cookies.get('empresa_id')
    if not empresa_id:
        return None
    
    return EmpresaHelper.obter_empresa_completa(int(empresa_id))

def obter_cor_empresa(empresa_id):
    """
    Função de compatibilidade para obter cor da empresa
    """
    empresa = EmpresaHelper.obter_empresa_completa(empresa_id)
    return empresa.get('cor_emp', '#030413') if empresa else '#030413'

def obter_email_empresa(empresa_id):
    """
    Função de compatibilidade para obter email da empresa
    """
    empresa = EmpresaHelper.obter_empresa_completa(empresa_id)
    return empresa.get('email', 'sua.agenda.notificacoes@gmail.com') if empresa else 'sua.agenda.notificacoes@gmail.com'

def obter_senha_app(empresa_id):
    """
    Função de compatibilidade para obter senha do app
    """
    empresa = EmpresaHelper.obter_empresa_completa(empresa_id)
    return empresa.get('senha_app', 'bous nxkb ynqz uiiy') if empresa else 'bous nxkb ynqz uiiy'

def verificar_envia_email(empresa_id):
    """
    Função de compatibilidade para verificar se empresa envia emails
    """
    empresa = EmpresaHelper.obter_empresa_completa(empresa_id)
    return empresa.get('envia_email', True) if empresa else True
