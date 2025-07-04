"""
Prompt template builder for text-to-SQL conversion tasks.
"""

def build_prompt(schema: str, user_query: str) -> str:
    """
    Build a prompt for the AI model to convert natural language to SQL, given a schema and user query.
    """
    return f"""
You are an AI assistant that converts natural language into SQL.

Here is the database schema:
{schema}

User Query:
{user_query}

Respond with only the SQL query.
"""
