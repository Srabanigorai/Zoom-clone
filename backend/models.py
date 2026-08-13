from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from datetime import datetime

from database import Base


# =========================================================
# MEETING
# =========================================================

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    meeting_id = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    scheduled_at = Column(
        DateTime,
        nullable=True
    )

    duration = Column(
        Integer,
        nullable=False
    )

    invite_link = Column(
        String,
        nullable=False
    )

    status = Column(
        String,
        default="scheduled"
    )


# =========================================================
# PARTICIPANT
# =========================================================

class Participant(Base):
    __tablename__ = "participants"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    meeting_id = Column(
        String,
        ForeignKey("meetings.meeting_id"),
        nullable=False
    )

    display_name = Column(
        String,
        nullable=False
    )

    joined_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    is_muted = Column(
        Boolean,
        default=False
    )


# =========================================================
# CHAT MESSAGE
# =========================================================

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    meeting_id = Column(
        String,
        ForeignKey("meetings.meeting_id"),
        nullable=False
    )

    display_name = Column(
        String,
        nullable=False
    )

    message = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )