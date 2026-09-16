#%%
import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

async def main():
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://docs.crawl4ai.com/",
        )
        # print(result.markdown[:])  # Show the first 300 characters of extracted text
        print(result.html[:])



# await main()

if __name__ == "__main__":
    asyncio.run(main())
# %%
