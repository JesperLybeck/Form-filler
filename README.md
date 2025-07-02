# 🏢 Form Filler - Business Data Extraction API

A FastAPI-based service that automatically extracts business information from company websites using AI-powered web crawling and data extraction.

## ✨ Features

- 🌐 **Web Crawling**: Automatically crawls company websites using Firecrawl
- 🤖 **AI Extraction**: Uses Google Gemini to extract structured business data
- 📊 **Structured Output**: Returns clean, standardized business information
- 🔧 **RESTful API**: Easy-to-use HTTP endpoints
- ⚡ **Fast Processing**: Optimized for quick data extraction

## 📋 Extracted Data Fields

- Company name and type
- Contact information (phone, email, address)
- Website and social media links
- Business description
- Organization details
- Logo and cover images

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Firecrawl API key
- Google Gemini API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/formfiller.git
   cd formfiller
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Start the server**
   ```bash
   python -m uvicorn main_api:app --reload
   ```

5. **Open the API documentation**
   ```
   http://127.0.0.1:8000/docs
   ```

## 🔧 Configuration

Create a `.env` file with your API keys:

```env
FIRECRAWL_API_KEY=your_firecrawl_api_key_here
GOOGLE_API_KEY=your_google_gemini_api_key_here
LLM_API_KEY=your_google_gemini_api_key_here
```

## 📖 API Usage

### 1. Initialize the Pipeline
```http
POST /initialize_extraction_pipeline
```

### 2. Set Target URL
```http
POST /setURL?url=https://company-website.com
```

### 3. Start Extraction
```http
POST /start_extraction
```

### 4. Get Results
```http
GET /get_fields
```

## 🏗️ Architecture

```
User Request → FastAPI → Firecrawl → HTML Processing → Gemini AI → Structured Data
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🔗 Links

- [Firecrawl API](https://firecrawl.dev/)
- [Google Gemini](https://ai.google.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
