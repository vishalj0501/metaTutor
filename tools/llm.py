import json
import os
from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

class LLM:

    def __init__(self, model: str = "gemini-2.5-pro", api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")):


        self.model = model
        self.api_key = api_key
        self.client = ChatGoogleGenerativeAI(
            model=model,    
            api_key=api_key
        )

    def invoke(self, prompt: str) -> str:
        response = self.client.invoke(prompt)
        return response.content