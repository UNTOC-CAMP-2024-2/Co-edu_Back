import subprocess
import ast
import tempfile
import os


def validate_code(code: str):
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            # 금지된 함수나 모듈 호출을 탐지
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in {"os", "subprocess", "socket"}:
                        return False, f"Forbidden import: {alias.name}"
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in {"open", "exec", "eval", "compile", "os.system", "subprocess.run"}:
                    return False, f"Forbidden function: {node.func.id}"
        return True, None  # 코드가 유효한 경우
    except Exception as e:
        return False, f"Code validation error: {str(e)}"


def get_execution_command(language: str, code_file: str) -> list:
    commands = {
        "python": ["python", code_file],
        "javascript": ["node", code_file],
        "java": ["javac", code_file, "&&", "java", code_file.replace(".java", "")],
        "c": ["gcc", code_file, "-o", "a.out", "&&", "./a.out"],
        "cpp": ["g++", code_file, "-o", "a.out", "&&", "./a.out"]
    }
    if language not in commands:
        raise ValueError(f"Unsupported language: {language}")
    return commands[language]


def get_file_extension(language: str) -> str:
    extensions = {
        "python": ".py",
        "javascript": ".js",
        "java": ".java",
        "c": ".c",
        "cpp": ".cpp"
    }
    if language not in extensions:
        raise ValueError(f"Unsupported language: {language}")
    return extensions[language]


def execute_code(language: str, code: str, input_data: str):
    # 코드 유효성 검증 (Python 전용)
    if language == "python":
        is_valid, error_message = validate_code(code)
        if not is_valid:
            return None, f"Code validation failed: {error_message}"

    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=get_file_extension(language)) as code_file:
            code_file.write(code.encode('utf-8'))
            code_file.flush()
            code_file_path = code_file.name

        # 실행 명령 가져오기
        command = get_execution_command(language, code_file_path)

        # subprocess로 실행
        process = subprocess.run(
            " ".join(command),  # 명령을 문자열로 전달
            input=input_data,
            text=True,
            shell=True,  # 쉘 실행 필요 (&& 지원)
            capture_output=True,
            timeout=3  # 실행 시간 제한
        )
        return process.stdout.strip(), process.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, "Execution timed out."
    except Exception as e:
        return None, str(e)
    finally:
        # 임시 파일 삭제
        if 'code_file_path' in locals() and os.path.exists(code_file_path):
            os.remove(code_file_path)
        if os.path.exists("a.out"):  # C, C++ 실행 파일 삭제
            os.remove("a.out")
