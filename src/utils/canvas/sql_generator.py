"""
Canvas to SQL Generator
Converts visual canvas operations (drag, connect, join) to SQL statements
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

class JoinType(Enum):
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL JOIN"

@dataclass
class TableNode:
    table_name: str
    alias: str
    x: int
    y: int
    selected_fields: List[str] = field(default_factory=list)
    filters: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class JoinConnection:
    left_table: str
    left_field: str
    right_table: str
    right_field: str
    join_type: JoinType = JoinType.INNER

@dataclass
class CanvasState:
    tables: Dict[str, TableNode] = field(default_factory=dict)
    joins: List[JoinConnection] = field(default_factory=list)

class CanvasSQLGenerator:
    def __init__(self):
        self.state = CanvasState()

    def add_table(self, table_name: str, x: int = 0, y: int = 0) -> TableNode:
        alias = self._generate_alias(table_name)
        node = TableNode(table_name=table_name, alias=alias, x=x, y=y)
        self.state.tables[alias] = node
        return node

    def remove_table(self, alias: str):
        if alias in self.state.tables:
            del self.state.tables[alias]
        self.state.joins = [j for j in self.state.joins if j.left_table != alias and j.right_table != alias]

    def toggle_field(self, table_alias: str, field_name: str):
        if table_alias in self.state.tables:
            node = self.state.tables[table_alias]
            if field_name in node.selected_fields:
                node.selected_fields.remove(field_name)
            else:
                node.selected_fields.append(field_name)

    def add_filter(self, table_alias: str, field: str, operator: str, value: str):
        if table_alias in self.state.tables:
            self.state.tables[table_alias].filters.append({
                'field': field,
                'operator': operator,
                'value': value
            })

    def remove_filter(self, table_alias: str, field: str, operator: str, value: str):
        if table_alias in self.state.tables:
            node = self.state.tables[table_alias]
            node.filters = [f for f in node.filters if not (
                f['field'] == field and f['operator'] == operator and f['value'] == value
            )]

    def add_join(self, left_table: str, left_field: str, right_table: str, right_field: str, join_type: JoinType = JoinType.INNER):
        join = JoinConnection(
            left_table=left_table,
            left_field=left_field,
            right_table=right_table,
            right_field=right_field,
            join_type=join_type
        )
        self.state.joins.append(join)
        return join

    def remove_join(self, left_table: str, left_field: str, right_table: str, right_field: str):
        self.state.joins = [j for j in self.state.joins if not (
            j.left_table == left_table and j.left_field == left_field and
            j.right_table == right_table and j.right_field == right_field
        )]

    def cycle_join_type(self, left_table: str, left_field: str, right_table: str, right_field: str):
        for join in self.state.joins:
            if (join.left_table == left_table and join.left_field == left_field and
                join.right_table == right_table and join.right_field == right_field):
                join_types = [JoinType.INNER, JoinType.LEFT, JoinType.RIGHT, JoinType.FULL]
                current_idx = join_types.index(join.join_type)
                join.join_type = join_types[(current_idx + 1) % len(join_types)]

    def _generate_alias(self, table_name: str) -> str:
        words = table_name.lower().split('_')
        if len(words) > 1:
            return ''.join(w[0] for w in words if w)
        return table_name[:2]

    def _format_field(self, alias: str, field: str) -> str:
        return f"{alias}.{field}"

    def _format_condition(self, alias: str, field: str, operator: str, value: str) -> str:
        if operator in ('=', '!=', '<', '>', '<=', '>='):
            return f"{alias}.{field} {operator} '{value}'"
        elif operator == 'LIKE':
            return f"{alias}.{field} LIKE '%{value}%'"
        elif operator == 'IN':
            values = ', '.join(f"'{v}'" for v in value.split(','))
            return f"{alias}.{field} IN ({values})"
        elif operator == 'IS NULL':
            return f"{alias}.{field} IS NULL"
        elif operator == 'IS NOT NULL':
            return f"{alias}.{field} IS NOT NULL"
        return f"{alias}.{field} {operator} '{value}'"

    def generate_select(self) -> str:
        if not self.state.tables:
            return ""

        select_parts = []
        where_parts = []

        for alias, node in self.state.tables.items():
            if node.selected_fields:
                for field in node.selected_fields:
                    select_parts.append(self._format_field(alias, field))
            else:
                select_parts.append(f"{alias}.*")

            for f in node.filters:
                where_parts.append(self._format_condition(alias, f['field'], f['operator'], f['value']))

        select_clause = "SELECT " + (", ".join(select_parts) if select_parts else "*")

        from_parts = []
        join_clauses = []

        main_alias = list(self.state.tables.keys())[0]
        main_node = self.state.tables[main_alias]
        from_parts.append(f"{main_node.table_name} AS {main_alias}")

        for join in self.state.joins:
            join_str = f" {join.join_type.value} {join.right_table} AS {join.right_table} ON {join.left_table}.{join.left_field} = {join.right_table}.{join.right_field}"
            join_clauses.append(join_str)

        from_clause = "FROM " + " ".join([from_parts[0]] + join_clauses)

        where_clause = ""
        if where_parts:
            where_clause = " WHERE " + " AND ".join(where_parts)

        return " ".join([select_clause, from_clause, where_clause]).strip()

    def get_state(self) -> Dict[str, Any]:
        return {
            'tables': {
                alias: {
                    'table_name': node.table_name,
                    'alias': node.alias,
                    'x': node.x,
                    'y': node.y,
                    'selected_fields': node.selected_fields,
                    'filters': node.filters
                }
                for alias, node in self.state.tables.items()
            },
            'joins': [
                {
                    'left_table': j.left_table,
                    'left_field': j.left_field,
                    'right_table': j.right_table,
                    'right_field': j.right_field,
                    'join_type': j.join_type.value
                }
                for j in self.state.joins
            ]
        }

    def reset(self):
        self.state = CanvasState()

    def load_state(self, state: Dict[str, Any]):
        self.state = CanvasState()
        for alias, node_data in state.get('tables', {}).items():
            node = TableNode(
                table_name=node_data['table_name'],
                alias=node_data['alias'],
                x=node_data.get('x', 0),
                y=node_data.get('y', 0),
                selected_fields=node_data.get('selected_fields', []),
                filters=node_data.get('filters', [])
            )
            self.state.tables[alias] = node

        for join_data in state.get('joins', []):
            join = JoinConnection(
                left_table=join_data['left_table'],
                left_field=join_data['left_field'],
                right_table=join_data['right_table'],
                right_field=join_data['right_field'],
                join_type=JoinType(join_data.get('join_type', 'INNER JOIN'))
            )
            self.state.joins.append(join)
