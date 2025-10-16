import jwt
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger("my_app")

# Validator will accept both RS256 and HS256 (this enables the vuln)
VERIFY_ALLOWED_ALGOS = "HS256"
SECRET_KEY = "ghostletmein" 


def generate_jwt_token(payload_data: dict, expiration_minutes: int = 30) -> str:

    payload_data["exp"] = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)
    token = jwt.encode(payload_data, SECRET_KEY, algorithm=VERIFY_ALLOWED_ALGOS)
    logger.debug("Generated RS256 token")
    return token


def verify_token(token: str):
    try:
        logger.debug(f"Token to validate: {token}")

        # Получаем заголовок токена
        unverified_header = jwt.get_unverified_header(token)
        alg = unverified_header.get("alg", "").upper()
        logger.debug(f"Token header alg: {alg}")

        # Проверка токена
        decoded = jwt.decode(token,
                                key=SECRET_KEY,
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
