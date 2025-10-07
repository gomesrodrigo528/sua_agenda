"""
Funções para cadastro seguro de usuários
"""

from supabase_config import supabase
from utils.security import PasswordManager, EmailValidator
from flask import jsonify

class UserRegistration:
    """Classe para cadastro seguro de usuários"""
    
    @staticmethod
    def cadastrar_usuario(dados_usuario):
        """
        Cadastra um novo usuário com validações de segurança
        
        Args:
            dados_usuario: Dict com dados do usuário
            
        Returns:
            Dict com resultado do cadastro
        """
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['nome_usuario', 'email', 'senha', 'telefone', 'id_empresa']
            for campo in campos_obrigatorios:
                if not dados_usuario.get(campo):
                    return {
                        'success': False,
                        'message': f'Campo obrigatório: {campo}'
                    }
            
            # Validar formato do email
            if not EmailValidator.is_valid_email(dados_usuario['email']):
                return {
                    'success': False,
                    'message': 'Formato de email inválido'
                }
            
            # Validar força da senha
            senha_valida, mensagem_erro = PasswordManager.validate_password_strength(dados_usuario['senha'])
            if not senha_valida:
                return {
                    'success': False,
                    'message': mensagem_erro
                }
            
            # Verificar se email já existe
            usuario_existente = supabase.table('usuarios').select('id').eq('email', dados_usuario['email']).execute()
            if usuario_existente.data:
                return {
                    'success': False,
                    'message': 'Email já cadastrado no sistema'
                }
            
            # Gerar hash da senha
            senha_hash = PasswordManager.hash_password(dados_usuario['senha'])
            
            # Preparar dados para inserção
            dados_insercao = {
                'nome_usuario': dados_usuario['nome_usuario'],
                'email': dados_usuario['email'],
                'senha': senha_hash,  # Senha em hash
                'telefone': dados_usuario['telefone'],
                'id_empresa': dados_usuario['id_empresa']
            }
            
            # Inserir no banco
            resultado = supabase.table('usuarios').insert(dados_insercao).execute()
            
            if resultado.data:
                return {
                    'success': True,
                    'message': 'Usuário cadastrado com sucesso',
                    'user_id': resultado.data[0]['id']
                }
            else:
                return {
                    'success': False,
                    'message': 'Erro ao cadastrar usuário'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }
    
    @staticmethod
    def cadastrar_usuario_cliente(dados_cliente):
        """
        Cadastra um novo usuário cliente com validações de segurança
        
        Args:
            dados_cliente: Dict com dados do cliente
            
        Returns:
            Dict com resultado do cadastro
        """
        try:
            # Validar dados obrigatórios
            campos_obrigatorios = ['nome', 'email', 'senha', 'telefone']
            for campo in campos_obrigatorios:
                if not dados_cliente.get(campo):
                    return {
                        'success': False,
                        'message': f'Campo obrigatório: {campo}'
                    }
            
            # Validar formato do email
            if not EmailValidator.is_valid_email(dados_cliente['email']):
                return {
                    'success': False,
                    'message': 'Formato de email inválido'
                }
            
            # Validar força da senha
            senha_valida, mensagem_erro = PasswordManager.validate_password_strength(dados_cliente['senha'])
            if not senha_valida:
                return {
                    'success': False,
                    'message': mensagem_erro
                }
            
            # Verificar se email já existe
            usuario_existente = supabase.table('usuarios_clientes').select('id').eq('email', dados_cliente['email']).execute()
            if usuario_existente.data:
                return {
                    'success': False,
                    'message': 'Email já cadastrado no sistema'
                }
            
            # Gerar hash da senha
            senha_hash = PasswordManager.hash_password(dados_cliente['senha'])
            
            # Preparar dados para inserção
            dados_insercao = {
                'nome': dados_cliente['nome'],
                'email': dados_cliente['email'],
                'senha': senha_hash,  # Senha em hash
                'telefone': dados_cliente['telefone'],
                'status': True
            }
            
            # Inserir no banco
            resultado = supabase.table('usuarios_clientes').insert(dados_insercao).execute()
            
            if resultado.data:
                return {
                    'success': True,
                    'message': 'Cliente cadastrado com sucesso',
                    'user_id': resultado.data[0]['id']
                }
            else:
                return {
                    'success': False,
                    'message': 'Erro ao cadastrar cliente'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }
    
    @staticmethod
    def alterar_senha(usuario_id, senha_atual, nova_senha, tipo_usuario='usuario'):
        """
        Altera a senha de um usuário com validações
        
        Args:
            usuario_id: ID do usuário
            senha_atual: Senha atual
            nova_senha: Nova senha
            tipo_usuario: 'usuario' ou 'cliente'
            
        Returns:
            Dict com resultado da alteração
        """
        try:
            # Determinar tabela baseada no tipo
            tabela = 'usuarios' if tipo_usuario == 'usuario' else 'usuarios_clientes'
            
            # Buscar usuário
            usuario = supabase.table(tabela).select('senha').eq('id', usuario_id).execute()
            if not usuario.data:
                return {
                    'success': False,
                    'message': 'Usuário não encontrado'
                }
            
            # Verificar senha atual
            if not PasswordManager.verify_password(senha_atual, usuario.data[0]['senha']):
                return {
                    'success': False,
                    'message': 'Senha atual incorreta'
                }
            
            # Validar nova senha
            senha_valida, mensagem_erro = PasswordManager.validate_password_strength(nova_senha)
            if not senha_valida:
                return {
                    'success': False,
                    'message': mensagem_erro
                }
            
            # Gerar hash da nova senha
            nova_senha_hash = PasswordManager.hash_password(nova_senha)
            
            # Atualizar no banco
            resultado = supabase.table(tabela).update({
                'senha': nova_senha_hash
            }).eq('id', usuario_id).execute()
            
            if resultado.data:
                return {
                    'success': True,
                    'message': 'Senha alterada com sucesso'
                }
            else:
                return {
                    'success': False,
                    'message': 'Erro ao alterar senha'
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erro interno: {str(e)}'
            }
