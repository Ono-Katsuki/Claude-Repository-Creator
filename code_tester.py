import subprocess
import tempfile
import os

class CodeTester:
    def __init__(self, tech_stack):
        self.tech_stack = tech_stack

    def test_code(self, code):
        language = self.tech_stack[0]  # 簡単のため、最初の技術を言語として使用
        
        if language == 'python':
            return self._test_python_code(code)
        elif language == 'java':
            return self._test_java_code(code)
        # 他の言語のテストメソッドも同様に追加
        else:
            return {'success': False, 'message': f'Unsupported language: {language}'}

    def _test_python_code(self, code):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code)
            temp_file_path = temp_file.name

        try:
            result = subprocess.run(['python', '-m', 'py_compile', temp_file_path], capture_output=True, text=True)
            if result.returncode == 0:
                return {'success': True, 'message': 'コードは正常にコンパイルされました。'}
            else:
                return {'success': False, 'message': f'コンパイルエラー: {result.stderr}'}
        finally:
            os.unlink(temp_file_path)

    def _test_java_code(self, code):
        # Javaコードのテストロジックを実装
        # コンパイルと基本的な構文チェックを行う
        pass
