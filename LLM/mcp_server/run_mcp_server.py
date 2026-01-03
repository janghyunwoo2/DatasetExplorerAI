from mcp.server.fastmcp import FastMCP
import os
import sys
import importlib

# 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.join(current_dir, "tools") # [수정] 폴더명 변경 (plugins -> tools)

# MCP 서버 생성 (이름: DatasetExplorerTools)
mcp = FastMCP("DatasetExplorerTools")

def load_tools(): # [수정] 함수명 변경 (load_plugins -> load_tools)
    """tools 폴더에 있는 모든 도구 모듈을 로드하여 등록합니다."""
    sys.stderr.write(f"🔌 도구 로드 시작: {tools_dir}\n")
    
    # tools 폴더가 없으면 생성
    if not os.path.exists(tools_dir):
        os.makedirs(tools_dir)
        
    # 도구 폴더를 파이썬 경로에 추가
    sys.path.append(tools_dir)
    
    # 폴더 내의 .py 파일들을 순회
    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            module_name = filename[:-3] # .py 제거
            try:
                # 동적으로 모듈 임포트
                module = importlib.import_module(module_name)
                
                # register 함수가 있으면 실행
                if hasattr(module, "register"):
                    module.register(mcp)
                    sys.stderr.write(f"✅ 도구 등록 성공: {module_name}\n")
                else:
                    sys.stderr.write(f"⚠️ 도구 등록 실패 (register 함수 없음): {module_name}\n")
            except Exception as e:
                sys.stderr.write(f"❌ 도구 로드 중 오류 발생 ({module_name}): {e}\n")

if __name__ == "__main__":
    # 1. 도구 로드
    load_tools()
    
    # 2. 서버 실행
    sys.stderr.write("🚀 MCP 서버가 시작되었습니다! (Stdio 방식)\n")
    mcp.run()
