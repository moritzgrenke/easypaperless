from easypaperless import SyncPaperlessClient

# same example with the sync client:
# we encourage you to use .env files to store your credentials later
url = "http://192.168.178.86:8100"
api_key = "d69b3da4dfd61dec7c60110bdae16637ced2b013"
with SyncPaperlessClient(url=url, api_key=api_key) as client:
    # List documents — full-text search across title and OCR content, return the last 3 docs
    docs = client.documents.list(search="test", max_results=3, ordering="added", descending=True)
    for doc in docs:
        print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

    # Fetch a single document
    doc = client.documents.get(id=1)
    print(doc.title, doc.created_date)

    # check if a "API_edited" tag already exists - otherwise create it.
    tags = client.tags.list(name_exact="API_edited")
    if not tags:
        client.tags.create(name="API_edited", color="#40bfb7")

    # Update metadata — string names are resolved to IDs automatically
    doc = client.documents.update(id=1, tags=["API_edited"])
    print(doc.title, doc.created_date, doc.tags)
