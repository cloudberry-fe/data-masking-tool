"""
安全相关工具：密码哈希、JWT、加密解密等
"""
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import hashlib

from app.core.config import settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_encryption_key() -> bytes:
    """从配置生成32字节的加密密钥"""
    key_bytes = settings.ENCRYPTION_KEY.encode()
    # 使用SHA256生成32字节密钥
    key_hash = hashlib.sha256(key_bytes).digest()
    # Base64编码为Fernet所需的格式
    return base64.urlsafe_b64encode(key_hash)


def encrypt_data(plaintext: str) -> str:
    """加密数据"""
    if not plaintext:
        return plaintext
    fernet = Fernet(get_encryption_key())
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_data(ciphertext: str) -> str:
    """解密数据"""
    if not ciphertext:
        return ciphertext
    fernet = Fernet(get_encryption_key())
    decrypted = fernet.decrypt(ciphertext.encode())
    return decrypted.decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """获取密码哈希"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """解码访问令牌"""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
