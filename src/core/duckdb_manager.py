import duckdb
import pandas as pd
from typing import List, Dict, Any, Optional
import os

class DuckDBManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DuckDBManager, cls).__new__(cls)
            cls._instance._init_connection()
        return cls._instance
    
    def _init_connection(self):
        self.conn = duckdb.connect(database=':memory:', read_only=False)
        self.conn.execute("SET enable_progress_bar = false")
    
    def execute_query(self, query: str) -> Any:
        try:
            result = self.conn.execute(query)
            return result
        except Exception as e:
            raise RuntimeError(f"SQL execution error: {str(e)}")
    
    def fetch_df(self, query: str) -> pd.DataFrame:
        result = self.execute_query(query)
        return result.fetch_df()
    
    def fetch_one(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            result = self.execute_query(query)
            if result is None:
                return None
            row = result.fetchone()
            if row is None:
                return None
            if result.description is None:
                return None
            columns = [desc[0] for desc in result.description]
            return dict(zip(columns, row))
        except Exception as e:
            print(f"fetch_one error: {str(e)}")
            return None
    
    def fetch_all(self, query: str) -> List[Dict[str, Any]]:
        try:
            result = self.execute_query(query)
            if result is None:
                return []
            rows = result.fetchall()
            if result.description is None:
                return []
            columns = [desc[0] for desc in result.description]
            return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"fetch_all error: {str(e)}")
            return []
    
    def import_csv(self, file_path: str, table_name: str, header_row: int = 0, skip_rows: int = 0) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            
            df = pd.read_csv(file_path, header=header_row, skiprows=skip_rows if skip_rows > 0 else None, dtype=str)
            self.conn.register(table_name + '_temp', df)
            
            columns = df.columns.tolist()
            cast_columns = [f"CAST(`{col}` AS VARCHAR) AS `{col}`" for col in columns]
            self.execute_query(f"CREATE TABLE {table_name} AS SELECT {', '.join(cast_columns)} FROM {table_name}_temp")
            self.execute_query(f"DROP VIEW IF EXISTS {table_name}_temp")
        except Exception as e:
            raise RuntimeError(f"CSV import failed: {str(e)}")
    
    def import_excel(self, file_path: str, sheet_name: str, table_name: str, header_row: int = 0, skip_rows: int = 0) -> None:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            self.execute_query(f"DROP TABLE IF EXISTS {table_name}")
            
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row, skiprows=skip_rows, dtype=str)
            self.conn.register(table_name + '_temp', df)
            
            columns = df.columns.tolist()
            cast_columns = [f"CAST(`{col}` AS VARCHAR) AS `{col}`" for col in columns]
            self.execute_query(f"CREATE TABLE {table_name} AS SELECT {', '.join(cast_columns)} FROM {table_name}_temp")
            self.execute_query(f"DROP VIEW IF EXISTS {table_name}_temp")
        except Exception as e:
            raise RuntimeError(f"Excel import failed: {str(e)}")
    
    def get_tables(self) -> List[str]:
        query = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'"
        result = self.fetch_all(query)
        unique_tables = list(dict.fromkeys([row['table_name'] for row in result]))
        return unique_tables
    
    def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        query = f"PRAGMA table_info('{table_name}')"
        result = self.fetch_all(query)
        return [{'column_name': row['name'], 'data_type': row['type']} for row in result]
    
    def rename_table(self, old_name: str, new_name: str) -> None:
        query = f"ALTER TABLE {old_name} RENAME TO {new_name}"
        self.execute_query(query)
    
    def drop_table(self, table_name: str) -> None:
        query = f'DROP TABLE IF EXISTS "{table_name}"'
        self.execute_query(query)
    
    def table_exists(self, table_name: str) -> bool:
        query = f"SELECT COUNT(*) as count FROM information_schema.tables WHERE table_name = '{table_name}'"
        result = self.fetch_one(query)
        return result['count'] > 0
    
    def get_row_count(self, table_name: str) -> int:
        query = f'SELECT COUNT(*) as count FROM "{table_name}"'
        result = self.fetch_one(query)
        return result['count'] if result is not None else 0
    
    def save_df(self, df: pd.DataFrame, table_name: str) -> None:
        try:
            self.execute_query(f'DROP TABLE IF EXISTS "{table_name}"')
            
            columns = df.columns.tolist()
            cast_columns = [f'CAST("{col}" AS VARCHAR) AS "{col}"' for col in columns]
            
            self.conn.register(table_name + '_temp', df)
            self.execute_query(f'CREATE TABLE "{table_name}" AS SELECT {", ".join(cast_columns)} FROM {table_name}_temp')
            self.conn.unregister(table_name + '_temp')
        except Exception as e:
            raise RuntimeError(f"Failed to save DataFrame: {str(e)}")
    
    def close(self):
        if self.conn:
            self.conn.close()
            DuckDBManager._instance = None

