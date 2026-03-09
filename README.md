# easypaperless 

[![PyPI version](https://img.shields.io/pypi/v/easypaperless.svg)](https://pypi.org/project/easypaperless/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**easypaperless** is a high-level easy-to-use Python API wrapper for [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx). 

Unlike other wrappers that simply mirror REST endpoints, **easypaperless** is designed for humans. It provides a true abstraction layer, allowing you to interact with your document management system using intuitive Python methods and objects. You don't need to understand the underlying REST API to be productive.

---

## ✨ Key Features

* **True Abstraction:** Focus on your logic, not on HTTP methods or JSON payloads.
* **Developer Experience (DX):** Full Type Hinting support. Your IDE (VS Code, PyCharm, etc.) will provide perfect autocompletion and documentation as you type.
* **Extensive Coverage:** Covers all essential workflows from document management to complex bulk operations.
* **Async-First with Sync Support:** Built on top of httpx, easypaperless is fully asynchronous by default for high-performance applications. But it also offers a synchronous wrapper for a classic blocking workflow.
* **Built-in Bulk Tools:** Easily manage hundreds of tags, correspondents, or documents with single-method calls.
* **Intuitive Error Hierarchy:** easypaperless provides descriptive, custom exceptions that tell you exactly what went wrong,

---

## 📋 Requirements

* Python: 3.11 or higher
* Paperless-ngx: 2.18 or higher (only tested with 2.18 so far)

### Core Dependencies: 

* httpx>=0.27 
* Pydantic>=2.0 

---

## 🚀 Installation

Install the package via pip:

```bash

pip install easypaperless

```

---

## 🛠 Quickstart

Get up and running in seconds. No API deep-dive required.

### async Client

``` Python

from easypaperless import PaperlessClient
import asyncio

async def main():

    # create a paperless client 
    # we encourage you to use .env files to store your credentials later
    async with PaperlessClient(url="http://localhost:8000", api_key="YOUR_TOKEN") as client:
        # List documents — full-text search across title and OCR content, return the last three added documents
        docs = await client.list_documents(search="test", max_results=3, ordering="added", descending=True)
        for doc in docs:
            print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

        # Fetch a single document
        doc = await client.get_document(id=1)
        print(doc.title, doc.created_date)

        #check if a "API_edited" tag already exists - otherwise create it.
        tags = await client.list_tags(name_exact="API_edited")
        if not tags:
            await client.create_tag(name="API_edited", color = "#40bfb7")

        # Update metadata — string names are resolved to IDs automatically
        await client.update_document(id=1, tags=["API_edited"])

        # Upload and wait for processing to complete
        #doc = await client.upload_document("path/scan.pdf", title="your title here", wait=True)
        #print("Processed:", doc.id)

asyncio.run(main())

```

### sync Client

``` Python

from easypaperless import SyncPaperlessClient

# same example with the sync client:
# we encourage you to use .env files to store your credentials later
with SyncPaperlessClient(url="http://localhost:8000", api_key="YOUR_TOKEN") as client:
    # List documents — full-text search across title and OCR content, return the last three added documents
    docs = client.list_documents(search="test", max_results=3, ordering="added", descending=True)
    for doc in docs:
        print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

    # Fetch a single document
    doc = client.get_document(id=1)
    print(doc.title, doc.created_date)

    #check if a "API_edited" tag already exists - otherwise create it.
    tags = client.list_tags(name_exact="API_edited")
    if not tags:
        client.create_tag(name="API_edited", color = "#40bfb7")

    # Update metadata — string names are resolved to IDs automatically
    client.update_document(id=1, tags=["API_edited"])

```

## 📖 Functional Overview

### Client

* **PaperlessClient / SyncPaperlessClient** Allows token based authentication. Allows to increase timeout period for slow instances.

### Documents

* **list_documents()** This is the workhorse of the wrapper and allows you to search for documents in your paperless-ngx instance and filter them by several criteria.
* **get_document()** Fetch a single document's data and optionally include its extended file metadata.
* **get_document_metadata()** Retrieve file-level technical metadata (checksums, sizes, MIME types) for a specific document.
* **update_document()** Partially update document fields like title, tags, or dates using PATCH semantics.
* **delete_document()** Permanently remove a document from your Paperless-ngx instance.
* **download_document()** Download the binary content of a document, either the archived PDF or the original file.
* **upload_document()** Upload a new file to Paperless-ngx and optionally wait for the processing task to complete.

### Document Notes

* **get_notes()** Retrieve all text notes attached to a specific document.
* **create_note()** Add a new text note to an existing document.
* **delete_note()** Remove a specific note from a document.

### Non-Document Entities

* **list_tags() / get_tag() / create_tag() / update_tag()** Manage document tags, supporting colors and matching algorithms.
* **list_correspondents() / get_correspondent() / create_correspondent()** Manage document authors, senders, or recipients.
* **list_document_types() / get_document_type() / create_document_type()** Manage categories like "Invoice," "Letter," or "Contract."
* **list_storage_paths() / get_storage_path() / create_storage_path()** Manage the physical directory structure where files are stored.
* **list_custom_fields() / get_custom_field() / create_custom_field()** Manage user-defined metadata fields for advanced document tracking.

### Bulk Operations

* **bulk_edit()** A low-level method to execute arbitrary batch operations on a list of document IDs. It is recommended to use the high level methods below.
* **bulk_add_tag()** Add a single tag to a collection of documents in one request.
* **bulk_remove_tag()** Strip a specific tag from multiple documents simultaneously.
* **bulk_modify_tags()** Atomically add and remove multiple tags across a set of documents.
* **bulk_delete()** Permanently delete a list of documents in a single batch.
* **bulk_set_correspondent()** Assign or clear the correspondent for multiple documents at once.
* **bulk_set_document_type()** Change the document type for a group of documents in one go.
* **bulk_set_storage_path()** Update the storage path for multiple documents simultaneously.
* **bulk_modify_custom_fields()** Batch update or remove custom field values across multiple documents.
* **bulk_set_permissions()** Manage ownership and access permissions for a list of documents.

### Bulk Operations (Non-Documents)

* **bulk_edit_objects()** A low level method to execute batch operations on system objects like tags or correspondents. It is recommended to use the high level methods below.
* **bulk_delete_tags() / bulk_delete_correspondents() / bulk_delete_document_types() / bulk_delete_storage_paths()** Batch delete various entity types to clean up your metadata.
* **bulk_set_permissions_tags() / _correspondents() / _document_types() / _storage_paths()** Batch update access control and ownership for specific metadata entities.


## 📚 Documentation

See the 👉 [Full API Reference (pdoc)](https://tastymojito.github.io/easypaperless/)

## 🤝 Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.


