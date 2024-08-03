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
        logger.info("Generating text requirements...")
        prompt = create_text_requirements_prompt(user_request)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _extract_text_requirements(self, response):
        match = re.search(r'<detailed_requirements>(.*?)</detailed_requirements>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def update_text_requirements(self, current_requirements, user_feedback):
        logger.info("Updating text requirements based on user feedback...")
        prompt = create_text_update_prompt(current_requirements, user_feedback)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    # JSON requirements generation methods
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
                logger.warning("Extracted JSON is incomplete. Returning raw string for completion.")
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
                logger.info(f"Attempt {attempt + 1} to ensure complete JSON")
                if isinstance(requirements, str):
                    logger.info("Requirements is a string, attempting to complete truncated JSON")
                    requirements = await self._complete_truncated_json(requirements, project_description)
                
                logger.info("Validating JSON structure")
                self._validate_json_structure(requirements)
                
                logger.info("Validating JSON content")
                self._validate_json_content(requirements)
                
                logger.info("Complete and valid JSON generated successfully")
                return requirements
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"JSON completion attempt {attempt + 1} failed: {str(e)}")
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to generate complete JSON after {max_attempts} attempts")
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
            logger.info("Attempting to complete truncated JSON")
            parsed_part, unparsed_part = self._partial_parse(incomplete_json)
            logger.info(f"Parsed part: {json.dumps(parsed_part, indent=2)}")
            logger.info(f"Unparsed part: {unparsed_part}")

            completion_prompt = create_json_completion_prompt(
                json.dumps(parsed_part, indent=2),
                unparsed_part,
                project_description
            )
            logger.info(f"JSON completion prompt:\n{completion_prompt}")

            logger.info("Requesting completion for truncated JSON")
            completion = await self._execute_claude_request(completion_prompt, lambda x: x)
            logger.info(f"Claude's completion response:\n{completion}")
            
            logger.info("Cleaning up and combining the completion part")
            completion = completion.strip()
            if completion.startswith('{'):
                completion = completion[1:]  # Remove the opening brace
            if completion.endswith('}'):
                completion = completion[:-1]  # Remove the closing brace
            logger.info(f"Cleaned completion:\n{completion}")

            # Combine parsed part and completion more carefully
            combined_json = json.dumps(parsed_part)[:-1]  # Remove closing brace
            if not combined_json.endswith(','):
                combined_json += ','
            combined_json += completion + '}'
            logger.info(f"Combined JSON before parsing:\n{combined_json}")
            
            logger.info("Parsing the combined JSON")
            completed_json = json.loads(combined_json)
            logger.info(f"Successfully parsed combined JSON:\n{json.dumps(completed_json, indent=2)}")
            return completed_json
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Error position: {e.pos}")
            logger.error(f"Error line and column: {e.lineno}:{e.colno}")
            logger.error(f"Error context: {e.doc[max(0, e.pos-50):e.pos+50]}")
            
            # Attempt to repair the JSON
            try:
                logger.info("Attempting to repair the JSON")
                repaired_json = self._repair_json(combined_json)
                logger.info(f"Repaired JSON:\n{repaired_json}")
                return json.loads(repaired_json)
            except:
                logger.error("Failed to repair the JSON")
                raise ValueError(f"Unable to parse or repair the combined JSON: {str(e)}") from e
        except Exception as e:
            logger.error(f"Error completing JSON: {str(e)}")
            raise ValueError(f"Unable to complete the truncated JSON: {str(e)}") from e

    def _repair_json(self, invalid_json: str) -> str:
        # Simple JSON repair attempt
        # Remove any trailing commas before closing braces or brackets
        repaired = re.sub(r',\s*}', '}', invalid_json)
        repaired = re.sub(r',\s*]', ']', repaired)
        
        # Ensure the JSON is properly closed
        if not repaired.endswith('}'):
            repaired += '}'
        
        return repaired

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
                    # If we can't parse even the valid part, break and return what we have
                    break

        logger.info(f"Partial parse result - Parsed: {json.dumps(parsed, indent=2)}, Unparsed: {unparsed}")
        return parsed, unparsed

    async def update_json_requirements(self, current_requirements, project_description):
        logger.info("Updating JSON requirements...")
        prompt = create_json_update_prompt(json.dumps(current_requirements, indent=2), project_description)
        updated_requirements = await self._execute_claude_request(prompt, self._extract_json_requirements)
        return await self._ensure_complete_json(updated_requirements, project_description)

    # Helper methods
    async def _execute_claude_request(self, prompt, extract_function):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                logger.info(f"Executing Claude request (attempt {attempt + 1}/{max_retries})...")
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
                    logger.info("Claude request successful.")
                    return result
                else:
                    logger.warning("No valid requirements found in the response.")
                    raise ValueError("No valid requirements found in the response")
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Attempt {attempt + 1} failed. Retrying in {2 ** attempt} seconds...")
                    await asyncio.sleep(2 ** attempt)
                else:
                    error_msg = f"Failed to execute Claude request after {max_retries} attempts: {str(e)}"
                    logger.error(error_msg)
                    raise

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
