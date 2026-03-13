# Product Requirements Document

## Vision
easypaperless is a Python API wrapper for the paperless-ngx REST API. It should be easy to use for human programmers and also be effectively usable by AI agents.

## Target Users
Python developers who want to access the paperless-ngx document management system from within their Python projects. They want to simply install the package and use it intuitively. It should largly cover all functionality of the API.

## Core Features

* Async Client and Sync Client
* Connects to a paperless-ngx instance via token.
* resources based wrapper that covers most of the functionality of the api
* custom error hierarchy
* `UNSET` sentinel for distinguishing "not provided" from explicit `None` (null) in optional parameters — enables clearing nullable fields and filtering for unset values

## Success Metrics
GitHub projects building upon easypaperless.

## Constraints
No real constraints.

## Non-Goals
* We are not building a new document management system.
* We are not building an MCP server for AI agents.

