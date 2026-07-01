from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class ConfigRecord(BaseModel):
    api_key: str
    max_depth: int
    timeout: int
    output_format: str

def load_config():
    config = {
        'api_key': os.getenv('API_KEY'),
        'max_depth': int(os.getenv('MAX_DEPTH', '5')),
        'timeout': int(os.getenv('TIMEOUT', '30')),
        'output_format': os.getenv('OUTPUT_FORMAT', 'markdown')
    }
    return ConfigRecord(**config)
