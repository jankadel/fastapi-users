import secrets
from typing import Generic, Optional

import aioredis

from fastapi_users import models
from fastapi_users.authentication.strategy.base import Strategy
from fastapi_users.manager import BaseUserManager, InvalidID, UserNotExists


class RedisStrategy(Strategy, Generic[models.UP]):
    def __init__(self, redis: aioredis.Redis, lifetime_seconds: Optional[int] = None):
        self.redis = redis
        self.lifetime_seconds = lifetime_seconds

    async def read_token(
        self, token: Optional[str], user_manager: BaseUserManager[models.UP, models.ID]
    ) -> Optional[models.UP]:
        if token is None:
            return None

        user_id = await self.redis.get(token)
        if user_id is None:
            return None

        try:
            parsed_id = user_manager.parse_id(user_id)
            return await user_manager.get(parsed_id)
        except (UserNotExists, InvalidID):
            return None

    async def write_token(self, user: models.UP) -> str:
        token = secrets.token_urlsafe()
        await self.redis.set(token, str(user.id), ex=self.lifetime_seconds)
        return token

    async def destroy_token(self, token: str, user: models.UP) -> None:
        await self.redis.delete(token)
