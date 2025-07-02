from firecrawl import FirecrawlApp, ScrapeOptions


class FirecrawlClient:
    def __init__(self, api_key: str, max_pages: int = 2, url: str = "https://scoped.no"):
        self.url = url
        self.api_key = api_key
        self.base_url = "https://api.firecrawl.dev/v1/crawl"
        self.max_pages = max_pages
        self.app = FirecrawlApp(api_key=self.api_key)

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

    def get_map(self):
        return self.app.map_url(self.url)
    
    def get_html_content(self,crawl_result=None):
        
        
        return [page.html for page in crawl_result.data if hasattr(page, 'html')]
      

    def store_crawl_result(self, crawl_result, filepath):
        for i, page in enumerate(crawl_result.data):
            if hasattr(page, 'html') and page.html:
                with open(f"{filepath}{i}.html", 'w', encoding='utf-8') as f:
                    f.write(page.html)