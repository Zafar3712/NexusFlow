import duckdb
import pandas as pd

def setup_database():
    # Initialize DuckDB in-memory for testing (Layer 3)
    conn = duckdb.connect(database=':memory:')
    
    # Create some dummy data to query
    data = {
        'date': pd.date_range(start='2023-01-01', periods=5, freq='ME'),
        'sales': [250, 300, 150, 400, 350],
        'region': ['North', 'South', 'North', 'East', 'West']
    }
    df = pd.DataFrame(data)
    
    # Register the dataframe as a table
    conn.register('sales_data', df)
    return conn

def get_schema(conn):
    # Retrieve Relational Metadata (Layer 1)
    schema_query = "SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema='main';"
    schema_df = conn.execute(schema_query).df()
    
    # Format into a string for the LLM
    schema_str = "Database Schema:\n"
    for _, row in schema_df.iterrows():
        schema_str += f"- Table: {row['table_name']}, Column: {row['column_name']}, Type: {row['data_type']}\n"
    return schema_str