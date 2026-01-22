import os
import sys
import glob
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed

#翻译某个目录下pdf

def run_babeldoc(pdf, input_dir, working_dir, api_key):
    cmd = [
        "babeldoc",
        "--openai",
        "--openai-model", "deepseek-chat",
        "--openai-base-url", "https://api.deepseek.com/v1",
        "--openai-api-key", api_key,
        "--output", input_dir,   # 输出目录就是输入目录
        "--files", pdf,          # 单个文件
        "--working-dir", working_dir
    ]
    try:
        subprocess.run(cmd, check=True)
        return f"✅ 完成: {os.path.basename(pdf)}"
    except subprocess.CalledProcessError as e:
        return f"⚠️ 失败: {os.path.basename(pdf)}, 错误: {e}"

def main(input_dir):
    working_dir = r"C:/Users/15611/Desktop/translate"
    api_key = "sk-d96b43a1d6c1403283b15d791cd5cad4"

    # 查找目录下所有 PDF 文件
    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))

    if not pdf_files:
        print(f"❌ 未找到 PDF 文件: {input_dir}")
        return

    max_workers = 5  # 并行数量

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(run_babeldoc, pdf, input_dir, working_dir, api_key) for pdf in pdf_files]

        for future in as_completed(futures):
            print(future.result())

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python xxx.py <目录路径>")
        sys.exit(1)
    input_dir = sys.argv[1]
    main(input_dir)

