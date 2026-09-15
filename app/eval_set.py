eval_set = [
    {
        "question": "How does dependency injection work?",
        "expected_files": ["fastapi/param_functions.py", "fastapi/dependencies/utils.py"]
    },
    {
        "question": "How are path parameters like /items/{item_id} validated?",
        "expected_files": ["fastapi/param_functions.py", "fastapi/dependencies/utils.py"]
    },
    {
        "question": "How does FastAPI generate the automatic API documentation (Swagger UI)?",
        "expected_files": ["fastapi/openapi/docs.py", "fastapi/openapi/utils.py"]
    },
    {
        "question": "How is CORS (cross-origin requests) handled?",
        "expected_files": ["fastapi/middleware/cors.py"],
        "note": "KNOWN EDGE CASE: cors.py is a one-line re-export of Starlette's CORSMiddleware, contains 0 AST chunks. Expected to score 0 - documents a real limitation of AST chunking on re-export files."
    },
    {
        "question": "How does API key authentication work?",
        "expected_files": ["fastapi/security/api_key.py"]
    },
    {
        "question": "How does HTTP Basic authentication work?",
        "expected_files": ["fastapi/security/http.py"]
    },
    {
        "question": "How does OAuth2 password flow authentication work?",
        "expected_files": ["fastapi/security/oauth2.py"]
    },
    {
        "question": "How does OpenID Connect authentication work?",
        "expected_files": ["fastapi/security/open_id_connect_url.py"]
    },
    {
        "question": "How does the FastAPI class initialize routes and middleware?",
        "expected_files": ["fastapi/applications.py"]
    },
    {
        "question": "How do background tasks work in FastAPI?",
        "expected_files": ["fastapi/background.py"]
    },
    {
        "question": "How does the FastAPI CLI command work?",
        "expected_files": ["fastapi/cli.py"]
    },
    {
        "question": "How does FastAPI handle file uploads?",
        "expected_files": ["fastapi/datastructures.py"]
    },
    {
        "question": "How does FastAPI convert Python objects to JSON-compatible data (jsonable_encoder)?",
        "expected_files": ["fastapi/encoders.py"]
    },
    {
        "question": "How does FastAPI raise and handle HTTP exceptions?",
        "expected_files": ["fastapi/exceptions.py"]
    },
    {
        "question": "How does request validation error handling work?",
        "expected_files": ["fastapi/exceptions.py"]
    },
    {
        "question": "What is the difference between Query, Path, Header, and Cookie parameter classes?",
        "expected_files": ["fastapi/params.py"]
    },
    {
        "question": "How does FastAPI handle response objects and status codes?",
        "expected_files": ["fastapi/responses.py"]
    },
    {
        "question": "How does APIRouter register routes?",
        "expected_files": ["fastapi/routing.py"]
    },
    {
        "question": "How does FastAPI match incoming requests to the correct path operation function?",
        "expected_files": ["fastapi/routing.py"]
    },
    {
        "question": "How does FastAPI build the dependency tree for a route with nested dependencies?",
        "expected_files": ["fastapi/routing.py", "fastapi/dependencies/utils.py"]
    },
    {
        "question": "How does Server-Sent Events (SSE) support work in FastAPI?",
        "expected_files": ["fastapi/sse.py"]
    },
    {
        "question": "What utility functions does FastAPI provide internally (fastapi/utils.py)?",
        "expected_files": ["fastapi/utils.py"]
    },
    {
        "question": "How is a Dependant object structured and what does it represent?",
        "expected_files": ["fastapi/dependencies/models.py"]
    },
    {
        "question": "How does FastAPI resolve/solve dependencies at request time?",
        "expected_files": ["fastapi/dependencies/utils.py"]
    },
    {
        "question": "How does FastAPI's AsyncExitStack middleware manage dependency cleanup?",
        "expected_files": ["fastapi/middleware/asyncexitstack.py"]
    },
    {
        "question": "How does FastAPI generate an OpenAPI schema from route definitions?",
        "expected_files": ["fastapi/openapi/utils.py"]
    },
    {
        "question": "What Pydantic models represent the OpenAPI specification in FastAPI?",
        "expected_files": ["fastapi/openapi/models.py"]
    },
    {
        "question": "What is the base class for all FastAPI security schemes?",
        "expected_files": ["fastapi/security/base.py"]
    },
    {
        "question": "What utility functions support FastAPI's security module?",
        "expected_files": ["fastapi/security/utils.py"]
    },
    {
        "question": "How does FastAPI handle compatibility between Pydantic v1 and v2?",
        "expected_files": ["fastapi/_compat/shared.py", "fastapi/_compat/v2.py"]
    },
]