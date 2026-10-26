import asyncio
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Reconfigure stdout to utf-8 if needed on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.instrumentation import flush_langfuse
from app.llm.groq_local import ask_local

question = ' '.join(sys.argv[1:]) or 'What is 17 + 25?'
answer = asyncio.run(ask_local(question))
print(f"Question: {question}")
print(f"Answer: {answer}")
flush_langfuse()