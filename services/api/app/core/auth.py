"""
Keycloak JWT authentication for BlazeDashboard API
"""
import os
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError
import httpx

# Configuration from environment
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "https://auth.wellspringfields.com")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "blaze")
KEYCLOAK_CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "blaze-app")

# Keycloak URLs
KEYCLOAK_REALM_URL = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}"
KEYCLOAK_JWKS_URL = f"{KEYCLOAK_REALM_URL}/protocol/openid-connect/certs"

security = HTTPBearer(auto_error=False)

# Cache for JWKS
_jwks_cache: Optional[dict] = None


async def get_jwks() -> dict:
    """Fetch and cache JWKS from Keycloak"""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    async with httpx.AsyncClient() as client:
        response = await client.get(KEYCLOAK_JWKS_URL)
        response.raise_for_status()
        _jwks_cache = response.json()
        return _jwks_cache


def get_public_key(token: str, jwks: dict) -> Optional[str]:
    """Extract the public key from JWKS for the given token"""
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        for key in jwks.get("keys", []):
            if key.get("kid") == kid:
                return key
        return None
    except JWTError:
        return None


class TokenPayload:
    """Parsed token payload"""
    def __init__(self, payload: dict):
        self.sub = payload.get("sub")
        self.email = payload.get("email")
        self.name = payload.get("name")
        self.preferred_username = payload.get("preferred_username")
        self.email_verified = payload.get("email_verified", False)
        self.realm_access = payload.get("realm_access", {})
        self.roles = self.realm_access.get("roles", [])

    def has_role(self, role: str) -> bool:
        return role in self.roles


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Optional[TokenPayload]:
    """
    Verify JWT token from Keycloak.
    Returns TokenPayload if valid, raises HTTPException if invalid.
    If AUTH_ENABLED is False, returns None (allows anonymous access).
    """
    if not AUTH_ENABLED:
        return None

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        jwks = await get_jwks()
        key = get_public_key(token, jwks)

        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token key",
                headers={"WWW-Authenticate": "Bearer"},
            )

        payload = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience="account",
            options={"verify_aud": False},  # Keycloak doesn't always set audience
        )

        return TokenPayload(payload)

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable",
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> Optional[TokenPayload]:
    """Dependency to get current authenticated user"""
    return await verify_token(credentials)


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> TokenPayload:
    """Dependency that requires authentication (fails if not authenticated)"""
    user = await verify_token(credentials)
    if user is None and AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(role: str):
    """Dependency factory that requires a specific role"""
    async def role_checker(
        credentials: HTTPAuthorizationCredentials = Security(security),
    ) -> TokenPayload:
        user = await require_auth(credentials)
        if user and not user.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required",
            )
        return user
    return role_checker
