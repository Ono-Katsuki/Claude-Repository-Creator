import logging
import re
from typing import Dict, List

logger = logging.getLogger(__name__)

class CodeGenerator:
    def __init__(self, claude_api, tech_stack: List[str]):
        self.claude_api = claude_api
        self.tech_stack = tech_stack
        self.templates = self.load_templates()

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
            # 他の言語やパターンも同様に追加
        }
        return templates

    def generate_feature_code(self, feature: Dict[str, any]) -> str:
        """
        与えられた機能に基づいてコードを生成します。

        :param feature: 機能の詳細を含む辞書
        :return: 生成されたコード
        """
        language = self.tech_stack[0].lower()  # 簡単のため、最初の技術を言語として使用
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
        1. 適切なクラスまたは関数の定義
        2. 機能の主要なロジック
        3. エラー処理
        4. コメントで説明された受け入れ基準の実装方法

        生成されたコードは、{language}のベストプラクティスに従ってください。
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
        self.templates[language.lower()] = templates
        logger.info(f"新しい言語テンプレートが追加されました: {language}")

    def get_supported_languages(self) -> List[str]:
        """サポートされている言語のリストを返します。"""
        return list(self.templates.keys())
