import logging
import re
from typing import Dict, List
from claude_api import ClaudeAPI

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, claude_api: ClaudeAPI, tech_stack: List[str]):
        self.claude_api = claude_api
        self.tech_stack = [self._normalize_language(lang) for lang in tech_stack]
        self.templates = self.load_templates()

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

    def generate_feature_code(self, feature: Dict[str, any]) -> str:
        """
        Generates code based on the given feature.
        :param feature: Dictionary containing feature details
        :return: Generated code
        """
        language = self._normalize_language(self.tech_stack[0])  # Use the first technology as the language
        template = self.templates.get(language, {})

        if not template:
            raise ValueError(f"Unsupported language: {language}")

        prompt = self._create_prompt(feature, language, template)
        system_prompt = self._create_system_prompt(language)

        try:
            response = self.claude_api.generate_response(
                prompt=prompt,
                system=system_prompt,
                max_tokens=4096,
                temperature=0
            )
            return self._process_code_response(response)
        except Exception as e:
            logger.error(f"Error occurred during code generation: {str(e)}")
            raise

    def _create_prompt(self, feature: Dict[str, any], language: str, template: Dict[str, str]) -> str:
        """Creates the prompt for code generation."""
        return f"""
        Generate {language} code based on the following feature:

        Feature Name: {feature['name']}
        Description: {feature['description']}
        Acceptance Criteria:
        {self._format_acceptance_criteria(feature['acceptance_criteria'])}

        Use the following templates:
        {template}

        Please include the following in your code:
        1. Appropriate class, function, or component definitions
        2. Core logic of the feature
        3. Error handling (where applicable)
        4. Comments explaining how the implementation meets the acceptance criteria

        Ensure the generated code follows best practices for {language}.
        For HTML, provide appropriate structure; for CSS, include relevant styles.
        For React, include state management and lifecycle methods as necessary.
        """

    def _create_system_prompt(self, language: str) -> str:
        """Creates the system prompt for code generation."""
        return f"""
        You are an expert {language} programmer.
        Generate clean, efficient, and best practice-compliant {language} code based on the given feature requirements.
        The code should be concise yet sufficiently detailed for other developers to easily understand and extend.
        Include appropriate comments to explain important parts or complex logic when necessary.
        Always consider security, performance, and scalability in your implementation.
        Aim for production-ready quality in the generated code.
        """

    def _format_acceptance_criteria(self, criteria: List[str]) -> str:
        """Formats the acceptance criteria."""
        return '\n'.join([f"- {c}" for c in criteria])

    def _process_code_response(self, response: str) -> str:
        """
        Extracts the actual code from Claude API's response.
        Looks for markdown code blocks and extracts them.
        """
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)
        return '\n\n'.join(code_blocks)

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
