from firecrawl_client import FirecrawlClient
from fastapi import FastAPI
import os
from dotenv import load_dotenv
import json
import HTML_chunker as chunker
from field_extractor import FieldExtractor
import time

load_dotenv()

search_url = "https://www.scoped.no/"


birdview_crawler = FirecrawlClient(
    os.getenv("FIRECRAWL_API_KEY"),
    max_pages=4,
    url=search_url
)
    


start_total = time.time()

# Crawler (if enabled)
start_crawl = time.time()
print(birdview_crawler.get_map())
#result = birdview_crawler.crawl_site()
#birdview_crawler.store_crawl_result(result, "formfiller/scoped_page_")
#html_content = result.data[0].html
end_crawl = time.time()
print(f"Crawling time: {end_crawl - start_crawl:.2f} seconds")

# Chunking
start_chunk = time.time()
chunker = chunker.HTMLChunker()
html_content = chunker.load_test_data()
chunks  = html_content
#chunks = chunker.simple_chunkify_pages(html_content)
'''
for page in html_content:
    chunks.extend(chunker.DOM_tree_chunkify(page))
'''
end_chunk = time.time()
print(f"Chunking time: {end_chunk - start_chunk:.2f} seconds")

# Field extraction
start_extract = time.time()
fields = ["name", "orgNumber", "address", "phone", "email", "website", "description", "type", "logo", "coverImage", "established", "employees", "postalCode", "city", "country"]
field_extractor = FieldExtractor(fields, data_chunks=chunks, field_descriptions={})
extracted_data = field_extractor.extract_company_info()

end_extract = time.time()
print(f"Field extraction time: {end_extract - start_extract:.2f} seconds")

# Aggregation
start_agg = time.time()
aggregated_result = FieldExtractor.aggregate_results(extracted_data)
print("Aggregated result: ", json.dumps(aggregated_result, indent=2, ensure_ascii=False))
end_agg = time.time()
print(f"Aggregation time: {end_agg - start_agg:.2f} seconds")

end_total = time.time()
print(f"Total pipeline time: {end_total - start_total:.2f} seconds")


'''TODO
- Add a FastAPI server to serve the results.

OPTIMIZATIONS:
- use \map, \search, and \scrape to visit pages in a more efficient order.

-If length of page is to long, use semantic chunking, to split.

- Early stopping. If fields are filled, (with sufficient confidence) then return.

- Page prioritization: start with pages that are more likely to contain relevant information.

-improve aggregation logic to handle more complex cases, such as multiple values for the same field.

- regex, pattern matching for predicatable formatted fields.

POSSIBLE IMPROVEMENTS:
- some asyncronous notification mechanisms, to update whenever a new data is found. No need to wait for the whole pipeline to finish.
- Add a database to store the results, so that we can query them later.



'''






#<----------------------------------------------------------------------------------------------------->

