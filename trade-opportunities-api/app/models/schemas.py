from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, constr, conint


class AnalysisResponse(BaseModel):
    """Response model for trade analysis reports."""

    sector: str = Field(..., description="Analyzed sector name")
    report: str = Field(..., description="Full markdown analysis report")
    generated_at: datetime = Field(..., description="UTC timestamp when report was generated")
    session_id: Optional[str] = Field(None, description="Session identifier used for the request")
    cached: bool = Field(False, description="Whether the result was returned from cache")
    sources_searched: int = Field(0, description="Number of sources searched for market data")


# --- Authentication schemas ------------------------------------------------

UsernameType = constr(strip_whitespace=True, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
PasswordType = constr(min_length=8)


class UserRegister(BaseModel):
    username: UsernameType = Field(..., description="Alphanumeric username (3-50 chars, underscores or hyphens allowed)")
    password: PasswordType = Field(..., description="User password (minimum 8 characters)")


class UserLogin(BaseModel):
    username: UsernameType = Field(..., description="Registered username")
    password: PasswordType = Field(..., description="User password")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    username: str
