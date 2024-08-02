import json
import re
import asyncio
import anthropic
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class RequirementsGenerator:
    def __init__(self, api_key):
        self.claude_client = anthropic.AsyncAnthropic(api_key=api_key)

    # Text requirements generation methods
    async def generate_text_requirements(self, user_request):
        print("Generating text requirements...")
        prompt = self._create_text_requirements_prompt(user_request)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _create_text_requirements_prompt(self, user_request):
        return f"""
        You are a skilled business analyst and system architect tasked with generating detailed software requirements from a user's brief request. Your goal is to expand on the user's initial idea and create a comprehensive set of requirements that cover various aspects of software development.

        Here's the user's request:
        <user_request>
        {user_request}
        </user_request>

        Based on this request, generate detailed requirements following these steps:

        1. Analyze the user request and identify the core functionality and purpose of the proposed software.

        2. Generate detailed requirements for each of the following categories. Ensure that each requirement is specific, measurable, achievable, relevant, and time-bound (SMART):

           a. Business Requirements:
              - Develop 3-5 specific use cases or user stories
              - Assign priority levels (High, Medium, Low) to each feature
              - Estimate expected user base and scale

           b. Technical Requirements:
              - Define performance requirements (e.g., response time, concurrent users)
              - Outline security requirements (e.g., authentication method, data encryption)
              - Specify scalability requirements

           c. Interface Design:
              - Describe key elements of the user interface
              - Suggest a color scheme and overall style guide
              - Outline the main screen flow

           d. Data Model:
              - List main entities and their relationships
              - Specify data types, constraints, and validation rules for key fields

           e. External System Integration:
              - Identify necessary external APIs or services
              - Suggest data synchronization frequency and methods

           f. Deployment Information:
              - Recommend suitable hosting environments
              - List required infrastructure components

           g. Testing Requirements:
              - Provide 3-5 key test scenarios
              - Suggest quality metrics (e.g., code coverage percentage)

           h. Internationalization and Localization:
              - List languages and regions to support
              - Specify date, time, and currency format requirements

           i. Accessibility Requirements:
              - Identify relevant accessibility guidelines to follow

           j. Legal Requirements:
              - Mention applicable data privacy regulations
              - Note any industry-specific compliance needs

        3. Pay special attention to use cases, data model, and UI/UX information, providing extra detail in these areas.

        4. Ensure all requirements are consistent with each other and the original user request.

        5. If any information is not explicitly mentioned or cannot be reasonably inferred from the user's request, make logical assumptions based on industry best practices. Clearly mark these assumptions.

        Present your detailed requirements in a structured format, using appropriate headings for each category. Use bullet points for individual requirements within each category. Begin your response with:

        <detailed_requirements>

        End your response with:

        </detailed_requirements>

        It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
        You need to think through every detail and edge case for each component:
        Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
        Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
        Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

        Remember to maintain a professional tone throughout the document and ensure that all requirements are clear, specific, and actionable.
        """

    def _extract_text_requirements(self, response):
        match = re.search(r'<detailed_requirements>(.*?)</detailed_requirements>', response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return None

    async def update_text_requirements(self, current_requirements, user_feedback):
        print("Updating text requirements based on user feedback...")
        prompt = self._create_text_update_prompt(current_requirements, user_feedback)
        return await self._execute_claude_request(prompt, self._extract_text_requirements)

    def _create_text_update_prompt(self, current_requirements, user_feedback):
        return f"""
        You are tasked with updating and improving the following software requirements based on user feedback. Your goal is to incorporate the user's suggestions and address any concerns while maintaining the overall structure and completeness of the requirements.

        Current Requirements:
        <current_requirements>
        {current_requirements}
        </current_requirements>

        User Feedback:
        <user_feedback>
        {user_feedback}
        </user_feedback>

        Please update the requirements based on the user feedback. Consider the following guidelines:
        1. Address all points mentioned in the user feedback.
        2. Maintain the overall structure of the requirements.
        3. Ensure consistency between new and existing requirements.
        4. If the user feedback introduces new features or major changes, integrate them seamlessly into the existing structure.
        5. If the user feedback is vague or unclear, make reasonable assumptions and note them clearly.
        6. Maintain the SMART criteria for all requirements (Specific, Measurable, Achievable, Relevant, Time-bound).

        Present your updated requirements in the same structured format as the original, using appropriate headings for each category. Use bullet points for individual requirements within each category. Begin your response with:

        <detailed_requirements>

        End your response with:

        </detailed_requirements>

        It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
        You need to think through every detail and edge case for each component:
        Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
        Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
        Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

        Ensure that your updated requirements are comprehensive, clear, and actionable.
        """

    # JSON requirements generation methods
    async def generate_json_requirements(self, project_description):
        print("Generating JSON requirements...")
        prompt = self._create_json_requirements_prompt(project_description)
        return await self._execute_claude_request(prompt, self._extract_json_requirements)

    def _create_json_requirements_prompt(self, project_description):
        return f"""
        Based on the following project description, create a detailed requirements definition:

        Produce only the JSON without any comments or additional text.

        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

        {project_description}

        Make sure to use the full filename with its extension for the "name" field within "files".
        
        Ensure that ALL fields are properly filled and that there are NO empty arrays or objects.
        Include at least one item in each array (features, tech_stack, files, etc.).
        For the folder structure, provide a realistic and comprehensive structure that reflects the project's complexity.
        Include a main file (e.g., main.py, index.js) in the appropriate location.

        It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
        You need to think through every detail and edge case for each component:
        Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
        Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
        Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

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

    async def _extract_json_requirements(self, response):
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            try:
                requirements = json.loads(json_str)
                self._validate_json_requirements(requirements)
                return requirements
            except json.JSONDecodeError:
                # JSON is incomplete, attempt to complete it
                print("JSON is incomplete. Attempting to complete it...")
                return await self._complete_truncated_json(json_str)
        else:
            raise ValueError("No JSON found in the response")

    def _validate_json_requirements(self, requirements):
        required_keys = ["project_name", "description", "features", "tech_stack", "folder_structure"]
        for key in required_keys:
            if key not in requirements:
                raise KeyError(f"Missing required key: {key}")

    async def _complete_truncated_json(self, incomplete_json):
        try:
            # Attempt to parse the incomplete JSON
            json.loads(incomplete_json)
            # If successful, the JSON is actually complete
            return json.loads(incomplete_json)
        except json.JSONDecodeError as e:
            # Find the last complete object or array
            last_complete = re.search(r'^.*\}(?!.*\})', incomplete_json, re.DOTALL)
            if last_complete:
                partial_json = last_complete.group()
            else:
                partial_json = incomplete_json

            # Create a prompt to complete the JSON
            completion_prompt = f"""
            The following JSON is incomplete. Please complete it:

            {partial_json}

            Ensure that you only provide the missing part of the JSON, starting from where it was cut off.
            Do not repeat any part of the JSON that was already provided.
            """

            try:
                print("Requesting completion for truncated JSON...")
                completion = await self._execute_claude_request(completion_prompt, lambda x: x)
                completed_json = partial_json + completion

                # Validate the completed JSON
                json.loads(completed_json)
                print("JSON completion successful.")
                return json.loads(completed_json)
            except Exception as e:
                logger.error(f"Error completing JSON: {str(e)}")
                print(f"Error completing JSON: {str(e)}")
                raise ValueError("Unable to complete the truncated JSON")

    async def update_json_requirements(self, current_requirements, project_description):
        print("Updating JSON requirements...")
        prompt = self._create_json_update_prompt(current_requirements, project_description)
        return await self._execute_claude_request(prompt, self._extract_json_requirements)

    def _create_json_update_prompt(self, current_requirements, project_description):
        return f"""
        Evaluate and improve the following project requirements:
        Provide the improved requirements in the same JSON format as the input.
        Produce only the JSON without any comments or additional text.
        It is absolutely crucial that you generate a complete and perfect JSON without any omissions or abbreviations. Every field must be properly filled, and there should be no placeholder values or TODO comments.

        It's absolutely critical that you conduct meticulous and comprehensive design for the backend, frontend, and database layers of this system. Half-assed, sloppy design work is completely unacceptable and will doom this project to failure.
        You need to think through every detail and edge case for each component:
        Backend: Robust API design, efficient algorithms, proper error handling, security measures, scalability considerations. Leave no stone unturned.
        Frontend: Intuitive UX flow, responsive layouts, accessibility, performance optimization, state management. Make it bulletproof.
        Database: Optimal schema design, indexing strategy, query optimization, data integrity rules, backup and recovery plans. Get it right the first time.

        Project Description:
        {project_description}

        Current Requirements:
        {json.dumps(current_requirements, indent=2)}

        Please analyze these requirements and make the following improvements:
        1. Ensure there is a main file (e.g., main.py, index.js) in the appropriate location.
        2. Check that all necessary dependencies are included.
        3. Verify that the folder structure is logical and follows best practices for the chosen tech stack.
        4. Make sure all function and method calls are correct and consistent.
        5. Add any missing critical components for the project to function properly.
        6. Ensure the tech stack is appropriate for the project description.
        7. Verify that all features have clear and testable acceptance criteria.
        """

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
                # Validate the JSON
                json.loads(json.dumps(incomplete_json))
                print("Complete JSON generated successfully.")
                return incomplete_json
            except json.JSONDecodeError:
                # If the JSON is incomplete, attempt to complete it
                print("JSON is still incomplete. Attempting to complete it...")
                completion = await self._complete_truncated_json(json.dumps(incomplete_json))
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
