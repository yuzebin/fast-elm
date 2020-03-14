import os

import jwt
from jwt import PyJWTError

from typing import Optional

from datetime import timedelta, datetime

from fastapi import Header, HTTPException, Depends

from motor.motor_asyncio import AsyncIOMotorClient

from starlette.datastructures import Secret
from starlette.status import (
    HTTP_403_FORBIDDEN, 
    HTTP_404_NOT_FOUND
)

from fmdb import (
    get_database, 
    db_name, 
    users_collection_name
)

from fmmodel import (
    RWModel, 
    RWUser, 
    RWUserInDB
)

ALGORITHM = "HS256"
SECRET_KEY = Secret(os.getenv(
    "SECRET_KEY", 
    "secret key for project"
))
JWT_TOKEN_PREFIX = "Token"

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7       # one week

access_token_jwt_subject = "access"


class TokenPayload(RWModel):
    username: str = ""


def _get_authorization_token(authorization: str = Header(...)):
    token_prefix, token = authorization.split(" ")
    if token_prefix != JWT_TOKEN_PREFIX:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Invalid authorization type"
        )

    return token


def _get_authorization_token_optional(authorization: str = Header(None)):
    if authorization:
        return _get_authorization_token(authorization)
    return ""


def create_access_token(
    *,
    data: dict,
    expires_delta: Optional[timedelta] = None
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "sub": access_token_jwt_subject})
    encoded_jwt = jwt.encode(to_encode, str(SECRET_KEY), algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user_authorizer(*, required: bool = True):
    if required:
        return _get_current_user
    else:
        return _get_current_user_optional


async def _get_current_user(
    db: AsyncIOMotorClient = Depends(get_database),
    token: str = Depends(_get_authorization_token)
) -> RWUser:
    try:
        payload = jwt.decode(token, str(SECRET_KEY), algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
    except PyJWTError:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )

    dbuser = await get_user(db, token_data.username)
    if not dbuser:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user = RWUser(**dbuser.dict(), token=token)
    return user


async def _get_current_user_optional(
    db: AsyncIOMotorClient = Depends(get_database),
    token: str = Depends(_get_authorization_token_optional),
) -> Optional[RWUser]:
    if token:
        return await _get_current_user(db, token)

    return None


async def get_user(conn: AsyncIOMotorClient, username: str) -> RWUserInDB:
    row = await conn[db_name][users_collection_name].find_one(
        {"username": username}
    )
    if row:
        return RWUserInDB(**row)