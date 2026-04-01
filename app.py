import streamlit as st
import pandas as pd
from database import setup_database, get_schema
from agent import generate_and_execute_sql, model

# Initialize Database
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = setup_database()
    st.session_state.schema = get_schema(st.session_state.db_conn)

st.title("NexusFlow: Intent-Based Data Exploration")
st.write("Ask questions about your data in plain English.")

user_input = st.text_input("What would you like to know?")

if user_input:
    with st.spinner("Translating intent to logic..."):
        # Synthesize and execute SQL
        df, sql = generate_and_execute_sql(user_input, st.session_state.schema, st.session_state.db_conn)
        
        if df is not None:
            st.success("Data Retrieved Successfully!")
            with st.expander("View Generated SQL"):
                st.code(sql, language='sql')
                
            st.write("Data Preview:", df.head())
            
            # Synthesize UI / Plotly Code (Layer 4)
            with st.spinner("Generating Interface..."):
                data_shape = f"Columns: {list(df.columns)}, Data Types: {df.dtypes.to_dict()}"
                ui_prompt = f"""
                You are a UI generation agent.
                I have a pandas dataframe named 'df' with the following shape: {data_shape}.
                Write Python code using Plotly to create the most appropriate visualization for this data.
                Assign the plotly figure to a variable named 'fig'.
                Return ONLY the raw Python code. No markdown, no explanations.
                """
                
                ui_response = model.generate_content(ui_prompt)
                code_to_exec = ui_response.text.strip().replace('```python', '').replace('```', '')
                
                try:
                    # Execute the generated UI code
                    local_vars = {'df': df}
                    exec(code_to_exec, globals(), local_vars)
                    
                    if 'fig' in local_vars:
                        st.plotly_chart(local_vars['fig'])
                except Exception as e:
                    st.error(f"Failed to render Generative UI: {e}")
        else:
            st.error(sql) # Displays the failure message