
def build_prompt(schema: str, user_query: str) -> str:
    return f"""
You are an AI assistant that converts natural language into SQL.

Here is the database schema:
{schema}

User Query:
{user_query}

Respond with only the SQL query.
"""
