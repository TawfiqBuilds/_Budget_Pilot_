"""
Every request that touches user data must prove who it's for. Supabase Auth issues
a JWT to the frontend when the user logs in; the frontend sends it as
`Authorization: Bearer <token>`. We verify that token here, server-side, on every
request. The frontend can claim to be anyone — this is the gate that actually checks.

Supabase now signs tokens with an asymmetric key (ES256), not the old shared
secret. Verification works by fetching Supabase's public signing key from its
JWKS endpoint -- no secret to store or leak on this end at all. PyJWT's
PyJWKClient handles fetching + caching that key automatically.
"""

import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings

bearer_scheme = HTTPBearer()

_jwks_client = PyJWKClient(f"{settings.supabase_url}/auth/v1/.well-known/jwks.json")


class CurrentUser:
    def __init__(self, user_id: str, email: str):
        self.user_id = user_id
        self.email = email


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> CurrentUser:
    token = credentials.credentials
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256", "RS256"],
            audience="authenticated",
        )
    except jwt.PyJWTError as e:
        print(f"[JWT DEBUG] {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session. Please log in again.",
        )

    user_id = payload.get("sub")
    email = payload.get("email")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Malformed token.")

    return CurrentUser(user_id=user_id, email=email)
