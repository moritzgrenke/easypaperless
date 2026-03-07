# Paperless API Wrapper Project
> A Python project template with an AI-powered development workflow using specialized skills for Requirements, Architecture, API Design, Development, QA, and Deployment.

## Tech Stack
- **Language:** Python 3.11+
- **HTTP client:** `httpx` (async-first)
- **Data models:** Pydantic v2
- **Build:** Hatch + hatchling
- **Linting/formatting:** Ruff
- **Type checking:** Mypy (strict)
- **Testing:** pytest + pytest-asyncio + respx

## Project Structure
```
src/
└── easypaperless/
    ├── __init__.py          # public API: PaperlessClient, SyncPaperlessClient
    ├── client.py            # async PaperlessClient (composes from async mixins)
    ├── sync.py              # SyncPaperlessClient (composes from sync mixins)
    ├── exceptions.py        # custom exception hierarchy
    ├── models/
    │   ├── __init__.py
    │   ├── documents.py
    │   ├── tags.py
    │   ├── correspondents.py
    │   ├── document_types.py
    │   ├── storage_paths.py
    │   ├── custom_fields.py
    │   └── permissions.py
    └── _internal/
        ├── http.py          # httpx session, auth, request helpers
        ├── resolvers.py     # name-to-ID resolution and caching
        ├── mixins/          # one async mixin per resource group
        │   ├── __init__.py
        │   ├── documents.py
        │   ├── notes.py
        │   ├── upload.py
        │   ├── document_bulk.py
        │   ├── non_document_bulk.py
        │   ├── tags.py
        │   ├── correspondents.py
        │   ├── document_types.py
        │   ├── storage_paths.py
        │   └── custom_fields.py
        └── sync_mixins/     # one sync mixin per resource group (mirrors mixins/)
            ├── __init__.py
            ├── documents.py
            ├── notes.py
            ├── upload.py
            ├── document_bulk.py
            ├── non_document_bulk.py
            ├── tags.py
            ├── correspondents.py
            ├── document_types.py
            ├── storage_paths.py
            └── custom_fields.py
tests/                       # mirrors src/easypaperless/ structure
features/                    # one spec file per feature (PROJ-X-name.md)
docs/
└── PRD.md
pyproject.toml
LICENSE
README.md
CHANGELOG.md
```

## Development Workflow
1. `/requirements` - Create feature spec from idea
2. `/architecture` - Design structure, interfaces, tech decisions (no code)
3. `/dev` - general coder. Implement features.
4. `/qa` - Tests, type-check, lint, edge cases, security audit
5. `/deploy` - Package, publish (PyPI / internal), release checklist

## Key Conventions
- **Feature IDs:** PROJ-1, PROJ-2, etc. (sequential)
- **Commits:** `feat(PROJ-X): description`, `fix(PROJ-X): description`
- **Single Responsibility:** One feature per spec file; one resource group per mixin file
- **No private leakage:** `__init__.py` defines exactly what is public
- **Human-in-the-loop:** All workflows have user approval checkpoints
- **naming conventions:** @docs/api-conventions.md
- **File size:** Keep files small and focused. Split any file that grows beyond ~200 lines into logical sub-modules (e.g. per-resource mixins). Prefer many small files over one large file.

## Build & Test Commands
```bash
# Activate venv (Windows)
source venv/Scripts/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=easypaperless

# Lint + format check
ruff check .
ruff format --check .

# Type check
mypy src/easypaperless/

# Bump version (patch / minor / major)
hatch version patch

# Build package
hatch build

# Publish to PyPI
hatch publish

# Run integration tests (requires live paperless instance + tests/.env)
pytest tests/integration/ -m integration -v
```

## Product Context
@docs/PRD.md

## Feature Overview
@features/INDEX.md