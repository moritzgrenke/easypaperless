# Product Requirements Document

## Vision
easypaperless is a Python API wrapper for the paperless-ngx REST API. It should be easy to use for human programmers and also be effectively usable by AI agents.

## Target Users
Python developers who want to access the paperless-ngx document management system from within their Python projects. They want to simply install the package and use it intuitively. It should largly cover all functionality of the API.

## Core Features (Roadmap)

| Priority | Feature | Status |
|----------|---------|--------|
| P0 (MVP) | _HTTP client core (auth, base request, error hierarchy)_ | Planned |
| P0 (MVP) | _Name-to-ID resolver_ | Implemented |
| P0 (MVP)  | _Document Ressource: list (with all filters/search modes)_ | Implemented |
| P0 (MVP)  | _Document Ressource: get_ | Implemented |
| P0 (MVP)  | _Document Ressource: update_ | Implemented |
| P2 | _Document Ressource: delete_ | Implemented |
| P2 | _Document Ressource: download (original, archive)_ | Implemented |
| P2 | _Document Ressource: upload_ | Implemented |
| P2 | _Document Ressource: bulk operations_ | Implemented |
| P3 | _tags Ressource: CRUD_ | Implemented |
| P3 | _correspondents Ressource: CRUD_ | Implemented |
| P3 | _document types Ressource: CRUD_ | Implemented |
| P3 | _custom fields Ressource: CRUD_ | Implemented |
| P3 | _storage paths Ressource: CRUD_ | Implemented |
| P3 | _non document ressources: bulk operations_ | Partially Implemented |
| P3 | _SyncPaperlessClient (sync wrapper)_ | Implemented |
| P3 | _Document Notes: list, create, delete_ | Implemented |
... more to be added

(features tbd)

## Success Metrics
GitHub projects building upon easypaperless.

## Constraints
No real constraints.

## Non-Goals
* We are not building a new document management system.
* We are not building an MCP server for AI agents.

---

Use `/requirements` to create detailed feature specifications for each item in the roadmap above.