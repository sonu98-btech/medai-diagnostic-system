"""
Security & Compliance Utilities
HIPAA-aligned: audit logging, session management, input sanitization,
rate limiting stubs, and data anonymization helpers.
"""
import os, json, hashlib, hmac, secrets, logging, time
from datetime import datetime
from functools import wraps
from flask import request, session, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash

# ── Audit Logger ──────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

fh = logging.FileHandler(os.path.join(LOG_DIR, "audit.log"))
fh.setFormatter(logging.Formatter('%(asctime)s | %(message)s'))
audit_logger.addHandler(fh)

app_logger = logging.getLogger("app")
app_logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
sh.setFormatter(logging.Formatter('[%(levelname)s] %(asctime)s — %(message)s'))
app_logger.addHandler(sh)


def log_audit_event(event_type: str, user_id: str, details: dict = None):
    """HIPAA-compliant audit trail entry."""
    entry = {
        "timestamp":  datetime.utcnow().isoformat() + "Z",
        "event":      event_type,
        "user":       _anonymize_id(user_id),
        "ip":         _hash_ip(request.remote_addr) if request else "N/A",
        "details":    details or {},
    }
    audit_logger.info(json.dumps(entry))


def _anonymize_id(user_id: str) -> str:
    """One-way hash for HIPAA de-identification."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]

def _hash_ip(ip: str) -> str:
    return hashlib.sha256(ip.encode()).hexdigest()[:12]


# ── Rate Limiting (simple in-memory token bucket) ─────────────────────
_rate_buckets: dict = {}
MAX_REQUESTS_PER_MIN = 30

def check_rate_limit(client_id: str) -> bool:
    now = time.time()
    bucket = _rate_buckets.get(client_id, {"count": 0, "reset": now + 60})
    if now > bucket["reset"]:
        bucket = {"count": 1, "reset": now + 60}
    elif bucket["count"] >= MAX_REQUESTS_PER_MIN:
        _rate_buckets[client_id] = bucket
        return False
    else:
        bucket["count"] += 1
    _rate_buckets[client_id] = bucket
    return True


def rate_limit(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        client_id = request.remote_addr or "unknown"
        if not check_rate_limit(client_id):
            abort(429)
        return f(*args, **kwargs)
    return decorated


# ── Input Sanitization ─────────────────────────────────────────────────
def sanitize_float(value, lo: float, hi: float, default: float) -> float:
    try:
        v = float(value)
        if lo <= v <= hi:
            return v
    except (TypeError, ValueError):
        pass
    return default

def sanitize_int(value, lo: int, hi: int, default: int) -> int:
    try:
        v = int(float(value))
        if lo <= v <= hi:
            return v
    except (TypeError, ValueError):
        pass
    return default

def sanitize_symptoms(symptom_list: list, valid_symptoms: list) -> list:
    """Whitelist-based symptom validation."""
    valid_set = set(valid_symptoms)
    return [s for s in symptom_list if s in valid_set]


# ── Simple In-Memory User Store (replace with DB in production) ────────
_USERS = {
    "doctor":  generate_password_hash("clinic2024"),
    "admin":   generate_password_hash("admin2024"),
    "nurse":   generate_password_hash("nurse2024"),
}

def verify_user(username: str, password: str) -> bool:
    hashed = _USERS.get(username)
    if hashed and check_password_hash(hashed, password):
        log_audit_event("LOGIN_SUCCESS", username)
        return True
    log_audit_event("LOGIN_FAILURE", username or "unknown")
    return False


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            from flask import redirect, url_for
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)
