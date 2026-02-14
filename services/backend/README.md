ML Trading System — Backend Scaffold

This backend provides a secure credential store and basic hosting scaffold you can run 24/7. It is intentionally minimal and designed as a safe starting point; do not store production credentials without configuring a proper secrets manager (AWS KMS, HashiCorp Vault, Azure Key Vault).

Features:
- FastAPI service exposing REST endpoints to store and retrieve encrypted broker credentials
- SQLite for demo; recommended: Postgres for production
- Encryption via `cryptography.Fernet` (development). In production, use KMS and avoid local keys.
- Simple API key authentication for endpoints (development only)
- Dockerfile + docker-compose for hosting

Security Notes (READ BEFORE USING):
- Do NOT use this scaffold in production as-is.
- Replace `FERNET_KEY` with a KMS-backed key or use HashiCorp Vault/AWS Secrets Manager.
- Enable TLS in front of the service and restrict access.
- Implement robust RBAC, audit logging, key rotation, and MFA for sensitive operations.
- Check each broker's Terms of Service — programmatic logins may be restricted.

Quickstart (development):
1. Create a Python venv and install deps:
   python -m venv .venv
   .venv\Scripts\pip install -r requirements.txt

2. Create environment file `.env` (see .env.example) and set `FERNET_KEY` and `ADMIN_API_KEY`.

3. Run:
   uvicorn main:app --host 0.0.0.0 --port 8000

Endpoints:
- POST /credentials  -> store credential (body includes `broker`, `username`, `password`, `notes`)
- GET /credentials/{id} -> retrieve decrypted credential (requires API key)

Next steps I can help with:
- Integrating AWS Secrets Manager / HashiCorp Vault
- Implementing background worker to perform broker logins via official APIs
- Adding OAuth flows where available
- Integrating with Kubernetes for 24/7 orchestration

