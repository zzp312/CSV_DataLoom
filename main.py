import flet as ft
import pandas as pd
import os
import time
from src.ui.left_panel import LeftPanel
from src.ui.middle_panel import MiddlePanel
from src.ui.right_panel import RightPanel
from src.core.duckdb_manager import DuckDBManager

def main(page: ft.Page):
    page.title = "Local Data Dual-Mode Workbench"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 1200
    page.window_height = 800
    
    db_manager = DuckDBManager()
    
    def handle_table_select(table_name: str):
        sql = f"SELECT * FROM {table_name}"
        middle_panel.update_sql_display(sql)
    
    def handle_run_sql(sql: str):
        if not sql.strip():
            return
        
        try:
            start_time = time.time()
            df = db_manager.fetch_df(sql)
            execution_time = time.time() - start_time
            right_panel.display_result(df, execution_time)
        except Exception as e:
            page.snack_bar = ft.SnackBar(ft.Text(f"Execution error: {str(e)}"), open=True)
            page.update()
    
    def handle_file_drop(e):
        if e.files:
            for file in e.files:
                process_file(file.path)
    
    def handle_file_select():
        page.snack_bar = ft.SnackBar(ft.Text("Please drag CSV/Excel files to the upload area"), open=True)
        page.update()
    
    def process_file(file_path: str):
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext in ['.csv']:
            show_csv_import_dialog(file_path)
        elif file_ext in ['.xlsx', '.xls']:
            show_excel_import_dialog(file_path)
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Unsupported file format: {file_ext}"), open=True)
            page.update()
    
    left_panel = LeftPanel(on_table_select=handle_table_select, on_file_select=handle_file_select)
    middle_panel = MiddlePanel(on_run_sql=handle_run_sql)
    right_panel = RightPanel()
    
    def show_csv_import_dialog(file_path: str):
        table_name_input = ft.TextField(
            label="Table Name",
            value=os.path.splitext(os.path.basename(file_path))[0],
            width=200
        )
        
        header_row_input = ft.TextField(
            label="Header Row (0-based)",
            value="0",
            width=150
        )
        
        content_row_input = ft.TextField(
            label="Content Start Row",
            value="1",
            width=150
        )
        
        def confirm_import(e):
            try:
                table_name = table_name_input.value.strip()
                header_row = int(header_row_input.value)
                content_row = int(content_row_input.value)
                
                skip_rows = content_row - (header_row + 1)
                if skip_rows < 0:
                    skip_rows = 0
                
                db_manager.import_csv(file_path, table_name, header_row, skip_rows)
                left_panel.update_table_list()
                
                dlg_modal.open = False
                page.update()
                
                page.snack_bar = ft.SnackBar(
                    ft.Text(f"CSV imported successfully: {table_name}"),
                    open=True
                )
                page.update()
            except Exception as ex:
                page.snack_bar = ft.SnackBar(ft.Text(f"Import failed: {str(ex)}"), open=True)
                page.update()
        
        dlg_modal = ft.AlertDialog(
            title=ft.Text("Import CSV File"),
            content=ft.Column(
                controls=[
                    ft.Text(f"File: {os.path.basename(file_path)}"),
                    table_name_input,
                    header_row_input,
                    content_row_input
                ],
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: setattr(dlg_modal, 'open', False)),
                ft.TextButton("Confirm", on_click=confirm_import)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        page.dialog = dlg_modal
        dlg_modal.open = True
        page.update()
    
    def show_excel_import_dialog(file_path: str):
        try:
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            selected_sheets = []
            sheet_checkboxes = []
            
            for sheet in sheet_names:
                checkbox = ft.Checkbox(label=sheet, value=True)
                sheet_checkboxes.append(checkbox)
                selected_sheets.append({'name': sheet, 'checkbox': checkbox})
            
            def confirm_import(e):
                try:
                    for sheet_info in selected_sheets:
                        if sheet_info['checkbox'].value:
                            sheet_name = sheet_info['name']
                            table_name = sheet_name.lower().replace(' ', '_')
                            
                            db_manager.import_excel(file_path, sheet_name, table_name)
                    
                    left_panel.update_table_list()
                    
                    dlg_modal.open = False
                    page.update()
                    
                    page.snack_bar = ft.SnackBar(
                        ft.Text("Excel file imported successfully"),
                        open=True
                    )
                    page.update()
                except Exception as ex:
                    page.snack_bar = ft.SnackBar(ft.Text(f"Import failed: {str(ex)}"), open=True)
                    page.update()
            
            dlg_modal = ft.AlertDialog(
                title=ft.Text("Import Excel File"),
                content=ft.Column(
                    controls=[
                        ft.Text(f"File: {os.path.basename(file_path)}"),
                        ft.Text("Select sheets to import:"),
                        *sheet_checkboxes
                    ],
                    width=400,
                    height=300,
                    scroll=True
                ),
                actions=[
                    ft.TextButton("Cancel", on_click=lambda e: setattr(dlg_modal, 'open', False)),
                    ft.TextButton("Confirm", on_click=confirm_import)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            page.dialog = dlg_modal
            dlg_modal.open = True
            page.update()
            
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"Failed to read Excel: {str(ex)}"), open=True)
            page.update()
    
    page.draggable = True
    page.on_file_drop = handle_file_drop
    
    page.add(
        ft.Row(
            controls=[
                ft.Container(
                    content=left_panel,
                    width=300,
                    border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_200))
                ),
                ft.Container(
                    content=middle_panel,
                    expand=True,
                    border=ft.Border(right=ft.BorderSide(1, ft.Colors.GREY_200))
                ),
                ft.Container(
                    content=right_panel,
                    width=400
                )
            ],
            expand=True
        )
    )

if __name__ == "__main__":
    ft.run(main)