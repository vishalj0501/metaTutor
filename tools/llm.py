import json
import os
from typing import Dict, Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
load_dotenv()



class LLM:
    """LLM wrapper that uses real or mock implementation."""

    def __init__(self, model: str = "gemini-2.5-flash", api_key: Optional[str] = None, use_mock: bool = False):
        self.model = model

        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.client = ChatGoogleGenerativeAI(
            model=model,    
            api_key=self.api_key
        )
        
    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        if hasattr(response, 'content'):
            return response.content
        else:
            return str(response)


def get_llm(use_mock: bool = True) -> LLM:
    """
    Get LLM instance.
    
    Args:
        use_mock: Whether to use mock LLM (default True for testing)
    
    Returns:
        LLM instance
    """
    return LLM(use_mock=use_mock)