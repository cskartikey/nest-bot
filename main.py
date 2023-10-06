from fastapi import FastAPI, Depends
from httpx import AsyncClient
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum, auto
import json

ROOT_URL = "https://identity.hackclub.app/api/v3/"
load_dotenv()
AUTH = os.environ.get("AUTHENTIK")
HEADERS = {"authorization": f"Bearer {AUTH}"}


class Role(Enum):
    internal = "internal"
    external = "external"
    internal_service_account = "internal_service_account"
    service_account = "internal_service_account"


class GroupObj(BaseModel):
    pk: str
    num_pk: int
    name: str
    is_superuser: Optional[bool]
    parent: Optional[str]
    parent_name: Optional[str]
    attributes: Optional[dict]


class User(BaseModel):
    pk: int
    username: str
    name: str
    is_active: Optional[bool]
    last_login: Optional[datetime]
    is_superuser: bool
    groups: Optional[List[str]]
    groups_obj: List[GroupObj]
    email: Optional[str]
    avatar: str
    attributes: Optional[dict]
    uid: str
    path: Optional[str]
    type: Optional[Role]


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.requests_client = AsyncClient()
    try:
        yield
    finally:
        await app.requests_client.aclose()


app = FastAPI(lifespan=lifespan)


def fetchUrl(route: str) -> str:
    return ROOT_URL + route



async def get_users_dependency():
    url = fetchUrl("core/users/")
    request_client = app.requests_client
    response = await request_client.get(url=url, headers=HEADERS)
    json_obj = response.json()

    results = json_obj.get("results", [])
    parsed_users = []

    for idx, user_data in enumerate(results):
        try:
            if "type" in user_data:
                user_data["type"] = Role(user_data["type"])
            user = User(**user_data)
            parsed_users.append(user)
        except Exception as e:
            print(f"Error for user at index {idx}: {e} User is: {user_data['name']}")
    return parsed_users

@app.get("/check_conflict")
async def check_conflict(users: List[User] = Depends(get_users_dependency)):
    usernames = [user.username for user in users]
    return usernames

@app.post("/resgister/user")