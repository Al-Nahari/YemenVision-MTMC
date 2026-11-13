import os
from dataclasses import dataclass
@dataclass(frozen=True)
class Settings:
 database_url:str=os.getenv('DATABASE_URL','sqlite:///./traffic_platform.db')
 api_keys_json:str=os.getenv('API_KEYS_JSON','{}')
 rate_limit_per_minute:int=int(os.getenv('RATE_LIMIT_PER_MINUTE','120'))
 retention_days:int=int(os.getenv('RETENTION_DAYS','30'))
settings=Settings()
