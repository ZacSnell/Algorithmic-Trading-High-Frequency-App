import os
from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from pathlib import Path

# local imports
from . import db, models, schemas, crypto

# Load .env if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY")
if not ADMIN_API_KEY:
    raise RuntimeError("ADMIN_API_KEY must be set in .env for the backend API (development only)")

app = FastAPI(title="MLTrading Backend - Credential Store")

# create tables
models.Base.metadata.create_all(bind=db.engine)


def get_db_dep():
    db_gen = db.get_db()
    return next(db_gen)


def require_api_key(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API Key")


@app.post("/credentials", response_model=schemas.CredentialRead)
def create_credential(payload: schemas.CredentialCreate, x_api_key: str = Header(...), db: Session = Depends(get_db_dep)):
    require_api_key(x_api_key)

    username_enc = crypto.encrypt_value(payload.username)
    password_enc = crypto.encrypt_value(payload.password)
    notes_enc = crypto.encrypt_value(payload.notes) if payload.notes else None

    cred = models.Credential(
        broker=payload.broker,
        username_encrypted=username_enc,
        password_encrypted=password_enc,
        notes_encrypted=notes_enc,
    )
    db.add(cred)
    db.commit()
    db.refresh(cred)

    return schemas.CredentialRead(
        id=cred.id,
        broker=cred.broker,
        username=payload.username,
        password=payload.password,
        notes=payload.notes,
        created_at=str(cred.created_at)
    )


@app.get("/credentials/{cred_id}", response_model=schemas.CredentialRead)
def get_credential(cred_id: int, x_api_key: str = Header(...), db: Session = Depends(get_db_dep)):
    require_api_key(x_api_key)
    cred = db.query(models.Credential).filter(models.Credential.id == cred_id).first()
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")

    username = crypto.decrypt_value(cred.username_encrypted)
    password = crypto.decrypt_value(cred.password_encrypted)
    notes = crypto.decrypt_value(cred.notes_encrypted) if cred.notes_encrypted else None

    return schemas.CredentialRead(
        id=cred.id,
        broker=cred.broker,
        username=username,
        password=password,
        notes=notes,
        created_at=str(cred.created_at)
    )


@app.get("/health")
def health():
    return {"status": "ok"}
