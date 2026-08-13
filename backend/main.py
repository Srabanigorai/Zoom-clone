from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
import uuid
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from database import engine, Base, get_db
from models import Meeting, Participant, ChatMessage
from schemas import (
    MeetingCreate,
    MeetingResponse,
    ParticipantResponse
)


app = FastAPI(title="Zoom Clone API")

# =========================================================
# WEBRTC SIGNALING
# =========================================================

connected_clients = {}


@app.websocket("/ws/{meeting_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    meeting_id: str
):
    await websocket.accept()

    if meeting_id not in connected_clients:
        connected_clients[meeting_id] = []

    connected_clients[meeting_id].append(websocket)

    try:
        while True:

            message = await websocket.receive_text()

            for client in connected_clients[meeting_id]:

                if client != websocket:
                    await client.send_text(message)

    except WebSocketDisconnect:

        if meeting_id in connected_clients:

            if websocket in connected_clients[meeting_id]:
                connected_clients[meeting_id].remove(websocket)

            if len(connected_clients[meeting_id]) == 0:
                del connected_clients[meeting_id]
# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DATABASE
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "Zoom Clone Backend Running"
    }


# =========================================================
# CREATE INSTANT MEETING
# =========================================================

@app.post(
    "/api/meetings/instant",
    response_model=MeetingResponse
)
def create_instant_meeting(
    db: Session = Depends(get_db)
):

    meeting_id = str(uuid.uuid4())[:9].replace("-", "")

    meeting = Meeting(
        meeting_id=meeting_id,
        title="Instant Meeting",
        description="Instant Zoom Clone Meeting",
        duration=60,
        invite_link=f"http://localhost:3000/meeting/{meeting_id}",
        status="active"
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


# =========================================================
# GET ALL MEETINGS
# =========================================================

@app.get(
    "/api/meetings",
    response_model=list[MeetingResponse]
)
def get_meetings(
    db: Session = Depends(get_db)
):

    return db.query(Meeting).order_by(
        Meeting.id.desc()
    ).all()


# =========================================================
# SCHEDULE MEETING
# =========================================================

@app.post(
    "/api/meetings/schedule",
    response_model=MeetingResponse
)
def schedule_meeting(
    data: MeetingCreate,
    db: Session = Depends(get_db)
):

    meeting_id = str(uuid.uuid4())[:9].replace("-", "")

    meeting = Meeting(
        meeting_id=meeting_id,
        title=data.title,
        description=data.description,
        scheduled_at=data.scheduled_at,
        duration=data.duration,
        invite_link=f"http://localhost:3000/meeting/{meeting_id}",
        status="scheduled"
    )

    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return meeting


# =========================================================
# UPCOMING MEETINGS
# =========================================================

@app.get(
    "/api/meetings/upcoming",
    response_model=list[MeetingResponse]
)
def upcoming_meetings(
    db: Session = Depends(get_db)
):

    return db.query(Meeting).filter(
        Meeting.status == "scheduled",
        Meeting.scheduled_at >= datetime.now()
    ).order_by(
        Meeting.scheduled_at.asc()
    ).all()


# =========================================================
# RECENT MEETINGS
# =========================================================

@app.get(
    "/api/meetings/recent",
    response_model=list[MeetingResponse]
)
def recent_meetings(
    db: Session = Depends(get_db)
):

    return db.query(Meeting).filter(
        Meeting.status == "completed"
    ).order_by(
        Meeting.id.desc()
    ).all()


# =========================================================
# JOIN MEETING REQUEST
# =========================================================

class JoinMeetingRequest(BaseModel):

    display_name: str


# =========================================================
# JOIN MEETING
# =========================================================

@app.post(
    "/api/meetings/{meeting_id}/join"
)
def join_meeting(
    meeting_id: str,
    data: JoinMeetingRequest,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if not data.display_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Display name is required"
        )

    participant = Participant(
        meeting_id=meeting_id,
        display_name=data.display_name.strip(),
        is_muted=False
    )

    db.add(participant)
    db.commit()
    db.refresh(participant)

    return {
        "message": "Successfully joined meeting",
        "participant_id": participant.id,
        "meeting_id": meeting_id,
        "display_name": participant.display_name,
        "is_muted": participant.is_muted
    }


# =========================================================
# GET SINGLE MEETING
# =========================================================

@app.get(
    "/api/meetings/{meeting_id}",
    response_model=MeetingResponse
)
def get_meeting(
    meeting_id: str,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    return meeting


# =========================================================
# GET PARTICIPANTS
# =========================================================

@app.get(
    "/api/meetings/{meeting_id}/participants",
    response_model=list[ParticipantResponse]
)
def get_participants(
    meeting_id: str,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    participants = db.query(Participant).filter(
        Participant.meeting_id == meeting_id
    ).all()

    return participants
@app.put("/api/meetings/{meeting_id}/mute-all")
def mute_all_participants(
    meeting_id: str,
    db: Session = Depends(get_db)
):
    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    participants = db.query(Participant).filter(
        Participant.meeting_id == meeting_id
    ).all()

    for participant in participants:
        participant.is_muted = True

    db.commit()

    return {
        "message": "All participants muted",
        "meeting_id": meeting_id,
        "count": len(participants)
    }
@app.delete("/api/meetings/{meeting_id}/participants/{participant_id}")
def remove_participant(
    meeting_id: str,
    participant_id: int,
    db: Session = Depends(get_db)
):
    participant = db.query(Participant).filter(
        Participant.id == participant_id,
        Participant.meeting_id == meeting_id
    ).first()

    if not participant:
        raise HTTPException(
            status_code=404,
            detail="Participant not found"
        )

    db.delete(participant)
    db.commit()

    return {
        "message": "Participant removed",
        "participant_id": participant_id
    }
    # =========================================================
# SEND CHAT MESSAGE
# =========================================================

class ChatMessageRequest(BaseModel):
    display_name: str
    message: str


@app.post("/api/meetings/{meeting_id}/chat")
def send_chat_message(
    meeting_id: str,
    data: ChatMessageRequest,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    if not data.display_name.strip():
        raise HTTPException(
            status_code=400,
            detail="Display name is required"
        )

    if not data.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty"
        )

    chat = ChatMessage(
        meeting_id=meeting_id,
        display_name=data.display_name.strip(),
        message=data.message.strip()
    )

    db.add(chat)
    db.commit()
    db.refresh(chat)

    return {
        "message": "Chat message sent",
        "id": chat.id,
        "meeting_id": chat.meeting_id,
        "display_name": chat.display_name,
        "chat_message": chat.message,
        "created_at": chat.created_at
    }


# =========================================================
# GET CHAT MESSAGES
# =========================================================

@app.get("/api/meetings/{meeting_id}/chat")
def get_chat_messages(
    meeting_id: str,
    db: Session = Depends(get_db)
):

    meeting = db.query(Meeting).filter(
        Meeting.meeting_id == meeting_id
    ).first()

    if not meeting:
        raise HTTPException(
            status_code=404,
            detail="Meeting not found"
        )

    messages = db.query(ChatMessage).filter(
        ChatMessage.meeting_id == meeting_id
    ).order_by(
        ChatMessage.created_at.asc()
    ).all()

    return messages