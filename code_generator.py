import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, claude_api, tech_stack: List[str]):
        self.claude_api = claude_api
        self.tech_stack = [self._normalize_language(lang) for lang in tech_stack]
        self.templates = self.load_templates()

    def _normalize_language(self, language: str) -> str:
        """言語名を正規化します。"""
        language = language.lower()
        if language in ['react', 'react.js', 'reactjs']:
            return 'react'
        if language in ['react native', 'react-native', 'reactnative']:
            return 'react native'
        return language

    def load_templates(self) -> Dict[str, Dict[str, str]]:
        """各言語や設計パターンに応じたテンプレートをロードします。"""
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
        与えられた機能に基づいてコードを生成します。
        :param feature: 機能の詳細を含む辞書
        :return: 生成されたコード
        """
        language = self._normalize_language(self.tech_stack[0])  # 最初の技術を言語として使用
        template = self.templates.get(language, {})

        if not template:
            raise ValueError(f"サポートされていない言語です: {language}")

        prompt = self._create_prompt(feature, language, template)

        try:
            response = self.claude_api.generate_response(prompt)
            return self._process_code_response(response)
        except Exception as e:
            logger.error(f"コード生成中にエラーが発生しました: {str(e)}")
            raise

    def _create_prompt(self, feature: Dict[str, any], language: str, template: Dict[str, str]) -> str:
        """プロンプトを作成します。"""
        return f"""
        以下の機能に基づいて、{language}を使用したコードを生成してください:

        機能名: {feature['name']}
        説明: {feature['description']}
        受け入れ基準:
        {self._format_acceptance_criteria(feature['acceptance_criteria'])}

        使用するテンプレート:
        {template}

        コードには以下を含めてください:
        1. 適切なクラス、関数、またはコンポーネントの定義
        2. 機能の主要なロジック
        3. エラー処理（該当する場合）
        4. コメントで説明された受け入れ基準の実装方法

        生成されたコードは、{language}のベストプラクティスに従ってください。
        HTMLの場合は適切な構造を、CSSの場合は関連するスタイルを生成してください。
        Reactの場合は、必要に応じてステート管理やライフサイクルメソッドを含めてください。
        """

    def _format_acceptance_criteria(self, criteria: List[str]) -> str:
        """受け入れ基準をフォーマットします。"""
        return '\n'.join([f"- {c}" for c in criteria])

    def _process_code_response(self, response: str) -> str:
        """
        Claude APIのレスポンスから実際のコードを抽出します。
        マークダウンのコードブロックを探して抽出します。
        """
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)
        return '\n\n'.join(code_blocks)

    def add_language_template(self, language: str, templates: Dict[str, str]) -> None:
        """
        新しい言語のテンプレートを追加します。
        :param language: 追加する言語の名前
        :param templates: 言語のテンプレート辞書
        """
        normalized_language = self._normalize_language(language)
        self.templates[normalized_language] = templates
        logger.info(f"新しい言語テンプレートが追加されました: {normalized_language}")

    def get_supported_languages(self) -> List[str]:
        """サポートされている言語のリストを返します。"""
        return list(self.templates.keys())

    def get_file_extension(self, language: str) -> str:
        """指定された言語に対応するファイル拡張子を返します。"""
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
