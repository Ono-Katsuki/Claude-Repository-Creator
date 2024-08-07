import json
import re
import asyncio
import anthropic
import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from openai import OpenAI
from prompts import (
    create_text_requirements_prompt,
    create_text_update_prompt,
    create_json_requirements_prompt,
    create_json_update_prompt
)

logger = logging.getLogger(__name__)

class Feature(BaseModel):
    name: str
    description: str
    acceptance_criteria: List[str]

class Method(BaseModel):
    name: str
    params: List[str]
    return_type: str
    description: str

class File(BaseModel):
    name: str
    type: str
    description: str
    properties: List[str]
    methods: List[Method]

class FolderStructure(BaseModel):
    subfolders: Dict[str, 'FolderStructure'] = Field(default_factory=dict)
    files: List[File] = Field(default_factory=list)

class Requirements(BaseModel):
    project_name: str
    description: str
    features: List[Feature]
    tech_stack: List[str]
    folder_structure: Dict[str, FolderStructure]

class RequirementsGenerator:
    def __init__(self, claude_api_key, openai_api_key):
        self.claude_client = anthropic.AsyncAnthropic(api_key=claude_api_key)
        self.openai_client = OpenAI(api_key=openai_api_key)

    async def generate_text_requirements(self, user_request):
        logger.info("Generating text requirements...")
        prompt = create_text_requirements_prompt(user_request)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _extract_text_requirements(self, response):
        match = re.search(r'<detailed_requirements>(.*?)</detailed_requirements>', response, re.DOTALL)
        return match.group(1).strip() if match else None

    async def update_text_requirements(self, current_requirements, user_feedback):
        logger.info("Updating text requirements based on user feedback...")
        prompt = create_text_update_prompt(current_requirements, user_feedback)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    async def generate_json_requirements(self, project_description):
        logger.info("Generating JSON requirements...")
        prompt = create_json_requirements_prompt(project_description)
        return await self._execute_openai_request(prompt, Requirements)

    async def update_json_requirements(self, current_requirements, project_description):
        logger.info("Updating JSON requirements...")
        prompt = create_json_update_prompt(json.dumps(current_requirements, indent=2), project_description)
        return await self._execute_openai_request(prompt, Requirements)

    async def _execute_claude_request(self, prompt, extract_function):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4096,
                    temperature=0,
                    system="You are an AI assistant specialized in software development and requirements analysis. Provide detailed and structured responses.",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                }
                            ]
                        }
                    ]
                )
                response = message.content[0].text
                
                if asyncio.iscoroutinefunction(extract_function):
                    result = await extract_function(response)
                else:
                    result = extract_function(response)
                
                if result is not None:
                    return result
                else:
                    raise ValueError("No valid requirements found in the response")
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise ValueError(f"Failed to execute Claude request after {max_retries} attempts: {str(e)}")

    async def _execute_openai_request(self, prompt, response_model):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                completion = await self.openai_client.beta.chat.completions.parse(
                    model="gpt-4o-2024-08-06",
                    messages=[
                        {"role": "system", "content": "You are an AI assistant specialized in software development and requirements analysis. Provide detailed and structured responses."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format=response_model,
                )
                return completion.choices[0].message.parsed
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise ValueError(f"Failed to execute OpenAI request after {max_retries} attempts: {str(e)}")

    async def generate_requirements(self, project_description, output_format="json"):
        logger.info(f"Generating requirements in {output_format} format...")
        if output_format.lower() == "json":
            return await self.generate_json_requirements(project_description)
        elif output_format.lower() == "text":
            return await self.generate_text_requirements(project_description)
        else:
            raise ValueError("Invalid output format. Choose 'json' or 'text'.")

    async def update_requirements(self, current_requirements, project_description, output_format="json"):
        logger.info(f"Updating requirements in {output_format} format...")
        if output_format.lower() == "json":
            return await self.update_json_requirements(current_requirements, project_description)
        elif output_format.lower() == "text":
            return await self.update_text_requirements(current_requirements, project_description)
        else:
            raise ValueError("Invalid output format. Choose 'json' or 'text'.")
