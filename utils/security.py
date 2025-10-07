"""
Utilitários de segurança para hash de senhas
"""

from werkzeug.security import generate_password_hash, check_password_hash
import re

class PasswordManager:
    """Gerenciador de senhas com hash seguro"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash seguro da senha usando Werkzeug
        
        Args:
            password: Senha em texto claro
            
        Returns:
            Hash da senha
        """
        if not password:
            raise ValueError("Senha não pode ser vazia")
        
        if len(password) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres")
            
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verifica se a senha corresponde ao hash
        
        Args:
            password: Senha em texto claro
            password_hash: Hash da senha armazenado
            
        Returns:
            True se a senha estiver correta
        """
        if not password or not password_hash:
            return False
            
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Valida a força da senha
        
        Args:
            password: Senha para validar
            
        Returns:
            Tupla (é_válida, mensagem_erro)
        """
        if len(password) < 8:
            return False, "Senha deve ter pelo menos 8 caracteres"
        
        if not re.search(r'[A-Z]', password):
            return False, "Senha deve conter pelo menos uma letra maiúscula"
        
        if not re.search(r'[a-z]', password):
            return False, "Senha deve conter pelo menos uma letra minúscula"
        
        if not re.search(r'\d', password):
            return False, "Senha deve conter pelo menos um número"
        
        return True, "Senha válida"

class EmailValidator:
    """Validador de email"""
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Valida formato do email
        
        Args:
            email: Email para validar
            
        Returns:
            True se o email for válido
        """
        if not email:
            return False
            
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
