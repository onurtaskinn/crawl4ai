# Website RAG System

Point it at a URL, and ask questions about that page.

The site is crawled to markdown, chunked, vectorised into Weaviate, and answered
from with citations back to the source. Built on the `crawl4ai` library.

> The GitHub repository is named `crawl4ai`, but it contains no library source —
> `crawl4ai` is a dependency installed from pip, not a fork. Everything in this
> repository is application code.

## How it works

```
url
 → AsyncWebCrawler (crawl4ai)      page fetched and converted to markdown
 → chunking                        ~1000 characters, split on word boundaries
 → Weaviate Cloud                  vectorised server-side by Cohere
 → near_text query                 top 3 chunks by default
 → gpt-4o                          answers from the retrieved chunks only
 → answer + sources                every chunk returned with its url
```

Two decisions are worth naming:

- **Vectorisation happens in the database, not in the app.** The `WebContent`
  collection is configured with `text2vec_cohere`, so there is no embedding code
  anywhere — text goes in, `near_text` comes out. This is why the whole system
  fits in 120 lines.
- **The collection is dropped and recreated on startup.** This is a
  one-site-at-a-time tool by design: a scratch index for the page you are
  currently asking about, not a growing corpus.

Chunking is hand-written rather than pulled from a splitter library — fixed size,
but never breaking a word.

## Layout

```
rag_system.py          the system: crawl, chunk, store, query — 120 lines
app.py                 Streamlit UI
cli.py                 command-line version
requirements.txt
examples/              learning the library, step by step
  01_simple_crawl.py
  02_crawler_configuration.py
  03_markdown_filtering.py
  04_css_extraction.py
  05_llm_extraction_pricing.py
  05_llm_extraction_products.py
  05_llm_extraction_docs.py
  outputs/             what those scripts actually returned
```

`cli.py` does not import `rag_system` — it carries its own copy of the
`RAGSystem` class, and that copy has drifted: it still answers with
`gpt-3.5-turbo` where the shared core uses `gpt-4o`. It is the older of the two,
and it is left as it is rather than quietly merged, because the divergence is
part of what the repository records.

## The learning ladder

`examples/` is the library being learned in order, each step a runnable script
against a real site:

| Step | Target | What it teaches |
|---|---|---|
| `01_simple_crawl` | docs.crawl4ai.com | The minimum crawl |
| `02_crawler_configuration` | HuggingFace.js docs | Crawler configuration, PDF export |
| `03_markdown_filtering` | Hacker News | Filtering the markdown output |
| `04_css_extraction` | raw HTML | `JsonCssExtractionStrategy` — CSS selectors |
| `05_llm_extraction_pricing` | openai.com/api/pricing | `LLMExtractionStrategy` — model names and token fees |
| `05_llm_extraction_products` | hepsiburada.com | the same strategy — products and prices |
| `05_llm_extraction_docs` | weaviate.io quickstart | the same strategy — steps and code snippets |

The three step-05 scripts share a number because they are one step, not three:
the same strategy pointed at three different page shapes.

**The interesting step is 4 → 5**, because it is a cost decision, not a feature
list. CSS-selector extraction needs a schema written once and then costs nothing
per page; LLM extraction takes a Pydantic model as its schema and costs a model
call per page, but survives pages whose markup you have not seen. Step 4's own
comment names the tradeoff: *generate a schema (one-time cost)*.

Step 5 is then run three times with the strategy held constant and the target
varied — a pricing table, an e-commerce listing, a documentation page — to see
where schema-driven LLM extraction holds up.

What came back is kept in `examples/outputs/`:

- `pricing.json` — model names with input and output token fees, correctly
  structured
- `products.json` — product names and prices in Turkish lira
- `docs.json` — quickstart steps with their code snippets
- `pricing_empty_run.json` — `[]`. An earlier run of the same script against the
  same page returned nothing. Kept deliberately: a run that produces an empty
  array is a result about the page, not a missing file.

The library's page-export feature (PDF and full-page PNG) was tried too. Those
captures are regenerable and ran to 28 MB, so they are ignored rather than
committed.

## Stack

Python · `crawl4ai` · Weaviate Cloud with the Cohere vectoriser · OpenAI `gpt-4o`
· Streamlit

`.env` supplies `WCD_URL`, `WCD_API_KEY`, `COHERE_APIKEY` and `OPENAI_API_KEY`.

## Where it was left

One commit, 27 January 2025. The RAG system is complete and coherent; there is no
saved output from it, so how far it was exercised is not recorded. The learning
scripts clearly were run — their extraction results are checked in beside them.

What a next pass would need: persist the collection instead of dropping it, let
`cli_app.py` import the shared core rather than keeping a stale copy, and crawl
beyond a single page.

## Status

**Archived.** Not under development.
