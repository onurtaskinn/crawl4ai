import os
import json
import asyncio
from pydantic import BaseModel, Field
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from typing import Dict



class Product(BaseModel):
    name: str = Field(..., description="Name of the product.")
    price: str = Field(..., description="Price of the product.")

    

async def extract_structured_data_using_llm(
    provider: str, api_token: str = None, extra_headers: Dict[str, str] = None
):
    print(f"\n--- Extracting Structured Data with {provider} ---")

    if api_token is None and provider != "ollama":
        print(f"API token is required for {provider}. Skipping this example.")
        return

    browser_config = BrowserConfig(headless=False)

    extra_args = {"temperature": 0, "top_p": 0.9, "max_tokens": 2000}
    if extra_headers:
        extra_args["extra_headers"] = extra_headers

    crawler_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        word_count_threshold=1,
        page_timeout=80000,
        extraction_strategy=LLMExtractionStrategy(
            provider=provider,
            api_token=api_token,
            schema=Product.model_json_schema(),
            extraction_type="schema",
            instruction="""From the crawled content, extract all the products along with their prices.""",
            extra_args=extra_args,
        ),
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(
            url="https://www.hepsiburada.com/", config=crawler_config
        )
        print(result.extracted_content)
        # save the extracted content to a file
        with open("outputs/products.json", "w") as f:
            f.write(result.extracted_content)


if __name__ == "__main__":
    asyncio.run(
        extract_structured_data_using_llm(
            provider="openai/gpt-4o", api_token=os.getenv("OPENAI_API_KEY")
        )
    )