import pypandoc

input_path=r"backend\open_webui\Custom\NOW7P2.md"
# output_path=r"backend\open_webui\Custom"
pypandoc.convert_file(
    input_path,
    "docx",
    outputfile=r"backend\open_webui\Custom\NOW7P2.docx",
extra_args=[
    "--standalone",
    "--from=markdown+tex_math_dollars+tex_math_single_backslash",
    "--mathml",   # produces editable Word equations (OMML)
    '--reference-doc', r"D:\project\miscellaneous\ChatGUI\update\open-webui\backend\open_webui\Custom\reference.docx"
        ]
)