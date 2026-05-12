import flet as ft
from src.core.duckdb_manager import DuckDBManager
from typing import Callable, List
import os

@ft.control
class LeftPanel(ft.Column):
    def __init__(self, on_table_select: Callable = None, on_file_select: Callable = None):
        super().__init__()
        self.db_manager = DuckDBManager()
        self.on_table_select = on_table_select
        self.on_file_select = on_file_select
        self.table_list = ft.ListView(expand=True, spacing=2)
        self._build_content()
    
    def _build_content(self):
        self.controls = [
            ft.Text("Import Data", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
            ft.Button(
                "Browse Files",
                icon="folder_open",
                on_click=self._on_browse_click,
                width=280,
                bgcolor=ft.Colors.BLUE_500,
                color=ft.Colors.WHITE
            ),
            ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Icon("cloud_upload", size=24, color=ft.Colors.BLUE_400),
                        ft.Text("Or drop files here", size=10, text_align=ft.TextAlign.CENTER),
                        ft.Text(".csv .xlsx .xls", size=9, color=ft.Colors.GREY_400, text_align=ft.TextAlign.CENTER)
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    height=80
                ),
                border=ft.Border.all(2, ft.Colors.BLUE_200),
                border_radius=8,
                padding=10,
                margin=ft.Margin(0, 10, 0, 10)
            ),
            ft.Divider(height=1),
            ft.Text("Data Assets", style=ft.TextStyle(weight=ft.FontWeight.BOLD)),
            self.table_list
        ]
        self.expand = True
    
    def _on_browse_click(self, e):
        if self.on_file_select:
            self.on_file_select()
    
    def update_table_list(self):
        tables = self.db_manager.get_tables()
        self.table_list.controls.clear()
        
        for table_name in tables:
            columns = self.db_manager.get_table_columns(table_name)
            row_count = self.db_manager.get_row_count(table_name)
            
            children = []
            for col in columns:
                type_icon = self._get_type_icon(col['data_type'])
                children.append(
                    ft.ListTile(
                        leading=ft.Text(type_icon, size=14),
                        title=ft.Text(col['column_name'], size=12),
                        trailing=ft.Text(col['data_type'], size=10, color=ft.Colors.GREY_500)
                    )
                )
            
            expand_tile = ft.ExpansionTile(
                title=ft.Row(
                    controls=[
                        ft.Icon("table_chart", size=16),
                        ft.Text(table_name, size=14, weight=ft.FontWeight.MEDIUM),
                        ft.Text(f"({row_count} rows)", size=10, color=ft.Colors.GREY_500)
                    ]
                ),
                controls=children,
                on_expansion_change=lambda e, tn=table_name: self._on_table_click(tn)
            )
            
            self.table_list.controls.append(expand_tile)
        
        self.update()
    
    def _get_type_icon(self, data_type: str) -> str:
        data_type = data_type.lower()
        if 'int' in data_type or 'bigint' in data_type or 'smallint' in data_type:
            return "#"
        elif 'float' in data_type or 'double' in data_type or 'decimal' in data_type or 'real' in data_type:
            return "0.0"
        elif 'date' in data_type or 'time' in data_type or 'timestamp' in data_type:
            return "D"
        elif 'bool' in data_type:
            return "T/F"
        else:
            return "abc"
    
    def _on_table_click(self, table_name: str):
        if self.on_table_select:
            self.on_table_select(table_name)