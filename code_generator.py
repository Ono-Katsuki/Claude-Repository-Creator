class CodeGenerator:
    def __init__(self, claude_api, tech_stack):
        self.claude_api = claude_api
        self.tech_stack = tech_stack
        self.templates = self.load_templates()

    def load_templates(self):
        # 各言語や設計パターンに応じたテンプレートをロード
        templates = {
            'python': {
                'class': "class {class_name}:\n    def __init__(self):\n        pass\n\n    {methods}",
                'function': "def {function_name}({params}):\n    {body}",
            },
            'java': {
                'class': "public class {class_name} {{\n    {methods}\n}}",
                'method': "public {return_type} {method_name}({params}) {{\n    {body}\n}}",
            },
            # 他の言語やパターンも同様に追加
        }
        return templates

    def generate_feature_code(self, feature):
        language = self.tech_stack[0]  # 簡単のため、最初の技術を言語として使用
        template = self.templates.get(language, {})

        prompt = f"""
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

        生成されたコードは、選択された言語のベストプラクティスに従ってください。
        """

        try:
            response = self.claude_api.generate_response(prompt)
            return self._process_code_response(response)
        except Exception as e:
            logger.error(f"コード生成中にエラーが発生しました: {str(e)}")
            raise

    def _format_acceptance_criteria(self, criteria):
        return '\n'.join([f"- {c}" for c in criteria])

    def _process_code_response(self, response):
        # Claude APIのレスポンスから実際のコードを抽出するロジック
        # 例: マークダウンのコードブロックを探して抽出する
        import re
        code_blocks = re.findall(r'```[\w]*\n(.*?)```', response, re.DOTALL)
        return '\n\n'.join(code_blocks)
