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
        requirements = await self._execute_claude_request(prompt, self._extract_json_requirements)
        return await self._ensure_complete_json(requirements, project_description)

    async def _extract_json_requirements(self, response: str) -> Dict[str, Any]:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                requirements = json.loads(json_str)
                self._validate_json_structure(requirements)
                return requirements
            except json.JSONDecodeError:
                return json_str
        else:
            raise ValueError("No JSON found in the response")

    def _validate_json_structure(self, requirements: Dict[str, Any]) -> None:
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        missing_keys = [key for key in required_keys if key not in requirements]
        if missing_keys:
            raise ValueError(f"JSON is missing required keys: {', '.join(missing_keys)}")

    async def _ensure_complete_json(self, requirements, project_description):
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                if isinstance(requirements, str):
                    requirements = await self._complete_truncated_json(requirements, project_description)
                self._validate_json_structure(requirements)
                self._validate_json_content(requirements)
                return requirements
            except (json.JSONDecodeError, ValueError) as e:
                if attempt == max_attempts - 1:
                    raise ValueError(f"Failed to generate complete JSON after {max_attempts} attempts: {str(e)}") from e
                requirements = json.dumps(requirements) if isinstance(requirements, dict) else requirements

    def _validate_json_content(self, json_obj: Dict[str, Any]) -> None:
        if not isinstance(json_obj.get("features"), list) or len(json_obj["features"]) == 0:
            raise ValueError("'features' must be a non-empty list")
        if not isinstance(json_obj.get("tech_stack"), list) or len(json_obj["tech_stack"]) == 0:
            raise ValueError("'tech_stack' must be a non-empty list")
        if not isinstance(json_obj.get("folder_structure"), dict) or len(json_obj["folder_structure"]) == 0:
            raise ValueError("'folder_structure' must be a non-empty dictionary")

    async def _complete_truncated_json(self, incomplete_json: str, project_description: str) -> Dict[str, Any]:
        try:
            parsed_part, unparsed_part = self._partial_parse(incomplete_json)
            completion_prompt = create_json_completion_prompt(
                json.dumps(parsed_part, indent=2),
                unparsed_part,
                project_description
            )
            completion = await self._execute_claude_request(completion_prompt, lambda x: x)
            cleaned_completion = self._clean_completion(completion)
            combined_json = self._combine_json(parsed_part, cleaned_completion)
            return json.loads(combined_json)
        except json.JSONDecodeError as e:
            repaired_json = self._repair_json(combined_json)
            return json.loads(repaired_json)
        except Exception as e:
            raise ValueError(f"Unable to complete the truncated JSON: {str(e)}") from e

    def _clean_completion(self, completion: str) -> str:
        cleaned = completion.strip()
        cleaned = re.sub(r'^,\s*', '', cleaned)
        cleaned = re.sub(r',\s*$', '', cleaned)
        if cleaned.startswith('{'):
            cleaned = cleaned[1:]
        if cleaned.endswith('}'):
            cleaned = cleaned[:-1]
        return cleaned.strip()

    def _combine_json(self, parsed_part: Dict[str, Any], completion: str) -> str:
        if not parsed_part:
            return '{' + completion + '}'
        base_json = json.dumps(parsed_part)[:-1]
        if not base_json.endswith(',') and not completion.startswith(','):
            base_json += ','
        return base_json + completion + '}'

    def _repair_json(self, invalid_json: str) -> str:
        repaired = re.sub(r'^\s*,*\s*', '', invalid_json)
        repaired = re.sub(r',\s*}', '}', repaired)
        repaired = re.sub(r',\s*]', ']', repaired)
        repaired = re.sub(r'(\w+)(?=\s*:)', r'"\1"', repaired)
        if not repaired.startswith('{'):
            repaired = '{' + repaired
        if not repaired.endswith('}'):
            repaired += '}'
        return repaired

    def _partial_parse(self, incomplete_json: str) -> Tuple[Dict[str, Any], str]:
        parsed = {}
        unparsed = incomplete_json.strip()
        if unparsed.startswith('{,'):
            unparsed = '{' + unparsed[2:]
        try:
            parsed = json.loads(unparsed)
            return parsed, ""
        except json.JSONDecodeError as e:
            valid_part = unparsed[:e.pos]
            remaining_part = unparsed[e.pos:]
            last_valid_pos = valid_part.rfind('}')
            if last_valid_pos != -1:
                valid_part = valid_part[:last_valid_pos+1]
                remaining_part = unparsed[last_valid_pos+1:]
            try:
                parsed = json.loads(valid_part)
            except json.JSONDecodeError:
                parsed = {}
            return parsed, remaining_part

    async def update_json_requirements(self, current_requirements, project_description):
        logger.info("Updating JSON requirements...")
        prompt = create_json_update_prompt(json.dumps(current_requirements, indent=2), project_description)
        updated_requirements = await self._execute_claude_request(prompt, self._extract_json_requirements)
        return await self._ensure_complete_json(updated_requirements, project_description)

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
