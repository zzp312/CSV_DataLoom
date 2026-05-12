import flet as ft
import pandas as pd
from typing import Callable, List, Dict, Any
from src.utils.sql_generator import SQLGenerator
import io
import csv

@ft.control
class RightPanel(ft.Column):
    def __init__(self):
        super().__init__()
        self.data_table = None
        self.status_text = None
        self.export_csv_btn = None
        self.export_sql_btn = None
        self.current_df = None
        self.total_rows = 0
        self.execution_time = 0.0
        self.page_size = 50
        self.current_page = 1
        self._build_content()
    
    def _build_content(self):
        self.status_text = ft.Text(
            "Total 0 rows, Time 0.00 sec",
            size=12,
            color=ft.Colors.GREY_500
        )
        
        self.data_table = ft.DataTable(
            columns=[ft.DataColumn(ft.Text(""))],
            rows=[],
            column_spacing=10,
            expand=True
        )
        
        data_table_container = ft.Container(
            content=ft.ListView(
                controls=[self.data_table],
                expand=True
            ),
            expand=True,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            padding=10
        )
        
        self.export_csv_btn = ft.Button("Export CSV",
            icon="download_file",
            on_click=self._on_export_csv,
            bgcolor=ft.Colors.GREEN_500,
            color=ft.Colors.WHITE
        )
        
        self.export_sql_btn = ft.Button("Export SQL",
            icon="code",
            on_click=self._on_export_sql,
            bgcolor=ft.Colors.ORANGE_500,
            color=ft.Colors.WHITE
        )
        
        export_panel = ft.Row(
            controls=[self.export_csv_btn, self.export_sql_btn],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        self.controls = [
            ft.Row(
                controls=[
                    ft.Text("Result Preview", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
                    self.status_text
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            ),
            ft.Divider(height=1),
            data_table_container,
            ft.Divider(height=1),
            export_panel
        ]
        self.expand = True
    
    def display_result(self, df: pd.DataFrame, execution_time: float):
        self.current_df = df
        self.total_rows = len(df)
        self.execution_time = execution_time
        
        self.status_text.value = f"Total {self.total_rows:,} rows, Time {self.execution_time:.2f} sec"
        
        if df.empty:
            self.data_table.columns = []
            self.data_table.rows = []
            self.update()
            return
        
        self.data_table.columns = [
            ft.DataColumn(ft.Text(col, size=12, weight=ft.FontWeight.BOLD))
            for col in df.columns
        ]
        
        display_rows = min(100, len(df))
        self.data_table.rows = []
        
        for _, row in df.head(display_rows).iterrows():
            cells = []
            for col in df.columns:
                cell_value = row[col]
                if pd.isna(cell_value):
                    cell_value = ""
                cells.append(ft.DataCell(ft.Text(str(cell_value), size=11)))
            self.data_table.rows.append(ft.DataRow(cells=cells))
        
        self.update()
    
    def _on_export_csv(self, e):
        if self.current_df is None or self.current_df.empty:
            return
        
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(self.current_df.columns)
        for _, row in self.current_df.iterrows():
            writer.writerow(row.values)
        
        csv_content = output.getvalue()
        
        e.page.download(
            ft.BytesIO(csv_content.encode('utf-8-sig')),
            "result.csv"
        )
    
    def _on_export_sql(self, e):
        if self.current_df is None or self.current_df.empty:
            return
        
        columns = []
        for col in self.current_df.columns:
            sample_values = self.current_df[col].dropna().head(10)
            inferred_type = "VARCHAR(255)"
            
            if len(sample_values) > 0:
                first_val = sample_values.iloc[0]
                inferred_type = SQLGenerator.infer_sql_type(type(first_val).__name__)
            
            columns.append({'name': col, 'type': inferred_type})
        
        table_name = "exported_data"
        drop_sql = SQLGenerator.generate_drop_table(table_name)
        create_sql = SQLGenerator.generate_create_table(table_name, columns)
        
        sample_size = min(1000, len(self.current_df))
        sample_df = self.current_df.head(sample_size)
        insert_sql = SQLGenerator.generate_insert(
            table_name,
            list(sample_df.columns),
            sample_df.values.tolist()
        )
        
        sql_content = f"{drop_sql};\n\n{create_sql};\n\n{insert_sql};"
        
        e.page.download(
            ft.BytesIO(sql_content.encode('utf-8')),
            "exported_data.sql"
        )
