import os
from fastapi import FastAPI
from fastapi import Query
from dotenv import load_dotenv
from firecrawl_client import FirecrawlClient
from config import *
import HTML_chunker as chnk
from field_extractor import FieldExtractor
import config
import traceback
from concurrent_extraction import AsynchronousExtraction
import asyncio

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

@app.post("/initialize_extraction_pipeline") 
def initialize_extraction_pipeline():
    global crawler, chunker, URL
    
    
    try:
        
        crawler = FirecrawlClient(
            api_key=FIRECRAWL_API_KEY,
            max_pages=config.CRAWLER_MAX_PAGES,
            url=URL
        )
        
        
        chunker = chnk.HTMLChunker()
        chunker.max_chunk_size = config.CHUNKER_MAX_CHUNK_SIZE
        chunker.min_chunk_size = config.CHUNKER_MIN_CHUNK_SIZE
        
        return {
            "message": f"Pipeline initialized for {URL}",
            "status": "ready",
            "crawler_ready": True,
            "chunker_ready": True
        }
    except Exception as e:
        return {
            "message": f"Initialization failed: {str(e)}",
            "status": "error",
            "crawler_ready": False,
            "chunker_ready": False
        }
    
@app.post("/get_relevant_urls")
def get_relevant_urls():
    global crawler
    if crawler is None:
        initialize_extraction_pipeline()
    relevant_urls = crawler.get_ranked_urls()

    return relevant_urls
"""
@app.post("start_extraction_priority_crawl")
def start_extraction_priority_crawl():
    global extracted_data, html_content
    crawler.prioritized_crawl()
    """
    
   

import time
import traceback

@app.post("/start_extraction")
def start_extraction():
    global extracted_data, html_content

    try:
        start_total = time.time()
        
        print("[start_extraction] Starting extraction pipeline")

        start_init = time.time()
        if crawler is None or chunker is None:
            print("[start_extraction] Initializing pipeline...")
            init_result = initialize_extraction_pipeline()
        else:
            init_result = None
        end_init = time.time()
        print(f"[start_extraction] Initialization took {end_init - start_init:.3f} seconds")

        if crawler is None or chunker is None:
            return {"error": "Pipeline initialization failed", "details": str(init_result)}

        start_crawl = time.time()
        result = crawler.prioritized_crawl()
        end_crawl = time.time()
        print(f"[start_extraction] Crawling took {end_crawl - start_crawl:.3f} seconds")

        html_content = []
        start_html_collect = time.time()
        for page in result:
            if hasattr(page, 'html') and page.html:
                html_content.append(page.html)
        end_html_collect = time.time()
        print(f"[start_extraction] Collecting HTML content took {end_html_collect - start_html_collect:.3f} seconds")

        chunks = html_content  

        start_extract = time.time()
        extractor = FieldExtractor(
            field_names=config.BUSINESS_DATA_FIELDS, 
            data_chunks=chunks, 
            field_descriptions={}
        )
        extracted_info = extractor.extract_company_info()
        extracted_data = extractor.aggregate_results(extracted_info)
        end_extract = time.time()
        print(f"[start_extraction] Data extraction took {end_extract - start_extract:.3f} seconds")

        if hasattr(extractor, 'pretty_print_extracted_data'):
            extractor.pretty_print_extracted_data(extracted_data)

        end_total = time.time()
        print(f"[start_extraction] Total extraction pipeline took {end_total - start_total:.3f} seconds")

        return {
            "message": "Extraction completed successfully",
            "status": "completed",
            "pages_processed": len(html_content),
            "fields_extracted": list(extracted_data.keys()) if extracted_data else [],
            "data_preview": str(extracted_data)[:200] + "..." if extracted_data else "No data"
        }
        
    except Exception as e:
        error_msg = f"Extraction failed: {str(e)}"
        return {
            "error": error_msg,
            "status": "failed",
            "traceback": traceback.format_exc()
        }



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
    try:
        extractor = AsynchronousExtraction(root_url=url)
        print("extractor created...")
        
        prioritized_urls = extractor.get_relevant_pages()
        print("relevant pages retrieved:", prioritized_urls)

        if not prioritized_urls:
            print("No relevant pages found.")
            return {"error": "No relevant pages found"}

        extraction_queue = asyncio.Queue()
        result_list = []
        done_event = asyncio.Event()

        await asyncio.gather(
            extractor.async_scraper(prioritized_urls, extraction_queue),
            extractor.async_extractor(extraction_queue, result_list, done_event)
        )

        aggregated = await extractor.aggregate_results(result_list, done_event)
        return aggregated or {"message": "No data extracted"}
        
    except Exception as e:
        print(f"Error in pipeline: {e}")
        return {"error": str(e)}