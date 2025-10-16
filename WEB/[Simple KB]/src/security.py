import jwt
from datetime import datetime, timedelta, timezone
from logs import *


setup_logging()
logger = logging.getLogger("my_app")

SECRET_KEY = "secret-key-for-jwt-CTF" 
ALGORITHM = "HS256"


def generate_jwt_token(payload_data: dict, expiration_minutes: int = 30):
        """
        Generates a JWT token with an expiration time.

        Args:
            payload_data (dict): The data to include in the token's payload.
            expiration_minutes (int): The number of minutes until the token expires.

        Returns:
            str: The encoded JWT token.
        """
                
        # Calculate expiration time
        expiration_time = datetime.now(timezone.utc) + timedelta(minutes=expiration_minutes)

        # Add 'exp' claim to the payload
        payload_data["exp"] = expiration_time

        # Encode the token
        encoded_jwt = jwt.encode(payload_data, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt


def verify_token(token):
    try:
        logger.debug(f'Token to validate is: {token}')
        unverified_header = jwt.get_unverified_header(token)
        if unverified_header.get("alg", "").lower() == "none":
            decoded_payload = jwt.decode(token, options={"verify_signature": False})
        else:
            decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        logger.info(f'Decoded Payload: {decoded_payload}')
        return True, decoded_payload["user_id"]
    except jwt.ExpiredSignatureError as e:
        message = "Token has expired"
        logger.error(f'Token has expired: {e}')
        return False, message
    except jwt.InvalidTokenError as e:
        message = "Invalid token"
        logger.error(f'Invalid token: {e}')
        return False, message