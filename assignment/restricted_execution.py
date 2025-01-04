import subprocess
import ast
import tempfile
import os
import re
import shutil 

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


def get_java_class_name(code: str) -> str:
    """
    Java 코드에서 public class 이름을 추출합니다.
    """
    match = re.search(r'public\s+class\s+(\w+)', code)
    if match:
        return match.group(1)
    raise ValueError("No public class found in Java code.")


def get_execution_command(language: str, code_file: str, class_name: str = None) -> list:
    """
    언어에 맞는 실행 명령을 반환합니다. 자바의 경우 class_name과 경로를 포함합니다.
    """
    commands = {
        "python": ["python", code_file],
        "javascript": ["node", code_file],
        "java": ["javac", code_file, "&&", "java", "-cp", os.path.dirname(code_file), class_name],
        "c": ["gcc", code_file, "-o", "a.out", "&&", "./a.out"],
        "cpp": ["g++", code_file, "-o", "a.out", "&&", "./a.out"]
    }
    if language not in commands:
        raise ValueError(f"Unsupported language: {language}")
    return commands[language]


def get_file_extension(language: str) -> str:
    """
    언어별 파일 확장자를 반환합니다.
    """
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
    """
    코드를 실행하는 함수로, 자바의 파일명 규칙을 처리합니다.
    """
    if language == "python":
        is_valid, error_message = validate_code(code)
        if not is_valid:
            return None, f"Code validation failed: {error_message}"

    try:
        if language == "java":
            class_name = get_java_class_name(code)
            file_name = f"{class_name}.java"
        else:
            file_name = f"temp{get_file_extension(language)}"

        # 임시 디렉토리 생성 및 파일 저장
        temp_dir = tempfile.mkdtemp()
        code_file_path = os.path.join(temp_dir, file_name)

        with open(code_file_path, "w", encoding="utf-8") as code_file:
            code_file.write(code)

        if language == "java":
            command = get_execution_command(language, code_file_path, class_name)
        else:
            command = get_execution_command(language, code_file_path)

        process = subprocess.run(
            " ".join(command),
            input=input_data,
            text=True,
            shell=True,
            capture_output=True,
            timeout=3
        )
        return process.stdout.strip(), process.stderr.strip()
    except subprocess.TimeoutExpired:
        return None, "Execution timed out."
    except ValueError as e:
        return None, str(e)
    except Exception as e:
        return None, str(e)
    finally:
        # 디렉토리 및 파일 삭제
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)  # 디렉토리와 내부 파일을 모두 삭제
        if os.path.exists("a.out"):  # C, C++ 실행 파일 삭제
            os.remove("a.out")