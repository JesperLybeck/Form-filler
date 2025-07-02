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
    global crawler, chunker
    
    
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


@app.post("/start_extraction")
def start_extraction():
    global extracted_data, html_content

    try:
        if crawler is None or chunker is None:
            init_result = initialize_extraction_pipeline()

        if crawler is None or chunker is None:
                return {"error": "Pipeline initialization failed", "details": str(init_result)}
        
        result = crawler.crawl_site()
        html_content = []
        for page in result.data:
            if hasattr(page, 'html') and page.html:
                html_content.append(page.html)

        chunks = html_content  
        extractor = FieldExtractor(
            field_names=config.BUSINESS_DATA_FIELDS, 
            data_chunks=chunks, 
            field_descriptions={}
        )
        extracted_info = extractor.extract_company_info()
        extracted_data = extractor.aggregate_results(extracted_info)
        
        if hasattr(extractor, 'pretty_print_extracted_data'):
            extractor.pretty_print_extracted_data(extracted_data)

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





