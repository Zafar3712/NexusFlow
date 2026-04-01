import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Use Gemini 3 Flash for high-speed agentic reasoning
model = genai.GenerativeModel('gemini-2.5-flash') 

def generate_and_execute_sql(user_query, schema_str, conn, retries=3):
    prompt = f"""
    You are an expert SQL assistant.
    Given the following schema:
    {schema_str}
    
    Write a DuckDB-compatible SQL query to answer this user request: "{user_query}"
    Return ONLY the raw SQL code. No markdown formatting, no explanations.
    """
    
    sql_query = "No SQL generated yet (API error)." 
    last_error = "No error recorded." # 1. Initialize our memory variable
    
    for attempt in range(retries):
        try:
            # Generate SQL
            response = model.generate_content(prompt)
            sql_query = response.text.strip().replace('```sql', '').replace('```', '')
            
            # Execute SQL (Layer 3)
            result_df = conn.execute(sql_query).df()
            return result_df, sql_query
            
        except Exception as e:
            last_error = str(e) # 2. Save the error message as a string!
            
            # Iterative Self-Correction Loop
            prompt = f"""
            The previous attempt failed.
            Original query intent: {user_query}
            Failed SQL: {sql_query}
            Error message: {last_error}
            
            Fix the SQL query and return ONLY the raw, corrected DuckDB SQL code.
            """
    
    # 3. Use our saved string instead of 'e'
    return None, f"Failed after {retries} attempts.\nLast SQL tried: {sql_query}\nLast Error: {last_error}"