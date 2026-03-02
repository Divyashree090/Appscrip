"""
Session tracking middleware
"""
import uuid
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

from app.utils.storage import storage

logger = logging.getLogger(__name__)


class SessionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get or create session ID from header
        session_id = request.headers.get("X-Session-ID", str(uuid.uuid4()))

        # Attach to request state
        request.state.session_id = session_id

        # Track session if it's an analyze request
        if "/analyze/" in request.url.path:
            username = self._get_username(request)
            if username:
                existing = storage.get_session(session_id)
                if not existing:
                    storage.create_session(session_id, username)
                storage.update_session(session_id)

        response = await call_next(request)
        response.headers["X-Session-ID"] = session_id
        return response

    def _get_username(self, request: Request) -> str:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            return storage.get_token_user(token) or "anonymous"
        return "anonymous"