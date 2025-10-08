"""
title: Colab Code Runner
author: Pratham
description: Generate Python code from user prompt, save as .ipynb, execute using built-in Code Interpreter, upload to GitHub, and return Colab link.
requirements: nbformat
version: 1.0.0
"""

import os
import nbformat as nbf
import shutil
import subprocess
from open_webui.llm import get_llm
from open_webui.utils.tools import get_tool

# nb = nbf.v4.new_notebook()

# =========================================================
# Helper Function: Push .ipynb to GitHub and get Colab link
# =========================================================
def push_ipynb_and_get_colab(file_name: str) -> str:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment variables.")
    
    repo_path = r"D:\project\miscellaneous\ChatGUI\update\open-webui\backend\AUTOCOLLABACTIVITY"
    username = "Prathat2006"
    repo_name = "AUTOCOLLABACTIVITY"
    repo_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    branch = "main"
    local_file_path = f"D:\\project\\miscellaneous\\ChatGUI\\openwebui\\Code_Execution\\{file_name}"

    os.makedirs(repo_path, exist_ok=True)
    filename = os.path.basename(local_file_path)
    dest_path = os.path.join(repo_path, filename)
    shutil.copy(local_file_path, dest_path)

    os.chdir(repo_path)
    subprocess.run(["git", "add", filename], check=True)
    subprocess.run(["git", "commit", "-m", f"Add/Update {filename}"], check=False)
    subprocess.run(["git", "push", repo_url, branch], check=True)

    colab_url = f"https://colab.research.google.com/github/{username}/{repo_name}/blob/{branch}/{filename}"
    return colab_url


# ================================================
# ToolKit Definition
# ================================================
class Tools:
    """
    Toolkit for generating, executing, and uploading Python notebooks.
    """

    def __init__(self):
        self.valves = self.Valves()

    class Valves:
        # You can define adjustable settings here later if needed
        pass

    # =========================================================
    # Main Tool Function
    # =========================================================
    def colab_code_runner(self, user_prompt: str) -> dict:
        """
        Generate Python code from a natural language description,
        create a .ipynb file, execute it using the built-in code interpreter,
        and upload to GitHub for Colab access.

        Args:
            user_prompt (str): The user's instruction (e.g. "write factorial code")

        Returns:
            dict: { generated_code, execution_output, colab_link }
        """
        # Step 1️⃣ Get active LLM
        llm = get_llm()

        # Step 2️⃣ Generate code from user prompt
        prompt = f"Write a clean Python script that {user_prompt}. Output only valid Python code without explanations."
        response = llm.invoke(prompt)
        code = response.content.strip("`").replace("python", "").strip()

        # Step 3️⃣ Create .ipynb file
        os.makedirs(r"D:\project\miscellaneous\ChatGUI\openwebui\Code_Execution", exist_ok=True)
        file_name = f"{user_prompt.replace(' ', '_')}.ipynb"
        file_path = os.path.join(r"D:\project\miscellaneous\ChatGUI\openwebui\Code_Execution", file_name)

        nb = nbf.v4.new_notebook()
        nb.cells.append(nbf.v4.new_code_cell(code))

        with open(file_path, "w", encoding="utf-8") as f:
            nbf.write(nb, f)

        # Step 4️⃣ Execute code using built-in Code Interpreter
        code_interpreter = get_tool("code_interpreter")
        result = code_interpreter({"code": code})
        output = result.get("output") or result.get("stdout") or "No output returned."

        # Step 5️⃣ Push to GitHub and get Colab link
        try:
            colab_link = push_ipynb_and_get_colab(file_name)
        except Exception as e:
            colab_link = f"Error while uploading to GitHub: {e}"

        # Step 6️⃣ Return combined result
        return {
            "generated_code": code,
            "execution_output": output,
            "colab_link": colab_link
        }
