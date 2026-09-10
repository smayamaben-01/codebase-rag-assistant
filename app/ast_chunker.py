import ast

def extract_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    tree = ast.parse(source)
    source_lines = source.splitlines()
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = node.end_lineno
            chunk_code = "\n".join(source_lines[start:end])
            docstring = ast.get_docstring(node) or ""

            chunks.append({
                "name": node.name,
                "code": chunk_code,
                "docstring": docstring,
                "file_path": filepath,
                "start_line": node.lineno
            })

    return chunks