import ast

def normalize_path(path):
    path = path.replace("\\", "/")
    if "fastapi-src/" in path:
        path = path.split("fastapi-src/")[-1]
    return path

def extract_chunks(filepath):
    with open(filepath, "r", encoding="utf-8") as f:  # use the REAL path to open
        source = f.read()

    tree = ast.parse(source)
    source_lines = source.splitlines()
    chunks = []
    clean_path = normalize_path(filepath)  # normalize once, for storage only

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
                "file_path": clean_path,  # normalized, for consistent storage
                "start_line": node.lineno
            })

    return chunks