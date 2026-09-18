"""
OmniLab AI - WebSocket JWT Authentication Middleware
Extracts JWT access token from query string (?token=...) or headers
and populates scope["user"] with the authenticated User instance.
"""
import urllib.parse
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_str: str):
    """Validate JWT access token and return user or AnonymousUser."""
    try:
        access_token = AccessToken(token_str)
        user_id = access_token.get("user_id") or access_token.get("sub")
        if not user_id:
            return AnonymousUser()
        user = User.objects.select_related("profile").get(id=user_id, is_active=True)
        return user
    except (InvalidToken, TokenError, User.DoesNotExist) as e:
        logger.debug("WS JWT auth failed: %s", e)
        return AnonymousUser()
    except Exception as e:
        logger.error("Unexpected error in WS JWT auth: %s", e)
        return AnonymousUser()


class JWTAuthMiddleware:
    """
    Custom ASGI middleware to authenticate WebSocket connections via JWT.
    Supports:
    1. Query param: ws://.../?token=<access_token>
    2. Header: Authorization: Bearer <access_token>
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            token = None

            # 1. Check query string: ?token=...
            query_string = scope.get("query_string", b"").decode("utf-8")
            if query_string:
                query_params = urllib.parse.parse_qs(query_string)
                if "token" in query_params:
                    token = query_params["token"][0]

            # 2. Check headers if token not in query string
            if not token:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b"authorization", b"").decode("utf-8")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:].strip()

            # 3. Authenticate
            if token:
                scope["user"] = await get_user_from_token(token)
            else:
                # Keep existing user if already set by AuthMiddlewareStack, else Anonymous
                if "user" not in scope:
                    scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """Helper function to wrap ASGI applications with JWTAuthMiddleware."""
    from channels.auth import AuthMiddlewareStack

    return JWTAuthMiddleware(AuthMiddlewareStack(inner))
