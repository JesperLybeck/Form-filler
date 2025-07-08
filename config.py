from pydantic import BaseModel
from typing import Optional

# Schema to fill with extracted data.
class business_data(BaseModel):
    name: Optional[str] = None
    orgNumber: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    postalCode: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    logo: Optional[str] = None
    coverImage: Optional[str] = None
    established: Optional[str] = None
    # socialMedia: dict usually problematic as it often produces unhashable types.

# Constant for easy access
BUSINESS_DATA_FIELDS = list(business_data.model_fields.keys())

# Firecrawl configuration
CRAWLER_MAX_PAGES = 3
CRAWLER_TIMEOUT = 30

# Chunker configuration
CHUNKER_MAX_CHUNK_SIZE = 18000  # Default chunk size, can be adjusted
CHUNKER_MIN_CHUNK_SIZE = 3000   # Minimum chunk size for DOM tree chunking

# Heuristic keywords for URL filtering
heuristic_keywords = [
    # High confidence — often contain business metadata
    "about", "om-oss", "kontakt", "contact", "company", "our-company",
    "who-we-are", "hvem-vi-er", "team", "our-team", "people", "staff",
    "organization", "orgnr", "organisasjonsnummer", "corporate", "overview",
    "profile", "firmainfo", "business", "business-info", "company-info",
    "information", "info", "identity", "established", "history", "our-story",

    # Secondary — often contain contact/address/branding details
    "kontakt-oss", "get-in-touch", "reach-us", "contact-us", "find-us",
    "location", "locations", "besøk", "visit", "address", "adresse",
    "headquarters", "hq", "kontor", "offices", "directions",

    # Branding/media — may contain logo, cover image
    "press", "media", "brand", "branding", "assets", "logos", "resources",

    # Legal/official — sometimes have org number or business info
    "terms", "legal", "privacy", "disclaimer", "imprint", "om-virksomheden",
    "regnskap", "report", "årsrapport", "accounting", "financials",

    # Misc fallbacks — very generic but potentially useful
    "faq", "help", "support", "services", "products"
]

# LLM Prompts
PROMPT_RELEVANT_URLS = """
Given this list of URLs {URL_list}, return the top {max_pages} URLs that are most likely to contain the following information:
{fields}

Return only a valid python list of URLs, without any additional text or explanation. Sort the list from most relevant to least relevant. No extra quotations, just a python list that can be used directly in my program.
"""

PROMPT_INFORMATION_EXTRACTION = """
Given the following website content, extract as much as possible of the following company information as JSON:
{fields}
---
{chunk}
---
Return only a single valid JSON object. Use double quotes for all keys and string values. Do not use single quotes. Do not include any text, markdown, or explanation before or after the JSON.
If no value for a field is found, write null as value.
"""