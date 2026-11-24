"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import hashlib
import os
import secrets
from pathlib import Path
from typing import Literal

from agent_framework import RawAgent
from agent_framework.openai import OpenAIChatClient
from fastapi import Cookie, Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse


SESSION_COOKIE = "mergington_session"
sessions = {}
_chat_agent: RawAgent | None = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


users = {
    os.getenv("MERINGTON_ADMIN_EMAIL", "admin@mergington.edu"): hash_password(
        os.getenv("MERINGTON_ADMIN_PASSWORD", "mergington123")
    )
}

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Practice soccer skills and compete in school matches",
        "schedule": "Mondays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": []
    },
    "Basketball Team": {
        "description": "Develop basketball skills and participate in team games",
        "schedule": "Tuesdays and Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 15,
        "participants": []
    },
    "Drama Club": {
        "description": "Explore acting, stagecraft, and theatrical productions",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "max_participants": 20,
        "participants": []
    },
    "Art Workshop": {
        "description": "Create artwork using drawing, painting, and mixed media",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 18,
        "participants": []
    },
    "Debate Team": {
        "description": "Build public speaking and critical thinking skills through debates",
        "schedule": "Mondays, 3:30 PM - 5:00 PM",
        "max_participants": 16,
        "participants": []
    },
    "Science Club": {
        "description": "Conduct experiments and explore scientific concepts",
        "schedule": "Wednesdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": []
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


def require_login(session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not session_id or session_id not in sessions:
        raise HTTPException(status_code=401, detail="Sign-in required")
    return sessions[session_id]


def get_chat_agent() -> RawAgent:
    global _chat_agent

    if _chat_agent is not None:
        return _chat_agent

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="The assistant is not configured. Set OPENAI_API_KEY on the server.",
        )

    _chat_agent = RawAgent(
        client=OpenAIChatClient(model="gpt-4o-mini", api_key=api_key),
        instructions="You are a helpful assistant for Mergington High School.",
    )
    return _chat_agent


@app.get("/auth/session")
def get_session(session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    email = sessions.get(session_id) if session_id else None
    return {"authenticated": email is not None, "email": email}


@app.post("/chat")
async def chat(request: ChatRequest, email: str = Depends(require_login)):
    del email
    if not request.messages or len(request.messages) > 12:
        raise HTTPException(status_code=422, detail="Send between 1 and 12 messages.")
    if any(not message.content.strip() or len(message.content) > 2000 for message in request.messages):
        raise HTTPException(status_code=422, detail="Messages must contain 1 to 2000 characters.")
    if request.messages[-1].role != "user":
        raise HTTPException(status_code=422, detail="The last message must be from the user.")

    conversation = "\n".join(
        f"{'User' if message.role == 'user' else 'Assistant'}: {message.content.strip()}"
        for message in request.messages
    )
    response = await get_chat_agent().run(
        "Continue this conversation and answer the latest user message:\n" + conversation
    )
    return {"reply": response.text}


@app.post("/auth/login")
def login(email: str, password: str, response: Response):
    password_hash = users.get(email)
    if not password_hash or not secrets.compare_digest(password_hash, hash_password(password)):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = email
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_id,
        httponly=True,
        samesite="strict",
        max_age=8 * 60 * 60,
    )
    return {"message": "Signed in", "email": email}


@app.post("/auth/logout")
def logout(response: Response, session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if session_id:
        sessions.pop(session_id, None)
    response.delete_cookie(key=SESSION_COOKIE)
    return {"message": "Signed out"}


@app.get("/activities")
def get_activities(email: str = Depends(require_login)):
    del email
    return activities


@app.get("/activities/options")
def get_activity_options():
    return list(activities.keys())


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

# Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(status_code=400, detail="Student already signed up for this activity")
   
    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/signup")
def unregister_from_activity(
    activity_name: str,
    email: str,
    signed_in_email: str = Depends(require_login),
):
    del signed_in_email
    """Remove a student from an activity"""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    activity = activities[activity_name]
    if email not in activity["participants"]:
        raise HTTPException(status_code=404, detail="Student is not signed up for this activity")

    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
