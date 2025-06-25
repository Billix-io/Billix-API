# FastAPI Project Setup

## Requirements
- Python 3.7+
- pip (Python package installer)

## Installation

1. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
.\venv\Scripts\activate  # On Windows
```

2. Install the requirements:
```bash
pip install -r requirements.txt
```

## Running the Application

To run the FastAPI application:
```bash
uvicorn main:app --reload
```

The application will be available at `http://127.0.0.1:8000`

Interactive API documentation will be available at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc` 