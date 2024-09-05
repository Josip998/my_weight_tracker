import uuid
from datetime import timedelta, datetime
from redis import Redis

class SessionManager:
    def __init__(self, redis_client: Redis, token_expiry: timedelta):
        self.redis_client = redis_client
        self.token_expiry = token_expiry

    def store_token(self, token: str, user_id: str):
        self.redis_client.setex(token, self.token_expiry, user_id)

    def get_user_id(self, token: str):
        return self.redis_client.get(token)

    def delete_token(self, token: str):
        self.redis_client.delete(token)

from redis_config import redis_client

session_manager = SessionManager(redis_client, timedelta(hours=1))