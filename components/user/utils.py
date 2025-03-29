import string
import secrets

from components.core import config
from components.user import models
from components.user import schemas
settings = config.get_settings()

def generate_password(length: int = 12) -> str:
    """Function is generate a random password"""
    characters = string.ascii_letters + string.digits
    return "".join(secrets.choice(characters)for i in range(length))

def create_jwt_token_payload_from_user(user: models.User) -> dict:
    return schemas.UserJWTPayload