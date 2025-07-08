import asyncio
import os
import json
import re
import ast
from urllib.parse import urlparse, urlunparse
from firecrawl import FirecrawlApp
from openai import OpenAI, AsyncOpenAI
from dotenv import load_dotenv
import config
from datetime import datetime

load_dotenv()


class AsynchronousExtraction:
    def __init__(self, root_url: str):

        self.Client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.firecrawl_app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))
        self.root_url = root_url

    def normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower().replace("www.", "")
        path = parsed.path.rstrip("/")
        return urlunparse((parsed.scheme, netloc, path, "", "", ""))

    def get_relevant_pages(self) -> list[str]:
        sitemap_result = self.firecrawl_app.map_url(self.root_url)
        relevant_pages = sitemap_result.links
        print(relevant_pages)

        # Heuristic matching
        relevant_urls = [
            url for url in relevant_pages
            if any(kw in url.lower() for kw in config.heuristic_keywords)
        ]
        print("Heuristic matches:", relevant_urls)

        if len(relevant_urls) >= config.CRAWLER_MAX_PAGES:
            print(f"Found {len(relevant_urls)} heuristic matches. Deduplicating and returning top {config.CRAWLER_MAX_PAGES} URLs.")
            seen = set()
            deduped = []
            for url in relevant_urls:
                norm = self.normalize_url(url)
                if norm not in seen:
                    deduped.append(url)
                    seen.add(norm)
                if len(deduped) >= config.CRAWLER_MAX_PAGES:
                    break
            return deduped

        print("Not enough keyword matches. Falling back to LLM for URL prioritization...")

        prompt = config.PROMPT_RELEVANT_URLS.format(
            URL_list=relevant_pages,
            max_pages=config.CRAWLER_MAX_PAGES,
            fields=config.BUSINESS_DATA_FIELDS,
        )

        response = self.model.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.2,
        )
        prioritized_urls = extract_urls_from_response(response.choices[0].message.content)

        seen = {self.normalize_url(url) for url in relevant_urls}
        for url in prioritized_urls or []:
            norm = self.normalize_url(url)
            if norm not in seen:
                relevant_urls.append(url)
                seen.add(norm)
                if len(relevant_urls) >= config.CRAWLER_MAX_PAGES:
                    break

        return relevant_urls

    async def extract_info_from_chunk(self, chunk: str):
        fields = config.BUSINESS_DATA_FIELDS
        prompt = config.PROMPT_INFORMATION_EXTRACTION.format(chunk=chunk, fields=fields)
        print(f"[Extractor] sending async request to LLM")
        result = await self.Client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
        )
        print(f"[Extractor] received response from LLM")
        return clean_response(result.choices[0].message.content)
    


  

    async def scrape_page_async(self, url: str):
        print(f"[Scraper Task] Scraping: {url}")
        scrape_result = await asyncio.to_thread(
            self.firecrawl_app.scrape_url,
            url,
            formats=['html'],
            maxAge=3600000,
            onlyMainContent=False
        )
        print(f"[Scraper Task] Finished scraping: {url}")
        
        
        return scrape_result

   

    async def async_scraper(self, urls: list[str], extraction_queue: asyncio.Queue):
        print("[Scraper] Starting async scraping...")

        async def scrape_and_enqueue(url):
            print(f"[Scraper] Spawning task to scrape: {url}")
            scrape_result = await self.scrape_page_async(url)
            print(f"[Scraper] Finished scraping: {url}")
            await extraction_queue.put(scrape_result)  # signal extractor that page is scraped by adding the scrape result as a task to the queue.

        tasks = []
        for url in urls:
            task = asyncio.create_task(scrape_and_enqueue(url))
            print(f"[Scraper] Created task for: {url}")
            tasks.append(task)

        await asyncio.gather(*tasks)  # signal extractor that all pages are scraped.

        # Signal that scraping is done
        await extraction_queue.put(None)
        print("[Scraper] All pages scraped. Sentinel added to queue.")

    async def async_extractor(self, extraction_queue: asyncio.Queue, result_list: list, completion_event: asyncio.Event):
        print("[Extractor] Extractor started. Waiting for chunks...")
        while True:
            item = await extraction_queue.get()
            if item is None:
                print("[Extractor] Received termination signal. Exiting.")
                extraction_queue.task_done()
                break
            print(f"[Extractor Task] Processing chunk of size: {len(item.html)}")
            extracted = await self.extract_info_from_chunk(item.html)
            result_list.append(extracted)
            extraction_queue.task_done()
        print("[Extractor] Setting completion event.")
        completion_event.set()

    async def aggregate_results(self, result_list: list, completion_event: asyncio.Event):
        print("[Aggregator] Waiting for extractor to finish...")
        await completion_event.wait()
        print("[Aggregator] Aggregating extracted results...")

        aggregated = {}
        for result in result_list:
            if result:
                for key, value in result.items():
                    if key not in aggregated or (value and not aggregated[key]):
                        aggregated[key] = value
        print("[Aggregator] Aggregation complete.")
        return aggregated



# ------------------------- Utility Functions -------------------------

def extract_urls_from_response(text):
    if text.startswith("```"):
        lines = text.strip().splitlines()
        if len(lines) > 2:
            text = "\n".join(lines[1:-1])
        else:
            text = ""
    try:
        urls = ast.literal_eval(text)
        return urls
    except Exception as e:
        print(f"[extract_urls_from_response] Error parsing URLs: {e}")
        return None

def clean_response(response_text):
    content = response_text.strip()
    if content.startswith("```json"):
        content = content[len("```json"):].strip()
    if content.startswith("```"):
        content = content[3:].strip()
    if content.endswith("```"):
        content = content[:-3].strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    fixed = content
    fixed = re.sub(r"\bNone\b", "null", fixed)
    fixed = re.sub(r"'([^\"']*?)'", r'"\1"', fixed)
    fixed = re.sub(r',\s*([}\]])', r'\1', fixed)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError as e:
        print(f"[clean_response] JSON parse failed: {e}")
        print(f"Raw content: {content}")
        return {}
