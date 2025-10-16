from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import base64
import json
import logging

logger = logging.getLogger("jwks_logs")

PRIVATE_KEY_FILE = "private.pem"
PUBLIC_KEY_FILE = "public.pem"
JWKS_FILE = "jwks.json"
KID = "main-key"

def to_base64url(num):
    return base64.urlsafe_b64encode(num.to_bytes((num.bit_length() + 7) // 8, "big")) \
           .rstrip(b"=").decode("utf-8")

def generate_prib_pub_keys():
    """
    Генерирует новый RSA ключ каждый раз и полностью перезаписывает .pem и JWKS
    """
    logger.debug("[*] Generating new RSA key pair...")
    # Генерация ключей
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    # Перезапись приватного ключа
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))

    # Перезапись публичного ключа
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ))

    logger.debug(f"[+] Private key overwritten: {PRIVATE_KEY_FILE}")
    logger.debug(f"[+] Public key overwritten: {PUBLIC_KEY_FILE}")

    # Формируем JWKS
    public_numbers = public_key.public_numbers()
    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "alg": "RS256",
                "use": "sig",
                "kid": KID,
                "n": to_base64url(public_numbers.n),
                "e": to_base64url(public_numbers.e)
            }
        ]
    }

    # Перезапись JWKS
    with open(JWKS_FILE, "w") as f:
        json.dump(jwks, f, indent=2)

    logger.debug(f"[+] JWKS overwritten: {JWKS_FILE}")
    logger.debug(f"[+] JWKS content: {jwks}")