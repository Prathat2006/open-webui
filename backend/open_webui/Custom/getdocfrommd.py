import pypandoc
import os
import uuid

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

# Ensure folders exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def convert_md_file(file_bytes: bytes, filename: str) -> str:
    """
    Converts a Markdown file (bytes) to DOCX.
    Returns the path to the generated DOCX file.
    """
    if not filename.endswith(".md"):
        raise ValueError("Only Markdown (.md) files are supported.")
    
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_FOLDER, f"{file_id}.md")
    output_path = os.path.join(OUTPUT_FOLDER, f"{file_id}.docx")
    
    # Save uploaded file
    with open(input_path, "wb") as f:
        f.write(file_bytes)
    
    # Convert to DOCX
    pypandoc.convert_file(
        input_path,
        "docx",
        outputfile=output_path,
    extra_args=[
        "--standalone",
        "--from=markdown+tex_math_dollars+tex_math_single_backslash",
        "--mathml",   # produces editable Word equations (OMML)
        '--reference-doc', r"open_webui\Custom\reference.docx"
            ]
    )
    return output_path
