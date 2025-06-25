# Text to SQL FastAPI Service

A FastAPI service that converts natural language queries to SQL using Google's Gemini model and Agno AI framework.

## Requirements

- Python 3.8+
- FastAPI
- Agno AI
- Google Generative AI
- SQLAlchemy

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your Google API key:
```
GOOGLE_API_KEY=your_google_api_key_here
```

## Running the Service

Start the FastAPI server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Usage

### Convert Natural Language to SQL

**Endpoint:** `POST /query`

**Request Body:**
```json
{
    "db_url": "your_database_connection_string",
    "query": "your natural language query"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/query" \
     -H "Content-Type: application/json" \
     -d '{"db_url": "postgresql://user:pass@localhost/db", "query": "Find all users who joined last month"}'
```

## Features

- Natural language to SQL conversion using Google's Gemini model
- Automatic schema inspection
- Safe query execution
- Clear explanations of generated queries
- Support for multiple database types through SQLAlchemy 