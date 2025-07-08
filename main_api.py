import os
from fastapi import FastAPI
from fastapi import Query
from dotenv import load_dotenv
import config
from concurrent_extraction import AsynchronousExtraction
import asyncio
import time

load_dotenv()
app = FastAPI()
URL = "https://scoped.no"
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")
LLM_API_KEY = os.getenv("LLM_API_KEY")
crawler = None
chunker = None
extracted_data = None
html_content = None

@app.get("/")
async def root():
    return {"message": "Successful connection to Form Filler API",}


@app.post("/setURL")
def create_url(url: str = Query(...)):
    global URL
    URL = url
    return {"message": f"URL updated to {URL}"}



@app.get("/get_fields", response_model=config.business_data)  
def get_extracted_data() -> config.business_data:
    if extracted_data is None:
        
        return config.business_data(
            name="", orgNumber="", type="", description="", website="",
            phone="", email="", address="", postalCode="", city="",
            country="", logo="", coverImage="", established="", socialMedia={}
        )
    return extracted_data

@app.get("/get_async_extraction")
async def run_pipeline_for_site(url: str):
    # Start overall timing
    start_time = time.time()
    
    try:
        print(f"[Pipeline] Starting extraction for: {url}")
        
        # Time extractor creation
        extractor_start = time.time()
        extractor = AsynchronousExtraction(root_url=url)
        extractor_time = time.time() - extractor_start
        print(f"[Timing] Extractor created in {extractor_time:.2f}s")
        
        # Time URL discovery
        url_start = time.time()
        prioritized_urls = extractor.get_relevant_pages()
        url_time = time.time() - url_start
        print(f"[Timing] URL discovery took {url_time:.2f}s")
        print(f"[Pipeline] Found {len(prioritized_urls)} relevant pages: {prioritized_urls}")

        if not prioritized_urls:
            total_time = time.time() - start_time
            print(f"[Timing] Total time: {total_time:.2f}s (no pages found)")
            return {"error": "No relevant pages found"}

        # Time scraping and extraction
        extraction_start = time.time()
        extraction_queue = asyncio.Queue()
        result_list = []
        done_event = asyncio.Event()

        await asyncio.gather(
            extractor.async_scraper(prioritized_urls, extraction_queue),
            extractor.async_extractor(extraction_queue, result_list, done_event)
        )
        extraction_time = time.time() - extraction_start
        print(f"[Timing] Scraping + extraction took {extraction_time:.2f}s")

        # Time aggregation
        aggregation_start = time.time()
        aggregated = await extractor.aggregate_results(result_list, done_event)
        aggregation_time = time.time() - aggregation_start
        print(f"[Timing] Aggregation took {aggregation_time:.2f}s")
        
        # Calculate total time
        total_time = time.time() - start_time
        print(f"[Timing] Total pipeline time: {total_time:.2f}s")
        
        # Return clean result without timing
        return aggregated or {"message": "No data extracted"}
        
    except Exception as e:
        total_time = time.time() - start_time
        print(f"[Timing] Error after {total_time:.2f}s: {e}")
        return {"error": str(e)}