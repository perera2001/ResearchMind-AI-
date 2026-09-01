from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    file_name = Column(
        String(255),
        nullable=False,
    )

    file_path = Column(
        String(500),
        nullable=False,
    )

    status = Column(
        String(50),
        default="uploaded",
    )

    page_count = Column(
        Integer,
        default=0,
    )

    chunk_count = Column(
        Integer,
        default=0,
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )