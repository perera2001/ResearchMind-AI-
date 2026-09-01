from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: int
    user_id: int
    file_name: str
    file_path: str
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True