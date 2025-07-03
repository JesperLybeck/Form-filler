
from firecrawl import FirecrawlApp, ScrapeOptions
import os
import config
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()
import json
import ast  # Safe way to evaluate Python literals


class FirecrawlClient:
    def __init__(self, api_key: str, max_pages: int = 2, url: str = "https://scoped.no"):
        self.url = url
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v1/crawl"
        self.max_pages = max_pages
        self.app = FirecrawlApp(api_key=self.api_key)
        # Configure Gemini API
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.pages_urls = []

    def get_sitemap(self):
        sitemap_result = self.app.map_url(self.url)
        # Parse the response JSON
        

        # Access the links list
        links = sitemap_result.links
        self.pages_urls = links

        return links
    
    @staticmethod
    def extract_urls_from_response(text):
        # Remove code block formatting if present
        if text.startswith("```"):
            # Remove first line (like ```python) and last line (```)
            lines = text.strip().splitlines()
            # Remove first and last lines
            if len(lines) > 2:
                text = "\n".join(lines[1:-1])
            else:
                # fallback if no middle content
                text = ""

        try:
            urls = ast.literal_eval(text)
            return urls
        except Exception as e:
            print(f"Error parsing URLs: {e}")
            return None


    def get_ranked_urls(self):
            
            URL_list = self.get_sitemap()
            PROMPT = """
            Given this list of URLs {URL_list}, return the top {max_pages} URLs that are most likely to contain the following information:
            {fields}
            ---
            ---
            Return only a valid python list of URLs, without any additional text or explanation. Sort the list from most relevant to least relevant. No extra quotations, just a python list that can be used directly in my program.
        """
            fields = config.BUSINESS_DATA_FIELDS
            prompt = PROMPT.format(fields=fields,max_pages = self.max_pages,URL_list=URL_list)
            response = self.model.generate_content(prompt)
            response = self.extract_urls_from_response(response.text)
            print(f"Ranked URLs: {response}")
            return response

    def crawl_site(self):
        crawl_result = self.app.crawl_url(
            self.url, 
            limit=self.max_pages,
            scrape_options=ScrapeOptions(
                formats=['html'],
                maxAge=3600000  # Use cached data if less than 1 hour old
            )
        )
        
        return crawl_result
    
    def prioritized_crawl(self):
        ranked_urls = self.get_ranked_urls()
        crawl_result = []
        if not ranked_urls:
            return {"error": "No ranked URLs found. Please check the input or the model response."}
        
        for url in ranked_urls:
            scrape_result = self.app.scrape_url(
            url,
            formats=['html'],
            maxAge=3600000
        )   
            crawl_result.append(scrape_result)
        
        return crawl_result

    def get_map(self):
        return self.app.map_url(self.url)
    
    def get_html_content(self,crawl_result=None):
        
        
        return [page.html for page in crawl_result.data if hasattr(page, 'html')]
      

    def store_crawl_result(self, crawl_result, filepath):
        for i, page in enumerate(crawl_result.data):
            if hasattr(page, 'html') and page.html:
                with open(f"{filepath}{i}.html", 'w', encoding='utf-8') as f:
                    f.write(page.html)