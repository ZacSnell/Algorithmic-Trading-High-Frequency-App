import os
from cryptography.fernet import Fernet

FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    raise RuntimeError("FERNET_KEY not set in environment. See .env.example")

fernet = Fernet(FERNET_KEY.encode())


def encrypt_value(plain_text: str) -> str:
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
