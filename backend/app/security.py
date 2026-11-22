"""Server-enforced API-key RBAC. Configure credentials through API_KEYS_JSON."""
import json
import time
from collections import defaultdict, deque
from fastapi import Header, HTTPException, Request
from app.config import settings

_requests = defaultdict(deque)


def principal(x_api_key: str | None = Header(default=None)):
    if not x_api_key:
        raise HTTPException(401, 'Missing API key')
    try:
        users = json.loads(settings.api_keys_json)
    except (TypeError, json.JSONDecodeError):
        raise HTTPException(503, 'API key configuration is invalid')
    identity = users.get(x_api_key)
    if not isinstance(identity, dict) or not identity.get('subject') or not isinstance(identity.get('roles'), list):
        raise HTTPException(401, 'Invalid API key')
    return identity

def require(*roles):
    def dependency(user = __import__('fastapi').Depends(principal)):
        if not set(roles).intersection(user.get('roles', [])):
            raise HTTPException(403, 'Insufficient role')
        return user
    return dependency

async def rate_limit(request: Request):
    key = request.headers.get('x-api-key', request.client.host if request.client else 'anonymous')
    q = _requests[key]
    now = time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= settings.rate_limit_per_minute:
        raise HTTPException(429, 'Rate limit exceeded')
    q.append(now)
