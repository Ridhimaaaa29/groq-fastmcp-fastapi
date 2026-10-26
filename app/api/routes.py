from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from langfuse import observe

from app import config
from app.instrumentation import get_recent_traces
from app.llm.groq_local import ask_local
from app.llm.groq_remote import ask_remote
from app.schemas import AskRequest, AskResponse

router = APIRouter()

DASHBOARD_FILE = Path(__file__).parent.parent / 'templates' / 'dashboard.html'


@router.get('/', response_class=HTMLResponse)
def get_dashboard():
    """Serves the live interactive Langfuse observability dashboard."""
    if DASHBOARD_FILE.exists():
        return HTMLResponse(content=DASHBOARD_FILE.read_text(encoding='utf-8'))
    return HTMLResponse(content="<h1>Dashboard file not found</h1>", status_code=404)


@router.get('/api/telemetry/traces')
def get_telemetry_traces():
    """Returns recent trace summaries including tool & LLM inference timings."""
    return {"traces": get_recent_traces()}


@router.get('/health')
def health():
    return {
        'ok': True,
        'langfuse': {
            'enabled': config.LANGFUSE_ENABLED,
            'host': config.LANGFUSE_HOST,
        }
    }


@router.post('/ask/local', response_model=AskResponse)
@observe(name="api:/ask/local")
async def ask_local_route(body: AskRequest):
    return AskResponse(answer=await ask_local(body.question))


# Plain def: FastAPI runs it in a threadpool, so the sync OpenAI client is fine.
@router.post('/ask/remote', response_model=AskResponse)
@observe(name="api:/ask/remote")
def ask_remote_route(body: AskRequest):
    return AskResponse(answer=ask_remote(body.question))
