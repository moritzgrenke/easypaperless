import asyncio

from easypaperless import PaperlessClient


async def main():

    # create a paperless client
    # we encourage you to use .env files to store your credentials later
    url = "your url"
    api_token = "your token"
    async with PaperlessClient(url=url, api_token=api_token) as client:
        # List documents — full-text search across title and OCR content, return the last 3 docs
        docs = await client.documents.list(
            search="test", max_results=3, ordering="added", descending=True
        )
        print(f"Total matching: {docs.count}")
        for doc in docs.results:
            print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

        # Fetch a single document
        doc = await client.documents.get(id=1)
        print(doc.title, doc.created)

        # check if a "API_edited" tag already exists - otherwise create it.
        tags = await client.tags.list(name_exact="API_edited")
        if not tags.results:
            await client.tags.create(name="API_edited", color="#40bfb7")

        # Update metadata — string names are resolved to IDs automatically
        await client.documents.update(id=1, tags=["API_edited"])

        # Upload and wait for processing to complete
        # doc = await client.documents.upload("path/scan.pdf", title="your title here", wait=True)
        # print("Processed:", doc.id)


asyncio.run(main())
