from pydantic import BaseModel

#Schema to fill with extracted data.
class business_data(BaseModel):
    name: str
    orgNumber: str
    type : str
    description: str
    website: str
    phone : str
    email: str
    address: str
    postalCode: str
    city: str
    country: str
    logo: str
    coverImage: str
    established: str
    socialMedia: dict



# Constant for easy access
BUSINESS_DATA_FIELDS = list(business_data.model_fields.keys())

#firecrawl configuration
CRAWLER_MAX_PAGES=4
CRAWLER_TIMEOUT=30


#chunker configuration
CHUNKER_MAX_CHUNK_SIZE=18000  # Default chunk size, can be adjusted
CHUNKER_MIN_CHUNK_SIZE=3000  # Minimum chunk size for DOM tree chunking



