# Claude Repository Creator

このツールは、Claudeを使用して要件定義を作成し、それに基づいてリポジトリ構造とファイルを生成します。

## 機能

- Claudeを使用した要件定義の自動生成
- 生成された要件に基づくリポジトリ構造の作成
- 複数のプログラミング言語とバージョン管理システムのサポート
- コード生成と自動テスト
- ユーザーによるコードの確認と編集機能

## セットアップ

1. リポジトリをクローンします:
   ```
   git clone https://github.com/yourusername/claude-repo-creator.git
   cd claude-repo-creator
   ```

2. 仮想環境を作成し、アクティベートします:
   ```
   python -m venv venv
   source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
   ```

3. 必要なパッケージをインストールします:
   ```
   pip install -r requirements.txt
   ```

4. `config.json`ファイルを作成し、Claude APIキーを設定します:
   ```json
   {
     "api_key": "your_claude_api_key_here",
     "version_control": "git",
     "cache_expiration": 3600
   }
   ```

## 使用方法

1. スクリプトを実行します:
   ```
   python main.py
   ```

2. プロンプトに従って、プロジェクトの説明を入力します。

3. 生成されたコードを確認し、必要に応じて編集します。

4. 生成されたリポジトリ構造とファイルを確認します。

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
