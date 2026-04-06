import duckdb
import pandas as pd
import os

def setup_database():
    return duckdb.connect(database=':memory:')

def load_uploaded_file(conn, uploaded_file):
    """Saves the uploaded file, loads it into DuckDB, and returns dataset health stats."""
    file_extension = uploaded_file.name.split('.')[-1]
    temp_path = f"temp_dataset.{file_extension}"
    
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    conn.execute("DROP TABLE IF EXISTS user_data;")
    
    if file_extension == 'csv':
        conn.execute(f"CREATE TABLE user_data AS SELECT * FROM read_csv_auto('{temp_path}');")
    elif file_extension == 'parquet':
        conn.execute(f"CREATE TABLE user_data AS SELECT * FROM read_parquet('{temp_path}');")
        
    os.remove(temp_path)
    
    # NEW: Data Profiling for System Trust
    row_count = conn.execute("SELECT COUNT(*) FROM user_data;").fetchone()[0]
    col_count = len(conn.execute("DESCRIBE user_data;").fetchall())
    
    return {
        "table": "user_data",
        "rows": f"{row_count:,}",
        "cols": col_count,
        "filename": uploaded_file.name
    }

def get_schema(conn):
    try:
        schema_query = "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='main';"
        schema_df = conn.execute(schema_query).df()
        
        if schema_df.empty:
            return "No schema available."
            
        schema_str = "Database Schema:\n"
        for _, row in schema_df.iterrows():
            schema_str += f"- Table: {row['table_name']}, Column: {row['column_name']}, Type: {row['data_type']}\n"
        return schema_str
    except Exception as e:
        return f"Error retrieving schema: {e}"

def get_ui_schema(conn):
    try:
        schema_query = "SELECT column_name, data_type FROM information_schema.columns WHERE table_schema='main';"
        df = conn.execute(schema_query).df()
        
        if df.empty:
            return None
            
        md_schema = ""
        for _, row in df.iterrows():
            md_schema += f"- **`{row['column_name']}`** : *{row['data_type']}*\n"
        return md_schema
    except Exception:
        return None