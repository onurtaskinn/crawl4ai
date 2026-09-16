import asyncio
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
import base64

async def main():
    browser_conf = BrowserConfig(headless=False)  # or False to see the browser
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        # screenshot=True,
        pdf=True,
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://huggingface.co/docs/huggingface.js/index",
            config=run_conf
        )
        print(result.markdown)
        # with open("webpage.png", "wb") as f:
        #     f.write(base64.b64decode(result.screenshot))  # 
        with open("webpage2.pdf", "wb") as f:
           f.write(result.pdf)  #      


if __name__ == "__main__":
    asyncio.run(main())