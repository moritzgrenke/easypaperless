from easypaperless import SyncPaperlessClient

# same example with the sync client:
# we encourage you to use .env files to store your credentials later
url = "your url"
api_token = "your token"
with SyncPaperlessClient(url=url, api_token=api_token) as client:
    # List documents — full-text search across title and OCR content, return the last 3 docs
    docs = client.documents.list(search="test", max_results=3, ordering="added", descending=True)
    print(f"Total matching: {docs.count}")
    for doc in docs.results:
        print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

    # Fetch a single document
    doc = client.documents.get(id=1)
    print(doc.title, doc.created)

    # check if a "API_edited" tag already exists - otherwise create it.
    tags = client.tags.list(name_exact="API_edited")
    if not tags.results:
        client.tags.create(name="API_edited", color="#40bfb7")

    # Update metadata — string names are resolved to IDs automatically
    doc = client.documents.update(id=1, tags=["API_edited"])
    print(doc.title, doc.created, doc.tags)
