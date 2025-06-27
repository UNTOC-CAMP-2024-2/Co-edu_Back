import subprocess
import ast
import tempfile
import os
import re
import shutil
import time

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

def get_compile_command(language: str, source_path: str, output_path: str):
    if language == "cpp":
        return ["g++", source_path, "-o", output_path]
    elif language == "c":
        return ["gcc", source_path, "-o", output_path]
    elif language == "java":
        return ["javac", source_path]
    else:
        raise ValueError(f"Unsupported language for compilation: {language}")

def get_execution_command(language: str, run_target_path: str, class_name: str = None):
    if language == "python":
        return ["python3", run_target_path]
    elif language in ["cpp", "c"]:
        return [run_target_path]  # 실행파일 경로 직접 실행
    elif language == "java":
        return ["java", "-cp", run_target_path, class_name]
    else:
        raise ValueError(f"Unsupported language for execution: {language}")

def execute_code(language: str, code: str, input_data: str):
    if language == "python":
        is_valid, error_message = validate_code(code)
        if not is_valid:
            return None, f"Code validation failed: {error_message}", 0.0

    temp_dir = tempfile.mkdtemp()
    try:
        # 파일 이름 결정
        if language == "java":
            class_name = get_java_class_name(code)
            code_file_name = f"{class_name}.java"
            exec_target = class_name  # Java는 class name
        else:
            code_file_name = f"temp{get_file_extension(language)}"
            exec_target = code_file_name if language == "python" else "a.out"

        code_path = os.path.join(temp_dir, code_file_name)
        exec_path = os.path.join(temp_dir, exec_target)

        # 코드 저장
        with open(code_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 컴파일 단계 (Python은 제외)
        if language in ["cpp", "c", "java"]:
            compile_cmd = get_compile_command(language, code_path, exec_path)
            compile_proc = subprocess.run(
                compile_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=temp_dir
            )
            if compile_proc.returncode != 0:
                compile_error = compile_proc.stderr.decode().strip()
                return None, f"Compilation failed: {compile_error}", 0.0

        # 실행 커맨드 구성
        run_cmd = get_execution_command(
            language,
            exec_path if language != "java" else temp_dir,
            exec_target if language == "java" else None
        )

        # 실행 시간 측정 시작
        exec_start = time.time()
        exec_proc = subprocess.run(
            run_cmd,
            input=input_data,
            text=True,
            capture_output=True,
            cwd=temp_dir,
            timeout=3,
            shell=False
        )
        exec_end = time.time()

        stdout = exec_proc.stdout.strip()
        stderr = exec_proc.stderr.strip()
        exec_time = round(exec_end - exec_start, 3)

        return stdout, stderr, exec_time

    except subprocess.TimeoutExpired:
        return None, "Execution timed out.", 3.0
    except Exception as e:
        return None, str(e), 0.0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
