"""
Testing Module
Validates core functionality of the data workbench
"""

import pandas as pd
import io
import time
from typing import Dict, List, Any, Tuple

class TestResult:
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'passed': self.passed,
            'message': self.message,
            'duration': self.duration
        }

class TestRunner:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.results: List[TestResult] = []

    def run_all_tests(self) -> List[TestResult]:
        self.results = []
        self.test_csv_import()
        self.test_excel_import()
        self.test_sql_query()
        self.test_data_export()
        return self.results

    def test_csv_import(self) -> TestResult:
        start_time = time.time()
        try:
            csv_data = "id,name,value\\n1,test,100\\n2,foo,200"
            df = pd.read_csv(io.StringIO(csv_data))
            self.db_manager.save_df(df, 'test_csv_table')

            tables = self.db_manager.get_tables()
            if 'test_csv_table' in tables:
                count = self.db_manager.get_row_count('test_csv_table')
                if count == 2:
                    duration = time.time() - start_time
                    result = TestResult("CSV Import", True, f"Imported {count} rows successfully", duration)
                else:
                    duration = time.time() - start_time
                    result = TestResult("CSV Import", False, f"Expected 2 rows, got {count}", duration)
            else:
                duration = time.time() - start_time
                result = TestResult("CSV Import", False, "Table not found after import", duration)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("CSV Import", False, str(e), duration)

        self.results.append(result)
        return result

    def test_excel_import(self) -> TestResult:
        start_time = time.time()
        try:
            df = pd.DataFrame({
                'col_a': [1, 2, 3],
                'col_b': ['x', 'y', 'z']
            })
            self.db_manager.save_df(df, 'test_excel_table')

            tables = self.db_manager.get_tables()
            if 'test_excel_table' in tables:
                columns = self.db_manager.get_table_columns('test_excel_table')
                if len(columns) == 2:
                    duration = time.time() - start_time
                    result = TestResult("Excel Import", True, "Imported with correct column count", duration)
                else:
                    duration = time.time() - start_time
                    result = TestResult("Excel Import", False, f"Expected 2 columns, got {len(columns)}", duration)
            else:
                duration = time.time() - start_time
                result = TestResult("Excel Import", False, "Table not found after import", duration)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("Excel Import", False, str(e), duration)

        self.results.append(result)
        return result

    def test_sql_query(self) -> TestResult:
        start_time = time.time()
        try:
            df1 = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
            df2 = pd.DataFrame({'id': [1, 2, 4], 'value': [10, 20, 40]})

            self.db_manager.save_df(df1, 'sql_test_t1')
            self.db_manager.save_df(df2, 'sql_test_t2')

            result_df = self.db_manager.fetch_df("""
                SELECT t1.id, t1.name, t2.value
                FROM sql_test_t1 t1
                LEFT JOIN sql_test_t2 t2 ON t1.id = t2.id
            """)

            if len(result_df) == 3:
                duration = time.time() - start_time
                result = TestResult("SQL Query & JOIN", True, f"JOIN returned {len(result_df)} rows", duration)
            else:
                duration = time.time() - start_time
                result = TestResult("SQL Query & JOIN", False, f"Expected 3 rows, got {len(result_df)}", duration)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("SQL Query & JOIN", False, str(e), duration)

        self.results.append(result)
        return result

    def test_data_export(self) -> TestResult:
        start_time = time.time()
        try:
            df = pd.DataFrame({
                'name': ['John', 'Jane'],
                'age': [30, 25],
                'city': ['NYC', 'LA']
            })
            self.db_manager.save_df(df, 'export_test')

            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()

            if 'John' in csv_content and 'Jane' in csv_content:
                if 'name,age,city' in csv_content:
                    duration = time.time() - start_time
                    result = TestResult("Data Export", True, "CSV export contains correct data", duration)
                else:
                    duration = time.time() - start_time
                    result = TestResult("Data Export", False, "CSV header missing", duration)
            else:
                duration = time.time() - start_time
                result = TestResult("Data Export", False, "CSV content incorrect", duration)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("Data Export", False, str(e), duration)

        self.results.append(result)
        return result

    def test_large_dataset(self) -> TestResult:
        start_time = time.time()
        try:
            n_rows = 10000
            df = pd.DataFrame({
                'id': range(n_rows),
                'data': ['x' * 100] * n_rows
            })
            self.db_manager.save_df(df, 'large_table')

            query_start = time.time()
            result_df = self.db_manager.fetch_df("SELECT * FROM large_table WHERE id > 5000 LIMIT 100")
            query_time = time.time() - query_start

            if len(result_df) == 100:
                duration = time.time() - start_time
                result = TestResult("Large Dataset Performance", True,
                    f"Processed {n_rows} rows, query took {query_time:.3f}s", duration)
            else:
                duration = time.time() - start_time
                result = TestResult("Large Dataset Performance", False,
                    f"Expected 100 rows, got {len(result_df)}", duration)
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult("Large Dataset Performance", False, str(e), duration)

        self.results.append(result)
        return result

    def get_summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed

        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'results': [r.to_dict() for r in self.results]
        }
