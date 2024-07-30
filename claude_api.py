import anthropic
from typing import Dict, Any

class ClaudeAPI:
    def __init__(self, api_key: str):
        self.config = self.load_config()
        self.client = anthropic.Anthropic(api_key=self.config['api_key'])
        self.model = "claude-3-5-sonnet-20240620"  # デフォルトモデル

    def generate_response(self, prompt: str, max_tokens: int = 4096, temperature: float = 0, system: str = "") -> str:
        """
        Claude APIを使用してレスポンスを生成します。

        :param prompt: ユーザーからの入力プロンプト
        :param max_tokens: 生成する最大トークン数
        :param temperature: 生成の温度（0.0から1.0）
        :param system: システムメッセージ
        :return: 生成されたレスポンス
        """
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system,
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
            return message.content[0].text
        except anthropic.APIError as e:
            raise Exception(f"API呼び出し中にエラーが発生しました: {str(e)}")

    def set_model(self, model: str) -> None:
        """
        使用するClaudeモデルを設定します。

        :param model: 使用するモデルの名前
        """
        self.model = model

    def get_available_models(self) -> Dict[str, Any]:
        """
        利用可能なClaudeモデルのリストを取得します。

        :return: 利用可能なモデルの辞書
        """
        try:
            models = self.client.models.list()
            return {model.id: model.for_dict() for model in models}
        except anthropic.APIError as e:
            raise Exception(f"モデルリストの取得中にエラーが発生しました: {str(e)}")
