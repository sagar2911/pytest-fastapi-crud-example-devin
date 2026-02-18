import time
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter()
security = HTTPBearer()

JWT_SECRET = "super-secret-key-for-demo"
JWT_ALGORITHM = "HS256"
TOKEN_EXPIRY_SECONDS = 3600


class TokenRequest(BaseModel):
    user_id: str = Field(..., description="UUID of the user to create token for")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(user_id: str, extra_claims: dict = None) -> str:
    now = int(time.time())
    payload = {
        "sub": user_id,
        "iat": now,
        "exp": now + TOKEN_EXPIRY_SECONDS,
    }
    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def decode_token_verified(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def decode_token_unverified(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_signature": False})


def get_token_headers(token: str) -> dict:
    return jwt.get_unverified_header(token)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials
    try:
        payload = decode_token_verified(token)
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.DecodeError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


@router.post("/token", response_model=TokenResponse)
def create_token(
    request: TokenRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.id == request.user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user with id: `{request.user_id}` found",
        )

    token = create_access_token(
        user_id=str(user.id),
        extra_claims={"name": user.first_name},
    )

    return TokenResponse(
        access_token=token,
        expires_in=TOKEN_EXPIRY_SECONDS,
    )


@router.get("/me")
def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(models.User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return {
        "id": str(user.id),
        "first_name": user.first_name,
        "last_name": user.last_name,
    }


@router.get("/inspect")
def inspect_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    token = credentials.credentials

    headers = get_token_headers(token)

    unverified_payload = decode_token_unverified(token)

    try:
        verified_payload = decode_token_verified(token)
        signature_valid = True
    except jwt.InvalidTokenError:
        verified_payload = None
        signature_valid = False

    return {
        "headers": headers,
        "payload": unverified_payload,
        "signature_valid": signature_valid,
    }
