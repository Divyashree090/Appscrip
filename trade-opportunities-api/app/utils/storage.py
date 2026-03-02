"""
In-memory storage for sessions, users, rate limits, and cached reports
"""
import hashlib
import time
from datetime import datetime
from typing import Any, Dict, Optional
import threading


class InMemoryStorage:
    """Thread-safe in-memory storage"""

    def __init__(self):
        self._lock = threading.Lock()
        self._users: Dict[str, Dict] = {}         # username -> user data
        self._sessions: Dict[str, Dict] = {}       # session_id -> session data
        self._rate_limits: Dict[str, Dict] = {}    # user_id -> rate limit data
        self._reports: Dict[str, Dict] = {}        # cache_key -> report data
        self._tokens: Dict[str, str] = {}          # token -> username

    # ── Users ────────────────────────────────────────────────────────────────

    def create_user(self, username: str, password_hash: str) -> Dict:
        with self._lock:
            if username in self._users:
                raise ValueError("Username already exists")
            user = {
                "username": username,
                "password_hash": password_hash,
                "created_at": datetime.utcnow(),
                "request_count": 0
            }
            self._users[username] = user
            return user

    def get_user(self, username: str) -> Optional[Dict]:
        return self._users.get(username)

    def increment_user_requests(self, username: str):
        with self._lock:
            if username in self._users:
                self._users[username]["request_count"] += 1

    # ── Sessions ─────────────────────────────────────────────────────────────

    def create_session(self, session_id: str, username: str) -> Dict:
        with self._lock:
            session = {
                "session_id": session_id,
                "username": username,
                "created_at": datetime.utcnow(),
                "request_count": 0,
                "last_request": None
            }
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[Dict]:
        return self._sessions.get(session_id)

    def update_session(self, session_id: str):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["request_count"] += 1
                self._sessions[session_id]["last_request"] = datetime.utcnow()

    # ── Tokens ────────────────────────────────────────────────────────────────

    def store_token(self, token: str, username: str):
        with self._lock:
            self._tokens[token] = username

    def get_token_user(self, token: str) -> Optional[str]:
        return self._tokens.get(token)

    def revoke_token(self, token: str):
        with self._lock:
            self._tokens.pop(token, None)

    # ── Rate Limiting ─────────────────────────────────────────────────────────

    def get_rate_limit(self, identifier: str, window: int, max_requests: int) -> Dict:
        """Returns rate limit info and whether request is allowed"""
        with self._lock:
            now = time.time()
            data = self._rate_limits.get(identifier)

            if not data or now > data["window_end"]:
                # New window
                self._rate_limits[identifier] = {
                    "count": 1,
                    "window_start": now,
                    "window_end": now + window,
                    "max_requests": max_requests
                }
                return {"allowed": True, "remaining": max_requests - 1, "reset_at": now + window}

            if data["count"] >= max_requests:
                return {
                    "allowed": False,
                    "remaining": 0,
                    "reset_at": data["window_end"]
                }

            data["count"] += 1
            return {
                "allowed": True,
                "remaining": max_requests - data["count"],
                "reset_at": data["window_end"]
            }

    # ── Report Cache ──────────────────────────────────────────────────────────

    def get_cached_report(self, sector: str, ttl: int) -> Optional[Dict]:
        key = f"report:{sector}"
        data = self._reports.get(key)
        if data and time.time() < data["expires_at"]:
            return data
        return None

    def cache_report(self, sector: str, report_data: Dict, ttl: int):
        key = f"report:{sector}"
        with self._lock:
            self._reports[key] = {
                **report_data,
                "cached_at": time.time(),
                "expires_at": time.time() + ttl
            }

    # ── Utility ───────────────────────────────────────────────────────────────

    def clear(self):
        with self._lock:
            self._sessions.clear()
            self._rate_limits.clear()
            self._reports.clear()

    def get_stats(self) -> Dict:
        return {
            "sessions": len(self._sessions),
            "reports": len(self._reports),
            "users": len(self._users),
            "tokens": len(self._tokens)
        }


# Singleton
storage = InMemoryStorage()