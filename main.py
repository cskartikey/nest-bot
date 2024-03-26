from fastapi import FastAPI, Depends
from httpx import AsyncClient, HTTPError
import httpx
import os
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum, auto
import sys
import json
import string
import random
from bot.os.osFunctions import generate_config, generate_configHome, setup_script

ROOT_URL = "https://identity.hackclub.app/api/v3/"
load_dotenv()
AUTH = os.environ.get("AUTHENTIK")
HEADERS = {"authorization": f"Bearer {AUTH}"}


class Role(Enum):
    internal = "internal"
    external = "external"
    internal_service_account = "internal_service_account"
    service_account = "service_account"


class GroupObj(BaseModel):
    pk: str
    num_pk: int
    name: str
    is_superuser: Optional[bool]
    parent: Optional[str]
    parent_name: Optional[str]
    attributes: Optional[dict]


class User(BaseModel):
    pk: Optional[int]
    username: str
    name: str
    is_active: Optional[bool]
    last_login: Optional[datetime]
    is_superuser: Optional[bool]
    groups: Optional[List[str]]
    # groups_obj: Optional[List[GroupObj]]
    email: Optional[str]
    avatar: Optional[str]
    attributes: Optional[dict]
    uid: Optional[str]
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


def get_random_string(length):
    letters = string.ascii_lowercase
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str


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
    nest_users = "c844feff-89b0-45cb-8204-8fc47afbd348"
    test_account = "2c756b31-2afa-4fbd-b011-b951529210d5"
    user_info_list = [
        {
            "username": user.username,
            "name": user.name,
            "email": user.email,
            "attributes": user.attributes,
        }
        for user in users
        if user.type == Role.internal
        and nest_users in user.groups
        and test_account not in user.groups
    ]
    return user_info_list


@app.post("/register_user")
async def register_user(user: User):
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        **HEADERS,
    }

    password = get_random_string(32)
    passwordDict = {"password": password}

    # Set default values
    user.last_login = "1970-01-01T00:00:00.000Z"
    user.is_active = True
    user.is_superuser = False
    user.path = "users"
    user.groups = ["c844feff-89b0-45cb-8204-8fc47afbd348"]  # nest-users
    user.type = Role.internal.name
    # Exclude unwanted fields
    excluded_fields = ["avatar", "uid", "is_superuser", "pk"]
    user_dict = {
        key: value for key, value in user.dict().items() if key not in excluded_fields
    }
    user_json = json.dumps(user_dict)
    passwordJson = json.dumps(passwordDict)

    url = fetchUrl("core/users/")

    try:
        response = await app.requests_client.post(
            url=url, data=user_json, headers=headers
        )
        json_pk = response.text
        pk = json.loads(json_pk)
        pk_value = pk.get("pk")  # extract pk value to set password
        passwordUrl = fetchUrl(f"core/users/{pk_value}/set_password/")
        passwordResponse = await app.requests_client.post(
            url=passwordUrl, data=passwordJson, headers=headers
        )
        passwordResponse.raise_for_status()

        response.raise_for_status()
        generate_config(user.username)
        setup_script(user.username)
        generate_configHome(user.username)
    except Exception as e:
        print(f"Unexpected error: {e}")

    return {"message": "User registered successfully", "password": password}
