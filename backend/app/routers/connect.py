"""Connect to a user-supplied database and receive a session token."""
import hmac
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field

from app.config import settings
from app.connectors.demo import get_demo
from app.connectors.sessions import sessions
from app.connectors.url_safety import UnsafeURL
from app.core.rate_limit import RateLimiter, client_key

logger = logging.getLogger(__name__)
router = APIRouter()

# Opening a connection is expensive and probes the network: limit it harder than chat.
_connect_limiter = RateLimiter(limit=settings.connect_rate_limit_per_minute, window=60)


class ConnectRequest(BaseModel):
    url: str = Field(max_length=2048, description="Database URL, e.g. postgresql://user:pass@host:5432/db")


class ConnectResponse(BaseModel):
    session_id: str
    dialect: str
    database: str
    tables: int
    nodes: int
    edges: int
    expires_in_minutes: int


def _check_access(code: Optional[str]) -> None:
    if settings.access_code and not hmac.compare_digest(code or "", settings.access_code):
        raise HTTPException(status_code=401, detail="Invalid access code.")


@router.get("/config")
def public_config():
    """What the UI needs to know before showing the connect form."""
    return {
        "access_code_required": bool(settings.access_code),
        "supported": ["PostgreSQL", "MySQL / MariaDB", "SQL Server", "Oracle"],
        "session_ttl_minutes": settings.session_ttl_minutes,
        "sample_data_available": get_demo() is not None,
    }


@router.post("", response_model=ConnectResponse)
def connect(request: Request, body: ConnectRequest, x_access_code: Optional[str] = Header(default=None)):
    _check_access(x_access_code)
    retry = _connect_limiter.check(client_key(request))
    if retry > 0:
        raise HTTPException(status_code=429, detail="Too many connection attempts. Please wait.",
                            headers={"Retry-After": str(int(retry) + 1)})
    try:
        s = sessions.open(body.url)
    except UnsafeURL as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # Never echo driver errors: they can contain hostnames, usernames and network details.
        logger.exception("Database connection failed")
        raise HTTPException(status_code=400, detail="Could not connect. Check the URL, credentials and that the database accepts remote connections.")
    return ConnectResponse(
        session_id=s.token, dialect=s.backend, database=s.database, tables=len(s.schema.tables),
        nodes=s.graph.number_of_nodes(), edges=s.graph.number_of_edges(),
        expires_in_minutes=settings.session_ttl_minutes,
    )


@router.delete("", status_code=204)
def disconnect(x_session_id: Optional[str] = Header(default=None)):
    if x_session_id:
        sessions.close(x_session_id)
