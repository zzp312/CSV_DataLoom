import flet as ft
from typing import Callable, List, Dict, Any

@ft.control
class MiddlePanel(ft.Column):
    def __init__(self, on_run_sql: Callable = None):
        super().__init__()
        self.on_run_sql = on_run_sql
        self.canvas_mode = True
        self.canvas_area = None
        self.sql_editor = None
        self.current_sql = ""
        self._build_content()
    
    def _build_content(self):
        self.canvas_area = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Visual Canvas", size=16, text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_500)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True
            ),
            border=ft.Border.all(1, ft.Colors.GREY_200),
            border_radius=8,
            expand=True,
            padding=10
        )
        
        self.sql_editor = ft.TextField(
            multiline=True,
            expand=True,
            hint_text="Enter SQL statement here...",
            border_color=ft.Colors.GREY_200,
            border_radius=8,
            visible=False,
            on_change=self._on_sql_change
        )
        
        content_stack = ft.Stack(
            controls=[self.canvas_area, self.sql_editor],
            expand=True
        )
        
        self.controls = [
            ft.Row(
                controls=[
                    ft.Button("Canvas Mode",
                        on_click=self._switch_to_canvas,
                        bgcolor=ft.Colors.BLUE_500,
                        color=ft.Colors.WHITE
                    ),
                    ft.Button("Code Mode",
                        on_click=self._switch_to_code,
                        bgcolor=ft.Colors.GREY_500,
                        color=ft.Colors.WHITE
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            ),
            ft.Divider(height=1),
            content_stack,
            ft.Divider(height=1),
            self._build_sql_display()
        ]
        self.expand = True
    
    def _build_sql_display(self):
        return ft.Row(
            controls=[
                ft.Text("Generated SQL:", size=12, color=ft.Colors.GREY_600),
                ft.Container(
                    content=ft.Text(
                        self.current_sql,
                        size=12,
                        color=ft.Colors.BLUE_600,
                        selectable=True
                    ),
                    padding=5,
                    bgcolor=ft.Colors.GREY_50,
                    border_radius=4,
                    expand=True
                ),
                ft.Button("Run",
                    icon="play_arrow",
                    on_click=self._on_run_click,
                    bgcolor=ft.Colors.BLUE_500,
                    color=ft.Colors.WHITE
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
    
    def _switch_to_canvas(self, e):
        self.canvas_area.visible = True
        self.sql_editor.visible = False
        self.canvas_mode = True
        self.update()
    
    def _switch_to_code(self, e):
        self.canvas_area.visible = False
        self.sql_editor.visible = True
        self.canvas_mode = False
        self.update()
    
    def _on_sql_change(self, e):
        self.current_sql = e.control.value
    
    def _on_run_click(self, e):
        if self.on_run_sql:
            if self.canvas_mode:
                self.on_run_sql(self.current_sql)
            else:
                self.on_run_sql(self.sql_editor.value)
    
    def update_sql_display(self, sql: str):
        self.current_sql = sql
        self.update()
    
    def set_sql_content(self, sql: str):
        self.sql_editor.value = sql
        self.update()
