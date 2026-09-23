from ast_chunker import extract_chunks

chunks = extract_chunks("../data/fastapi-src/fastapi/applications.py")
for c in chunks:
    print(c["name"], "- docstring length:", len(c["docstring"]), "chars")