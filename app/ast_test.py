import ast

with open("../data/fastapi-src/fastapi/param_functions.py", "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)
source_lines = source.splitlines()

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        start = node.lineno - 1
        end = node.end_lineno
        chunk_code = "\n".join(source_lines[start:end])
        print(f"--- {node.name} ({end - start} lines) ---")
        print(chunk_code[:100])  # just first 100 chars as a preview
        print()