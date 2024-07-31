import anthropic
import asyncio
import logging
import re
from typing import Dict, List, Optional
from tqdm import tqdm

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, api_key: str, tech_stack: List[str]):
        self.api_key = api_key
        self.tech_stack = [self._normalize_language(lang) for lang in tech_stack]
        self.templates = self.load_templates()
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)

    def _normalize_language(self, language: str) -> str:
        """Normalizes the language name."""
        language = language.lower()
        if language in ['react', 'react.js', 'reactjs']:
            return 'react'
        if language in ['react native', 'react-native', 'reactnative']:
            return 'react native'
        return language

    def load_templates(self) -> Dict[str, Dict[str, str]]:
        """Loads templates for each language and design pattern."""
        templates = {
            'python': {
                'class': "class {class_name}:\n    def __init__(self):\n        pass\n\n    {methods}",
                'function': "def {function_name}({params}):\n    {body}",
            },
            'java': {
                'class': "public class {class_name} {{\n    {methods}\n}}",
                'method': "public {return_type} {method_name}({params}) {{\n    {body}\n}}",
            },
            'javascript': {
                'class': "class {class_name} {{\n    constructor() {{\n    }}\n\n    {methods}\n}}",
                'function': "function {function_name}({params}) {{\n    {body}\n}}",
            },
            'html': {
                'structure': "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>{title}</title>\n</head>\n<body>\n    {body}\n</body>\n</html>",
            },
            'css': {
                'rule': "{selector} {{\n    {properties}\n}}",
            },
            'ruby': {
                'class': "class {class_name}\n  def initialize\n    {initialize_body}\n  end\n\n  {methods}\nend",
                'method': "def {method_name}({params})\n  {body}\nend",
            },
            'react': {
                'component': "import React from 'react';\n\nconst {component_name} = ({props}) => {\n  return (\n    <div>\n      {/* Component content */}\n    </div>\n  );\n};\n\nexport default {component_name};",
            },
            'react native': {
                'component': "import React from 'react';\nimport {{ View, Text }} from 'react-native';\n\nconst {component_name} = ({props}) => {\n  return (\n    <View>\n      <Text>{component_name}</Text>\n    </View>\n  );\n};\n\nexport default {component_name};",
            },
        }
        return templates

    async def generate_feature_code(self, feature: Optional[Dict[str, any]], file_info: Dict[str, any], max_retries: int = 3) -> Optional[str]:
        language = self._normalize_language(self.tech_stack[0])
        template = self.templates.get(language, {})

        if not template:
            raise ValueError(f"Unsupported language: {language}")

        prompt = self._create_prompt(feature, file_info, language, template)
        system_prompt = self._create_system_prompt(language)

        for attempt in range(max_retries):
            try:
                message = await self.client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4096,
                    temperature=0,
                    system=system_prompt,
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
                processed_code = self._process_code_response(response)
                if processed_code:
                    return processed_code
                logger.warning(f"No valid code found in response for {file_info['name']} (attempt {attempt + 1}/{max_retries})")
            except Exception as e:
                logger.error(f"Error occurred during code generation for {file_info['name']} (attempt {attempt + 1}/{max_retries}): {str(e)}")
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to generate code for {file_info['name']} after {max_retries} attempts")
        return None

    def _create_prompt(self, feature: Optional[Dict[str, any]], file_info: Dict[str, any], language: str, template: Dict[str, str]) -> str:
        """Creates the prompt for code generation."""
        feature_info = ""
        if feature:
            feature_info = f"""
            Feature Name: {feature['name']}
            Feature Description: {feature['description']}
            Acceptance Criteria:
            {self._format_acceptance_criteria(feature['acceptance_criteria'])}
            """
        
        return f"""
        Generate {language} code based on the following information:

        {feature_info}

        File Information:
        Name: {file_info['name']}
        Type: {file_info['type']}
        Description: {file_info['description']}
        Properties: {', '.join(file_info.get('properties', []))}
        Methods:
        {self._format_methods(file_info.get('methods', []))}

        Use the following templates:
        {template}

        Please include the following in your code:
        1. Appropriate {file_info['type']} definition based on the file information
        2. All specified properties and methods
        3. Core logic of the feature (if applicable)
        4. Error handling (where applicable)
        5. Comments explaining the implementation

        Ensure the generated code follows best practices for {language}.
        For HTML, provide appropriate structure; for CSS, include relevant styles.
        For React, include state management and lifecycle methods as necessary.

        Please output the code in a markdown code block, using the appropriate language identifier.
        For example:

        ```{language}
        // Your code here
        ```

        This will ensure the code is properly formatted and easy to extract.
        """

    def _create_system_prompt(self, language: str) -> str:
        """Creates the system prompt for code generation."""
        return f"""
        You are an expert {language} programmer.
        Generate clean, efficient, and best practice-compliant {language} code based on the given feature requirements and file information.
        The code should be concise yet sufficiently detailed for other developers to easily understand and extend.
        Include appropriate comments to explain important parts or complex logic when necessary.
        Always consider security, performance, and scalability in your implementation.
        Aim for production-ready quality in the generated code.
        Remember to output the code in a markdown code block with the appropriate language identifier.
        """

    def _format_acceptance_criteria(self, criteria: List[str]) -> str:
        """Formats the acceptance criteria."""
        return '\n'.join([f"- {c}" for c in criteria])

    def _format_methods(self, methods: List[Dict[str, any]]) -> str:
        """Formats the methods information for the prompt."""
        formatted_methods = []
        for method in methods:
            formatted_methods.append(f"- {method['name']}({', '.join(method['params'])}): {method['return_type']}\n  Description: {method['description']}")
        return '\n'.join(formatted_methods)

    def _process_code_response(self, response: str) -> Optional[str]:
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)
        if code_blocks:
            return '\n\n'.join(code_blocks)
        
        # If no code blocks found, try to extract any content that looks like code
        lines = response.split('\n')
        code_lines = [line for line in lines if not line.startswith(('#', '//', '/*', '*', '*/')) and line.strip()]
        if code_lines:
            return '\n'.join(code_lines)
        
        return None

    def write_code_to_file(self, file_path: str, code: str) -> None:
        """Writes the generated code to the specified file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            logger.info(f"Code written to file: {file_path}")
        except IOError as e:
            logger.error(f"Error writing code to file {file_path}: {str(e)}")
            raise

    def add_language_template(self, language: str, templates: Dict[str, str]) -> None:
        """
        Adds a new language template.
        :param language: Name of the language to add
        :param templates: Dictionary of templates for the language
        """
        normalized_language = self._normalize_language(language)
        self.templates[normalized_language] = templates
        logger.info(f"New language template added: {normalized_language}")

    def get_supported_languages(self) -> List[str]:
        """Returns a list of supported languages."""
        return list(self.templates.keys())

    def get_file_extension(self, language: str) -> str:
        """Returns the file extension for the specified language."""
        extensions = {
            'python': '.py',
            'java': '.java',
            'javascript': '.js',
            'html': '.html',
            'css': '.css',
            'ruby': '.rb',
            'react': '.jsx',
            'react native': '.js',
        }
        normalized_language = self._normalize_language(language)
        return extensions.get(normalized_language, '.txt')

    async def generate_code_for_features(self, features: List[Dict[str, any]], folder_structure: Dict[str, any]) -> Dict[str, Optional[str]]:
        """
        Generates code for multiple features concurrently.
        :param features: List of feature dictionaries
        :param folder_structure: Dictionary containing folder structure and file information
        :return: Dictionary mapping feature names to generated code
        """
        async def generate_with_progress(feature, file_info):
            return f"{file_info['name']}", await self.generate_feature_code(feature, file_info)

        tasks = []
        for folder_name, folder_content in folder_structure.items():
            feature = next((f for f in features if f['name'].lower().replace(' ', '_') == folder_name), None)
            for file_info in folder_content.get('files', []):
                tasks.append(generate_with_progress(feature, file_info))

        results = {}
        with tqdm(total=len(tasks), desc="Generating Code", unit="file") as pbar:
            for future in asyncio.as_completed(tasks):
                name, code = await future
                results[name] = code
                pbar.update(1)
        
        return results
