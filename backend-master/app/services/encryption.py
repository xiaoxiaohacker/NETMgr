"""
加密工具模块
用于加密和解密设备密码等敏感信息
"""
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class PasswordEncryption:
    """设备密码加密类"""
    
    def __init__(self, password: str = None):
        """
        初始化加密器
        
        Args:
            password: 用于生成密钥的密码，如果未提供则从环境变量获取
        """
        if password is None:
            password = os.getenv("DEVICE_ENCRYPTION_KEY", "default-insecure-key-change-in-production")
        
        self.key = self._derive_key(password)
        self.cipher_suite = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """
        从密码派生加密密钥
        
        Args:
            password: 用于生成密钥的密码
            
        Returns:
            生成的密钥
        """
        # 在生产环境中，这个salt应该存储在安全的地方
        salt = b'netmgr_salt_16bytes'  # 固定salt，生产环境中应该使用随机salt并安全存储
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_password(self, plaintext_password: str) -> str:
        """
        加密密码
        
        Args:
            plaintext_password: 明文密码
            
        Returns:
            加密后的密码（base64编码）
        """
        encrypted_bytes = self.cipher_suite.encrypt(plaintext_password.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt_password(self, encrypted_password: str) -> str:
        """
        解密密码
        
        Args:
            encrypted_password: 加密的密码（base64编码）
            
        Returns:
            解密后的明文密码
        """
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_password.encode())
        decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()


# 创建全局加密器实例
_password_encryptor = None


def get_password_encryptor() -> PasswordEncryption:
    """
    获取密码加密器单例实例
    
    Returns:
        PasswordEncryption实例
    """
    global _password_encryptor
    if _password_encryptor is None:
        _password_encryptor = PasswordEncryption()
    return _password_encryptor


def encrypt_device_password(plaintext_password: str) -> str:
    """
    加密设备密码
    
    Args:
        plaintext_password: 明文密码
        
    Returns:
        加密后的密码
    """
    encryptor = get_password_encryptor()
    return encryptor.encrypt_password(plaintext_password)


def decrypt_device_password(encrypted_password: str) -> str:
    """
    解密设备密码
    
    Args:
        encrypted_password: 加密的密码
        
    Returns:
        解密后的明文密码
    """
    encryptor = get_password_encryptor()
    return encryptor.decrypt_password(encrypted_password)