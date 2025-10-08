import os
import shutil
import subprocess
from dotenv import load_dotenv

load_dotenv()

# def push_ipynb_and_get_colab(local_file_path, repo_path, username, repo_name, branch="main"):
#     token = os.getenv("GITHUB_TOKEN")
#     if not token:
#         raise ValueError("GITHUB_TOKEN not found in environment variables.")

#     repo_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"

#     os.makedirs(repo_path, exist_ok=True)
#     filename = os.path.basename(local_file_path)
#     dest_path = os.path.join(repo_path, filename)
#     shutil.copy(local_file_path, dest_path)

#     os.chdir(repo_path)
#     subprocess.run(["git", "add", filename], check=True)
#     subprocess.run(["git", "commit", "-m", f"Add/Update {filename}"], check=False)
#     subprocess.run(["git", "push", repo_url, branch], check=True)

#     colab_url = f"https://colab.research.google.com/github/{username}/{repo_name}/blob/{branch}/{filename}"
#     return colab_url


def push_ipynb_and_get_colab(file_name):
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in environment variables.")
    repo_path = r"D:\project\miscellaneous\ChatGUI\update\open-webui\backend\AUTOCOLLABACTIVITY"
    username = "Prathat2006"
    repo_name = "AUTOCOLLABACTIVITY"

    repo_url = f"https://{username}:{token}@github.com/{username}/{repo_name}.git"
    branch="main"
    local_file_path =f"D:\project\miscellaneous\ChatGUI\openwebui\Code_Execution/{file_name}"


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


# === Usage ===
local_ipynb = r"D:\project\miscellaneous\ChatGUI\update\open-webui\backend\open_webui\Custom\trialthree.ipynb"
local_repo_path = r"D:\project\miscellaneous\ChatGUI\update\open-webui\backend\AUTOCOLLABACTIVITY"

link = push_ipynb_and_get_colab(local_ipynb)
print("Open your notebook in Colab:", link)
