from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class MeetingCreate(BaseModel):

    title: str

    description: Optional[str] = None

    scheduled_at: Optional[datetime] = None

    duration: int = 60


class MeetingResponse(BaseModel):

    id: int

    meeting_id: str

    title: str

    description: Optional[str]

    scheduled_at: Optional[datetime]

    duration: int

    invite_link: str

    status: str

    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):

    id: int

    meeting_id: str

    display_name: str

    joined_at: datetime

    is_muted: bool

    class Config:
        from_attributes = True