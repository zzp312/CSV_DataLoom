from typing import List, Dict, Any, Optional
import sqlglot

class SQLGenerator:
    @staticmethod
    def generate_select(
        tables: List[str],
        columns: List[Dict[str, str]] = None,
        joins: List[Dict[str, Any]] = None,
        where_clause: str = None,
        order_by: List[Dict[str, str]] = None,
        limit: int = None,
        offset: int = None
    ) -> str:
        if not tables:
            return ""
        
        if columns is None:
            columns = []
        
        if joins is None:
            joins = []
        
        sql_parts = ["SELECT"]
        
        if columns:
            selected_cols = []
            for col in columns:
                table_alias = col.get('table_alias', col['table'])
                selected_cols.append(f"{table_alias}.{col['column']}")
            sql_parts.append(", ".join(selected_cols))
        else:
            sql_parts.append("*")
        
        sql_parts.append(f"FROM {tables[0]}")
        
        if len(tables) > 1:
            for i, table in enumerate(tables[1:], 1):
                sql_parts.append(f", {table}")
        
        for join in joins:
            join_type = join.get('type', 'INNER').upper()
            left_table = join['left_table']
            left_col = join['left_column']
            right_table = join['right_table']
            right_col = join['right_column']
            
            sql_parts.append(f"{join_type} JOIN {right_table}")
            sql_parts.append(f"ON {left_table}.{left_col} = {right_table}.{right_col}")
        
        if where_clause:
            sql_parts.append(f"WHERE {where_clause}")
        
        if order_by:
            order_parts = []
            for order in order_by:
                direction = order.get('direction', 'ASC').upper()
                order_parts.append(f"{order['column']} {direction}")
            sql_parts.append(f"ORDER BY {', '.join(order_parts)}")
        
        if limit:
            sql_parts.append(f"LIMIT {limit}")
        
        if offset:
            sql_parts.append(f"OFFSET {offset}")
        
        return " ".join(sql_parts)
    
    @staticmethod
    def generate_create_table(table_name: str, columns: List[Dict[str, str]]) -> str:
        col_defs = []
        for col in columns:
            col_name = col['name']
            data_type = col.get('type', 'VARCHAR')
            col_defs.append(f"{col_name} {data_type}")
        
        return f"CREATE TABLE {table_name} ({', '.join(col_defs)})"
    
    @staticmethod
    def generate_drop_table(table_name: str) -> str:
        return f"DROP TABLE IF EXISTS {table_name}"
    
    @staticmethod
    def generate_insert(table_name: str, columns: List[str], values: List[List[Any]]) -> str:
        if not values:
            return ""
        
        col_str = ", ".join(columns)
        
        value_rows = []
        for row in values:
            row_values = []
            for val in row:
                if val is None:
                    row_values.append("NULL")
                elif isinstance(val, str):
                    escaped = val.replace("'", "''")
                    row_values.append(f"'{escaped}'")
                else:
                    row_values.append(str(val))
            value_rows.append(f"({', '.join(row_values)})")
        
        values_str = ", ".join(value_rows)
        
        return f"INSERT INTO {table_name} ({col_str}) VALUES {values_str}"
    
    @staticmethod
    def infer_sql_type(python_type: str) -> str:
        python_type = python_type.lower()
        
        if 'int' in python_type:
            return "INT"
        elif 'float' in python_type or 'double' in python_type or 'decimal' in python_type:
            return "DECIMAL(18, 4)"
        elif 'datetime' in python_type or 'date' in python_type:
            return "DATETIME"
        elif 'bool' in python_type:
            return "BOOLEAN"
        else:
            return "VARCHAR(255)"
    
    @staticmethod
    def parse_sql(sql: str) -> Optional[Dict[str, Any]]:
        try:
            parsed = sqlglot.parse_one(sql)
            
            result = {
                'type': parsed.args.get('this').__class__.__name__ if hasattr(parsed, 'args') else 'Unknown',
                'tables': [],
                'columns': [],
                'joins': [],
                'where': None,
                'order_by': [],
                'limit': None,
                'offset': None
            }
            
            return result
        except Exception:
            return None
    
    @staticmethod
    def format_sql(sql: str) -> str:
        try:
            parsed = sqlglot.parse_one(sql)
            return parsed.sql(dialect='duckdb', pretty=True)
        except Exception:
            return sql


def generate_create_table(table_name: str, df) -> str:
    columns = []
    for col_name, dtype in df.dtypes.items():
        columns.append({'name': col_name, 'type': SQLGenerator.infer_sql_type(str(dtype))})
    return SQLGenerator.generate_create_table(table_name, columns)


def generate_insert_statements(table_name: str, df, batch_size: int = 100) -> str:
    columns = df.columns.tolist()
    values = df.values.tolist()
    
    statements = []
    for i in range(0, len(values), batch_size):
        batch = values[i:i+batch_size]
        statements.append(SQLGenerator.generate_insert(table_name, columns, batch))
    
    return "\n".join(statements)

