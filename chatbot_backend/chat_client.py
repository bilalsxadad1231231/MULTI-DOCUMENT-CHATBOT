from groq import Groq
from typing import Any, List, Mapping, Optional, Dict
from pydantic import Field, BaseModel  # Updated import
from langchain_core.language_models.llms import LLM



class GroqLLM(LLM, BaseModel):
    groq_api_key: str = Field(..., description="Groq API Key")
    model_name: str = Field(default="llama-3.3-70b-versatile", description="Model name to use")
    client: Optional[Any] = None

    def __init__(self, **data):
        super().__init__(**data)
        self.client = Groq(api_key=self.groq_api_key)
    
    @property
    def _llm_type(self) -> str:
        return "groq"

    def _call(self, prompt: str, stop: Optional[List[str]] = None, **kwargs: Any) -> str:
        completion = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_name,
            **kwargs
        )
        return completion.choices[0].message.content
    
    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get the identifying parameters."""
        return {
            "model_name": self.model_name
        }