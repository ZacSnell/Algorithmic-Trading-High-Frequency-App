from pydantic import BaseModel, Field
from typing import Optional


class CredentialCreate(BaseModel):
    broker: str = Field(..., example="ibkr")
    username: str
    password: str
    notes: Optional[str] = None


class CredentialRead(BaseModel):
    id: int
    broker: str
    username: str
    password: str
    notes: Optional[str] = None
    created_at: Optional[str]

    class Config:
        orm_mode = True
