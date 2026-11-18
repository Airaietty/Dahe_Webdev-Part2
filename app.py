
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse
from sqlmodel import Session, select
from pydantic import BaseModel
from contextlib import asynccontextmanager
import hashlib
import secrets
import hmac

from database import engine, create_db_and_tables
from models import User, Matcha


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)
sessions = {}


class UserInput(BaseModel):
    username: str
    password: str


class MatchaInput(BaseModel):
    name: str
    price: float
    variant: str


# hashing
def hash_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()


def current_user(request: Request):
    session_id = request.cookies.get("session_id")
    username = sessions.get(session_id)

    if not username:
        raise HTTPException(
            status_code=401,
            detail="Please log in first"
        )

    return username


# pages
@app.get("/")
@app.get("/login")
def login_page():
    return FileResponse("login.html")


@app.get("/register")
def register_page():
    return FileResponse("register.html")


@app.get("/profile")
def profile_page(request: Request):
    if request.cookies.get("session_id") not in sessions:
        return RedirectResponse("/login")

    return FileResponse("profile.html")


@app.get("/styles.css")
def stylesheet():
    return FileResponse("styles.css", media_type="text/css")


# register
@app.post("/api/register")
def register(user: UserInput):
    username = user.username.strip()

    if not username or not user.password:
        raise HTTPException(
            status_code=400,
            detail="Fill in all fields"
        )

    username_hash = hash_text(username)

    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.username == username_hash)
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail="Username already exists"
            )

        salt = secrets.token_hex(16)

        new_user = User(
            username=username_hash,
            password_hash=hash_password(user.password, salt),
            salt=salt
        )

        session.add(new_user)
        session.commit()

    return {"message": "Registration successful"}


# login
@app.post("/api/login")
def login(user: UserInput, response: Response):
    username = user.username.strip()
    username_hash = hash_text(username)

    with Session(engine) as session:
        existing = session.exec(
            select(User).where(User.username == username_hash)
        ).first()

        if not existing or not hmac.compare_digest(
            hash_password(user.password, existing.salt),
            existing.password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid username or password"
            )

    session_id = secrets.token_hex(24)
    sessions[session_id] = username

    response.set_cookie(
        "session_id",
        session_id,
        httponly=True,
        samesite="lax"
    )

    return {
        "message": "Login successful",
        "username": username
    }


@app.get("/api/me")
def me(request: Request):
    return {"username": current_user(request)}


# logout
@app.post("/api/logout")
def logout(request: Request, response: Response):
    sessions.pop(request.cookies.get("session_id"), None)
    response.delete_cookie("session_id")

    return {"message": "Logged out"}


# display matcha list
@app.get("/api/matcha")
def list_matcha(request: Request):
    current_user(request)

    with Session(engine) as session:
        return session.exec(select(Matcha)).all()


# add matcha
@app.post("/api/matcha")
def add_matcha(item: MatchaInput, request: Request):
    current_user(request)

    if not item.name.strip() or not item.variant.strip() or item.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Enter valid matcha details"
        )

    with Session(engine) as session:
        matcha = Matcha(
            name=item.name.strip(),
            price=item.price,
            variant=item.variant.strip()
        )

        session.add(matcha)
        session.commit()
        session.refresh(matcha)

        return matcha
