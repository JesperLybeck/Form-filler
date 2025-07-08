# Form Filler - Business Data Extraction API

A FastAPI-based service that automatically extracts business information from company websites using AI-powered web crawling and data extraction.

## Key concepts

- **Web Crawling**: uses a customized scraping logic based on firecrawls /scrape and /map endpoints.
- **AI Extraction**: Uses gpt-4o-mini to extract structured business data
- **Structured Output**: Returns clean, standardized business information
- **RESTful API**: Easy-to-use HTTP endpoints
- **Concurrent scraping and extraction**: based on producer-consumer pattern with asyncio and threading for efficient data processing.
- **Easy configuration**: add fields and keywords in the configuration file.

## Extracted Data Fields are provided as a pydantic basemodel

### Prerequisites

- Python 3.11 or higher
- Firecrawl API key
- GPT-4o-Mini API key

### Installation

1. **Clone the repository**
 

2. **Install dependencies**

3. **Set up environment variables**

4. **Start the server**

5. **Open the API documentation**
   ```
   http://127.0.0.1:8000/docs
   ```

## Configuration

Create a `.env` file with your API keys:

```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
LLM_API_KEY=your_gpt-4o-mini_api_key_here
```

## API Usage

### Single endpoint: /extract_data that takes a URL and returns structured business data.

## Architecture
