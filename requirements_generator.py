import re
import asyncio
import anthropic
import logging
from typing import Union, Type 
from pydantic import BaseModel 
from openai import AsyncOpenAI
from prompt_manager import prompt_manager
from repository_models import Requirements

logger = logging.getLogger(__name__)

class RequirementsGenerator:
    def __init__(self, claude_api_key: str, openai_api_key: str):
        self.claude_client = anthropic.AsyncAnthropic(api_key=claude_api_key)
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)

    def _select_prompt(self, prompt_category):
        prompts = prompt_manager.list_prompts()
        category_prompts = [p for p in prompts if p[0] == prompt_category]
        
        print(f"\nAvailable {prompt_category} prompts:")
        for i, (_, name) in enumerate(category_prompts, 1):
            print(f"{i}. {name}.md")
        
        while True:
            try:
                choice = int(input("Enter the number of the prompt you want to use: ")) - 1
                if 0 <= choice < len(category_prompts):
                    return category_prompts[choice][1]
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")

    async def generate_text_requirements(self, user_request: str) -> str:
        logger.info("Generating text requirements...")
        prompt_name = self._select_prompt('create_text_requirements_prompt')
        prompt = prompt_manager.get_prompt('create_text_requirements_prompt', prompt_name, user_request=user_request)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _extract_text_requirements(self, response: str) -> str:
        match = re.search(r'<detailed_requirements>(.*?)</detailed_requirements>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        else:
            # タグがない場合は応答全体を返す
            return response.strip()

    async def update_text_requirements(self, current_requirements: str, user_feedback: str) -> str:
        logger.info("Updating text requirements based on user feedback...")
        prompt_name = self._select_prompt('create_text_update_prompt')
        prompt = prompt_manager.get_prompt('create_text_update_prompt', prompt_name, current_requirements=current_requirements, user_feedback=user_feedback)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    async def generate_structured_requirements(self, project_description: str) -> Requirements:
        logger.info("Generating structured requirements...")
        prompt_name = self._select_prompt('create_json_requirements_prompt')
        prompt = prompt_manager.get_prompt('create_json_requirements_prompt', prompt_name, project_description=project_description)
        return await self._execute_openai_request(prompt, Requirements)

    async def update_structured_requirements(self, current_requirements: Requirements, project_description: str, user_feedback: str) -> Requirements:
        logger.info("Updating structured requirements...")
        current_requirements_json = current_requirements.model_dump_json(indent=2)
        prompt_name = self._select_prompt('create_json_update_prompt')
        prompt = prompt_manager.get_prompt('create_json_update_prompt', prompt_name, current_requirements=current_requirements_json, project_description=project_description, user_feedback=user_feedback)
        return await self._execute_openai_request(prompt, Requirements)

    async def _execute_claude_request(self, prompt: str, extract_function: callable) -> str:
        max_retries = 3
        
        # Print the final prompt for debugging
        print("===== Final Prompt =====")
        print(prompt)
        print("===== End of Prompt =====")
        
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
                
                return result  
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise ValueError(f"Failed to execute Claude request after {max_retries} attempts: {str(e)}")

    async def _execute_openai_request(self, prompt: str, response_model: Type[BaseModel]) -> BaseModel:
        max_retries = 3
        
        # Print the final prompt for debugging
        print("===== Final Prompt =====")
        print(prompt)
        print("===== End of Prompt =====")
        
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

    async def generate_requirements(self, project_description: str, output_format: str = "structured") -> Union[str, Requirements]:
        logger.info(f"Generating requirements in {output_format} format...")
        if output_format.lower() == "structured":
            return await self.generate_structured_requirements(project_description)
        elif output_format.lower() == "text":
            return await self.generate_text_requirements(project_description)
        else:
            raise ValueError("Invalid output format. Choose 'structured' or 'text'.")

    async def update_requirements(self, current_requirements: Union[str, Requirements], project_description: str, user_feedback: str, output_format: str = "structured") -> Union[str, Requirements]:
        logger.info(f"Updating requirements in {output_format} format...")
        if output_format.lower() == "structured":
            if isinstance(current_requirements, str):
                current_requirements = Requirements.parse_raw(current_requirements)
            return await self.update_structured_requirements(current_requirements, project_description, user_feedback)
        elif output_format.lower() == "text":
            if isinstance(current_requirements, Requirements):
                current_requirements = current_requirements.model_dump_json(indent=2)
            return await self.update_text_requirements(current_requirements, user_feedback)
        else:
            raise ValueError("Invalid output format. Choose 'structured' or 'text'.")
