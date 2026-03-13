import asyncio

from easypaperless import PaperlessClient


async def main():

    # create a paperless client
    # we encourage you to use .env files to store your credentials later
    url = "http://192.168.178.86:8100"
    api_key = "d69b3da4dfd61dec7c60110bdae16637ced2b013"
    async with PaperlessClient(url=url, api_key=api_key) as client:
        # List documents — full-text search across title and OCR content, return the last 3 docs
        docs = await client.documents.list(
            search="test", max_results=3, ordering="added", descending=True
        )
        for doc in docs:
            print(f"Id: {doc.id} \nTitle: {doc.title} \nadded: {doc.added}\n")

        # Fetch a single document
        doc = await client.documents.get(id=1)
        print(doc.title, doc.created_date)

        # check if a "API_edited" tag already exists - otherwise create it.
        tags = await client.tags.list(name_exact="API_edited")
        if not tags:
            await client.tags.create(name="API_edited", color="#40bfb7")

        # Update metadata — string names are resolved to IDs automatically
        await client.documents.update(id=1, tags=["API_edited"])

        # Upload and wait for processing to complete
        # doc = await client.documents.upload("path/scan.pdf", title="your title here", wait=True)
        # print("Processed:", doc.id)


asyncio.run(main())
