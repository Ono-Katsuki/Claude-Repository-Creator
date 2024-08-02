import json
import re
import asyncio
import anthropic
import logging
from typing import Dict, Any, Tuple
from prompts import (
    create_text_requirements_prompt,
    create_text_update_prompt,
    create_json_requirements_prompt,
    create_json_update_prompt,
    create_json_completion_prompt
)

logger = logging.getLogger(__name__)

class RequirementsGenerator:
    def __init__(self, api_key):
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)

    # Text requirements generation methods
    async def generate_text_requirements(self, user_request):
        print("Generating text requirements...")
        prompt = create_text_requirements_prompt(user_request)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _extract_text_requirements(self, response):
        match = re.search(r'<detailed_requirements>(.*?)</detailed_requirements>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def update_text_requirements(self, current_requirements, user_feedback):
        print("Updating text requirements based on user feedback...")
        prompt = create_text_update_prompt(current_requirements, user_feedback)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    # JSON requirements generation methods
    async def generate_json_requirements(self, project_description):
        print("Generating JSON requirements...")
        prompt = create_json_requirements_prompt(project_description)
        return await self._execute_claude_request(prompt, lambda response: self._extract_json_requirements(response, project_description))

    async def _extract_json_requirements(self, response: str, project_description: str) -> Dict[str, Any]:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                requirements = json.loads(json_str)
                self._validate_json_requirements(requirements)
                return requirements
            except json.JSONDecodeError:
                print("JSON is incomplete. Attempting to complete it...")
                return await self._complete_truncated_json(json_str, project_description)
        else:
            raise ValueError("No JSON found in the response")

    def _validate_json_requirements(self, requirements: Dict[str, Any]) -> None:
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                requirements[key] = self._generate_placeholder_value(key)

    def _generate_placeholder_value(self, key: str) -> Any:
        if key in ["project_name", "description"]:
            return f"Placeholder for {key}"
        elif key in ["features", "tech_stack"]:
            return []
        elif key == "folder_structure":
            return {}
        else:
            return None

    async def _complete_truncated_json(self, incomplete_json: str, project_description: str) -> Dict[str, Any]:
        try:
            parsed_part, unparsed_part = self._partial_parse(incomplete_json)
            completion_prompt = create_json_completion_prompt(
                json.dumps(parsed_part, indent=2),
                unparsed_part,
                project_description
            )

            print("Requesting completion for truncated JSON...")
            completion = await self._execute_claude_request(completion_prompt, lambda x: x)
            
            # Remove any leading/trailing whitespace and ensure it starts with a valid JSON character
            completion = completion.strip()
            if not completion.startswith('{') and not completion.startswith('['):
                completion = '{' + completion

            # Combine the parsed part with the completion
            combined_json = json.dumps(parsed_part)[:-1] + ',' + completion[1:]
            
            completed_json = json.loads(combined_json)
            self._validate_and_fix_json(completed_json)

            print("JSON completion successful.")
            return completed_json
        except Exception as e:
            logger.error(f"Error completing JSON: {str(e)}")
            print(f"Error completing JSON: {str(e)}")
            raise ValueError("Unable to complete the truncated JSON")

    def _partial_parse(self, incomplete_json: str) -> Tuple[Dict[str, Any], str]:
        parsed = {}
        unparsed = incomplete_json

        while unparsed:
            try:
                parsed = json.loads(unparsed)
                unparsed = ""
                break
            except json.JSONDecodeError as e:
                valid_json = unparsed[:e.pos]
                try:
                    parsed = json.loads(valid_json)
                    unparsed = unparsed[e.pos:]
                except json.JSONDecodeError:
                    break

        return parsed, unparsed

    def _validate_and_fix_json(self, json_obj: Dict[str, Any]) -> None:
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in json_obj:
                json_obj[key] = self._generate_placeholder_value(key)

        if not isinstance(json_obj.get("features"), list):
            json_obj["features"] = []

        if not isinstance(json_obj.get("tech_stack"), list):
            json_obj["tech_stack"] = []

        if not isinstance(json_obj.get("folder_structure"), dict):
            json_obj["folder_structure"] = {}

    async def update_json_requirements(self, current_requirements, project_description):
        print("Updating JSON requirements...")
        prompt = create_json_update_prompt(json.dumps(current_requirements, indent=2), project_description)
        updated_requirements = await self._execute_claude_request(prompt, lambda response: self._extract_json_requirements(response, project_description))
        
        # Ensure the result is a dictionary, not a coroutine
        if asyncio.iscoroutine(updated_requirements):
            updated_requirements = await updated_requirements
        
        return updated_requirements

    # Helper methods
    async def _execute_claude_request(self, prompt, extract_function):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Executing Claude request (attempt {attempt + 1}/{max_retries})...")
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
                
                if result:
                    print("Claude request successful.")
                    return result
                else:
                    print("No valid requirements found in the response.")
                    raise ValueError("No valid requirements found in the response")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed. Retrying in {2 ** attempt} seconds...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    error_msg = f"Failed to execute Claude request after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    print(error_msg)
                    raise

    async def generate_complete_json(self, project_description):
        print("Starting generation of complete JSON...")
        incomplete_json = await self.generate_json_requirements(project_description)
        while True:
            try:
                json.loads(json.dumps(incomplete_json))
                print("Complete JSON generated successfully.")
                return incomplete_json
            except json.JSONDecodeError:
                print("JSON is still incomplete. Attempting to complete it...")
                completion = await self._complete_truncated_json(json.dumps(incomplete_json), project_description)
                incomplete_json.update(completion)
                print("JSON updated with completion. Validating again...")

    async def generate_requirements(self, project_description, output_format="json"):
        print(f"Generating requirements in {output_format} format...")
        if output_format.lower() == "json":
            return await self.generate_complete_json(project_description)
        elif output_format.lower() == "text":
            return await self.generate_text_requirements(project_description)
        else:
            raise ValueError("Invalid output format. Choose 'json' or 'text'.")

    async def update_requirements(self, current_requirements, project_description, output_format="json"):
        print(f"Updating requirements in {output_format} format...")
        if output_format.lower() == "json":
            return await self.update_json_requirements(current_requirements, project_description)
        elif output_format.lower() == "text":
            return await self.update_text_requirements(current_requirements, project_description)
        else:
            raise ValueError("Invalid output format. Choose 'json' or 'text'.")
