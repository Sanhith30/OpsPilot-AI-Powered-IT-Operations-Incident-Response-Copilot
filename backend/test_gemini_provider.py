from dotenv import load_dotenv
load_dotenv()

from app.ai.providers.config import LLMConfig
from app.ai.providers.factory import create_llm_provider

config = LLMConfig(
    provider="gemini",
    model="gemini-3.8-flash",
    temperature=0.0,
    timeout_seconds=60,
)

provider = create_llm_provider(config)

response = provider.generate(
    system_prompt="You are an IT operations assistant.",
    user_prompt="Explain what an incident root cause is in one sentence.",
    temperature=0.0,
)

print(response)

provider.close()
