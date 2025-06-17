from google import genai
from google.genai import types
import logging
import os
import sys
from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
logging.info(f"Current directory: {current_dir}")
logging.info(f"Project root: {project_root}")
sys.path.insert(0, project_root)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

# 读取文件为二进制数据
file_path = "/home/liang/projects/efflux-desktop/README.md"
with open(file_path, "rb") as f:
    file_bytes = f.read()

client = genai.Client(
    api_key=os.getenv("AIHUBMIX_API_KEY"), # 🔑 换成你在 AiHubMix 生成的密钥
    http_options={"base_url": "https://aihubmix.com/gemini"}
)

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=types.Content(
        parts=[
            types.Part(
                inline_data=types.Blob(
                    data=file_bytes,
                    mime_type="text/md"
                )
            ),
            types.Part(
                text="请分析上面的 Markdown 文件内容，并总结成20字左右的简介。"
            )
        ]
    ),
    config=types.GenerateContentConfig(
        tools=[types.Tool(
            code_execution=types.ToolCodeExecution
        )]
    )
)

for part in response.candidates[0].content.parts:
    if part.text is not None:
        print(part.text)
    if getattr(part, "executable_code", None) is not None:
        print("Generated code:\n", part.executable_code.code)
    if getattr(part, "code_execution_result", None) is not None:
        print("Execution result:\n", part.code_execution_result.output)