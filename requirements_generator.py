import json
import re
import asyncio
import anthropic
import logging

logger = logging.getLogger(__name__)

class RequirementsGenerator:
    def __init__(self, api_key):
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)

    async def generate_requirements(self, project_description):
        cache_key = f"requirements_{hash(project_description)}"

        prompt = self.create_requirements_prompt(project_description)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                message = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4096,
                    temperature=0,
                    system="You are an AI assistant specialized in software development and repository creation. Provide detailed and structured responses.",
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
                
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    requirements = json.loads(json_str)
                    self.validate_requirements(requirements)
                    improved_requirements = await self.evaluate_and_improve_requirements(requirements, project_description)
                    return improved_requirements
                else:
                    raise ValueError("No JSON found in the response")
            except json.JSONDecodeError as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise ValueError("Invalid response format from Claude API after multiple attempts.")
            except KeyError as e:
                raise ValueError("Incomplete requirements generated.")
            except Exception as e:
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

    async def evaluate_and_improve_requirements(self, requirements, project_description):
        prompt = f"""
        Evaluate and improve the following project requirements:
        Provide the improved requirements in the same JSON format as the input.
        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.
        
        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]
        
        Project Description:
        {project_description}

        Current Requirements:
        {json.dumps(requirements, indent=2)}

        Please analyze these requirements and make the following improvements:
        1. Ensure there is a main file (e.g., main.py, index.js) in the appropriate location.
        2. Check that all necessary dependencies are included.
        3. Verify that the folder structure is logical and follows best practices for the chosen tech stack.
        4. Make sure all function and method calls are correct and consistent.
        5. Add any missing critical components for the project to function properly.
        6. Ensure the tech stack is appropriate for the project description.
        7. Verify that all features have clear and testable acceptance criteria.

        """

        message = await self.claude_client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=4096,
            temperature=0,
            system="You are an AI assistant specialized in software development and repository creation. Provide detailed and structured responses.",
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
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            improved_requirements = json.loads(json_str)
            self.validate_requirements(improved_requirements)
            return improved_requirements
        else:
            raise ValueError("No JSON found in the improved requirements response")

    def create_requirements_prompt(self, project_description):
        return f"""
        Based on the following project description, create a detailed requirements definition:

        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

        {project_description}

        For the "tech_stack" field, please only use the following allowed values:
        ["python", "javascript", "java", "react", "react native", "html", "css", "ruby"]

        Make sure to use the full filename with its extension for the "name" field within "files".
        
        Ensure that ALL fields are properly filled and that there are NO empty arrays or objects.
        Include at least one item in each array (features, tech_stack, files, etc.).
        For the folder structure, provide a realistic and comprehensive structure that reflects the project's complexity.
        Include a main file (e.g., main.py, index.js) in the appropriate location.

        Provide the requirements in the following JSON format:
        {{
            "project_name": "string",
            "description": "string",
            "features": [
                {{
                    "name": "string",
                    "description": "string",
                    "acceptance_criteria": ["string"]
                }}
            ],
            "tech_stack": ["string"],
            "folder_structure": {{
                "folder_name": {{
                    "subfolders": {{}},
                    "files": [
                        {{
                            "name": "string",
                            "type": "class|function|component",
                            "description": "string",
                            "properties": ["string"],
                            "methods": [
                                {{
                                    "name": "string",
                                    "params": ["string"],
                                    "return_type": "string",
                                    "description": "string"
                                }}
                            ]
                        }}
                    ]
                }}
            }}
        }}
        """

    def validate_requirements(self, requirements):
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                raise KeyError(f"Missing required key: {key}")
