"""Server-enforced API-key RBAC; replace with OIDC/MFA provider for production."""
import json,time
from collections import defaultdict,deque
from fastapi import Header,HTTPException,Request
from .config import settings
_requests=defaultdict(deque)
def principal(x_api_key:str|None=Header(default=None)):
 try: users=json.loads(settings.api_keys_json); identity=users[x_api_key]
 except Exception: raise HTTPException(401,'Invalid or missing API key')
 return identity
def require(*roles):
 def dependency(user=__import__('fastapi').Depends(principal)):
  if not set(roles).intersection(user.get('roles',[])): raise HTTPException(403,'Insufficient role')
  return user
 return dependency
async def rate_limit(request:Request):
 key=request.headers.get('x-api-key',request.client.host if request.client else 'anonymous'); q=_requests[key]; now=time.time()
 while q and now-q[0]>60:q.popleft()
 if len(q)>=settings.rate_limit_per_minute: raise HTTPException(429,'Rate limit exceeded')
 q.append(now)
