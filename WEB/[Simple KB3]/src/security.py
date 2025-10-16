import jwt, requests
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("my_app")

PRIVATE_KEY_PATH = "private.pem"
PUBLIC_KEY_PATH = "public.pem"

# Validator will accept both RS256 and HS256 (this enables the vuln)
VERIFY_ALLOWED_ALGOS = ["RS256"]


def get_key_file(path: str) -> str:
    logger.debug(f"Get key from file: {path}")
    with open(path, "r") as f:
        return f.read()


def _prepare_hmac_key_from_pem(pem_str: str) -> bytes:
    """
    Возвращает PEM как байты без изменений
    """
    return pem_str.encode("utf-8")


def generate_jwt_token(payload_data: dict, expiration_minutes: int = 30) -> str:
    """
    Generate a legitimate RS256 token (signed with server private key).
    """
    private_pem = get_key_file(PRIVATE_KEY_PATH)
    payload = dict(payload_data)
    payload["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

    token = jwt.encode(payload, private_pem, algorithm="RS256")
    logger.debug("Generated RS256 token")
    return token


def verify_token(token: str):
    try:
        logger.debug(f"Token to validate: {token}")

        # Получаем заголовок токена
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "").upper()
        jku_url = unverified_header.get("jku")
        
        logger.debug(f"Token header alg: {alg}, jku: {jku_url}")

        # Выбираем ключ для проверки в зависимости от алгоритма
        if jku_url:
            try:
                resp = requests.get(jku_url)
                jwks = resp.json()
                logger.debug(f"Keys got from jku {jku_url} is {jwks}")
                key_for_validation = jwt.algorithms.RSAAlgorithm.from_jwk(jwks['keys'][0])
                print(key_for_validation)
                
                # Проверка токена
                decoded = jwt.decode(token,
                                    key=key_for_validation,
                                    algorithms=VERIFY_ALLOWED_ALGOS
                                    )
                
            except (requests.exceptions.RequestException, ValueError) as e:
                logger.error(f"JKU fetch error from {jku_url}: {e}")
                return False, "JKU host unavailable"
            except (jwt.InvalidTokenError, Exception) as e:
                logger.error(f"Token validation with JKU failed: {e}")
                return False, "Invalid token"

        else:
            
            # Считываем публичный ключ
            public_pem = get_key_file(PUBLIC_KEY_PATH)
            
            # Для RS256 — стандартная проверка с публичным ключом
            key_for_validation = public_pem
            
            # Проверка токена
            decoded = jwt.decode(token,
                                 key=key_for_validation,
                                 algorithms=VERIFY_ALLOWED_ALGOS
                                 )

        logger.debug(f"Decoded payload: {decoded}")

        uid = decoded.get("user_id")
        if uid is None:
            logger.error("Token payload missing user_id")
            return False, "Invalid token payload"

        return True, uid

    except jwt.ExpiredSignatureError as e:
        logger.error(f"Token expired: {e}")
        return False, "Token has expired"
    except jwt.InvalidKeyError as e:
        logger.error(f"Invalid Key: {e}")
        return False, "Invalid Key"
    except jwt.InvalidTokenError as e:
        logger.error(f"Invalid token: {e}")
        return False, "Invalid token"
