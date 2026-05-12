import streamlit as st
import pandas as pd
import duckdb
import os
import io
import time
from src.core.duckdb_manager import DuckDBManager

st.set_page_config(
    page_title="Local Data Dual-Mode Workbench",
    page_icon="📊",
    layout="wide"
)

db_manager = DuckDBManager()

st.sidebar.title("📁 Import Data")
uploaded_file = st.sidebar.file_uploader("Choose CSV/Excel file", type=["csv", "xlsx", "xls"])

if uploaded_file is not None:
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    
    if file_ext == '.csv':
        st.sidebar.subheader("CSV Import Settings")
        table_name = st.sidebar.text_input("Table Name", value=os.path.splitext(uploaded_file.name)[0])
        header_row = st.sidebar.number_input("Header Row (0-based)", min_value=0, value=0)
        content_row = st.sidebar.number_input("Content Start Row", min_value=1, value=1)
        
        if st.sidebar.button("Import CSV"):
            try:
                skip_rows = content_row - (header_row + 1)
                if skip_rows < 0:
                    skip_rows = 0
                
                df = pd.read_csv(uploaded_file, header=header_row, skiprows=skip_rows if skip_rows > 0 else None)
                db_manager.save_df(df, table_name)
                
                st.sidebar.success(f"CSV imported successfully: {table_name}")
            except Exception as e:
                st.sidebar.error(f"Import failed: {str(e)}")
    
    elif file_ext in ['.xlsx', '.xls']:
        try:
            xls = pd.ExcelFile(uploaded_file)
            sheet_names = xls.sheet_names
            
            st.sidebar.subheader("Excel Import Settings")
            selected_sheets = st.sidebar.multiselect("Select sheets to import", sheet_names, default=sheet_names)
            
            if st.sidebar.button("Import Excel"):
                try:
                    for sheet_name in selected_sheets:
                        df = pd.read_excel(xls, sheet_name=sheet_name)
                        table_name = sheet_name.lower().replace(' ', '_')
                        db_manager.save_df(df, table_name)
                    
                    st.sidebar.success("Excel file imported successfully")
                except Exception as e:
                    st.sidebar.error(f"Import failed: {str(e)}")
        except Exception as e:
            st.sidebar.error(f"Failed to read Excel: {str(e)}")

st.sidebar.divider()
st.sidebar.title("📋 Data Assets")
tables = db_manager.get_tables()

if tables:
    selected_table = st.sidebar.selectbox("Select a table", tables)
    
    if selected_table:
        columns = db_manager.get_table_columns(selected_table)
        row_count = db_manager.get_row_count(selected_table)
        
        st.sidebar.write(f"**Rows:** {row_count}")
        st.sidebar.write("**Columns:**")
        for col in columns:
            st.sidebar.write(f"- {col['column_name']}: {col['data_type']}")
        
        if st.sidebar.button("Generate SELECT *"):
            st.session_state['sql'] = f"SELECT * FROM {selected_table}"
else:
    st.sidebar.info("No tables found. Import a file first.")

col1, col2 = st.columns([1.5, 1])

with col1:
    st.title("SQL Editor")
    sql = st.text_area("Enter SQL query", value=st.session_state.get('sql', ''), height=200)
    
    if st.button("▶️ Run"):
        if sql.strip():
            try:
                start_time = time.time()
                df = db_manager.fetch_df(sql)
                execution_time = time.time() - start_time
                
                st.session_state['result'] = df
                st.session_state['execution_time'] = execution_time
                st.session_state['row_count'] = len(df)
            except Exception as e:
                st.error(f"Execution error: {str(e)}")

with col2:
    st.title("Results")
    
    if 'result' in st.session_state:
        df = st.session_state['result']
        row_count = st.session_state['row_count']
        execution_time = st.session_state['execution_time']
        
        st.write(f"**Rows:** {row_count} | **Time:** {execution_time:.2f} seconds")
        
        st.dataframe(df.head(100), use_container_width=True)
        
        st.subheader("Export")
        export_format = st.selectbox("Format", ["CSV", "SQL Script"])
        
        if export_format == "CSV":
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode()
            
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="result.csv",
                mime="text/csv"
            )
        
        elif export_format == "SQL Script":
            from src.utils.sql_generator import generate_create_table, generate_insert_statements
            
            create_sql = generate_create_table("exported_table", df)
            insert_sql = generate_insert_statements("exported_table", df, batch_size=100)
            
            sql_script = f"{create_sql}\n\n{insert_sql}"
            
            st.download_button(
                "Download SQL Script",
                data=sql_script,
                file_name="result.sql",
                mime="text/plain"
            )
    else:
        st.info("Run a query to see results")