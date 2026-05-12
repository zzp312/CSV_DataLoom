import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.core.duckdb_manager import DuckDBManager
import pandas as pd

# 创建测试数据
print("=== Testing DuckDB API ===")

db = DuckDBManager()

# 测试1: 创建一个简单表
print("\n1. Creating test table...")
df = pd.DataFrame({
    'id': [1, 2, 3, 4],
    'name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'email': ['alice@example.com', 'bob@example.com', 'charlie@example.com', 'diana@example.com'],
    'age': [25, 30, 35, 28]
})
db.save_df(df, 'test_data')
print("   OK: Table created")

# 测试2: 获取表列表
print("\n2. Getting table list...")
tables = db.get_tables()
print(f"   OK: Tables: {tables}")

# 测试3: 获取表结构
print("\n3. Getting table columns...")
try:
    columns = db.get_table_columns('test_data')
    print(f"   OK: Columns: {columns}")
except Exception as e:
    print(f"   ERROR: {e}")

# 测试4: 获取行数
print("\n4. Getting row count...")
try:
    rows = db.get_row_count('test_data')
    print(f"   OK: Row count: {rows}")
except Exception as e:
    print(f"   ERROR: {e}")

# 测试5: 测试查询
print("\n5. Testing query...")
try:
    result = db.fetch_one("SELECT COUNT(*) as count FROM test_data")
    print(f"   OK: Query result: {result}")
except Exception as e:
    print(f"   ERROR: {e}")

print("\n=== Test Complete ===")
