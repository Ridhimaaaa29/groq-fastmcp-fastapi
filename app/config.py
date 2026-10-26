import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ['GROQ_API_KEY']
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-120b')
MCP_PUBLIC_URL = os.getenv('MCP_PUBLIC_URL', '')

LANGFUSE_PUBLIC_KEY = os.getenv('LANGFUSE_PUBLIC_KEY', '')
LANGFUSE_SECRET_KEY = os.getenv('LANGFUSE_SECRET_KEY', '')
LANGFUSE_HOST = os.getenv('LANGFUSE_HOST', 'https://cloud.langfuse.com')
LANGFUSE_ENABLED = bool(LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY)
