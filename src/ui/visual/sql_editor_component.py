"""
SQL Editor Component
Provides SQL syntax highlighting and auto-complete functionality
"""

SQL_EDITOR_CSS = """
<style>
    .sql-editor-container {
        width: 100%;
        position: relative;
    }
    .sql-editor-wrapper {
        position: relative;
        border: 1px solid #ddd;
        border-radius: 4px;
        overflow: hidden;
        background: #1e1e1e;
    }
    .sql-editor-textarea {
        width: 100%;
        min-height: 150px;
        padding: 10px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.5;
        background: transparent;
        color: #d4d4d4;
        border: none;
        resize: vertical;
        outline: none;
        tab-size: 4;
    }
    .sql-editor-textarea::placeholder {
        color: #6a6a6a;
    }
    .autocomplete-dropdown {
        position: absolute;
        background: #2d2d2d;
        border: 1px solid #555;
        border-radius: 4px;
        max-height: 200px;
        overflow-y: auto;
        z-index: 1000;
        display: none;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .autocomplete-dropdown.active {
        display: block;
    }
    .autocomplete-item {
        padding: 6px 10px;
        cursor: pointer;
        font-family: 'Consolas', monospace;
        font-size: 13px;
        color: #d4d4d4;
    }
    .autocomplete-item:hover, .autocomplete-item.selected {
        background: #4285f4;
    }
    .autocomplete-item .type-badge {
        display: inline-block;
        font-size: 10px;
        padding: 1px 4px;
        border-radius: 2px;
        margin-left: 6px;
        background: #555;
        color: #ccc;
    }
    .autocomplete-item .type-badge.keyword { background: #c586c5; color: #fff; }
    .autocomplete-item .type-badge.table { background: #4ec9b0; color: #000; }
    .autocomplete-item .type-badge.column { background: #9cdcfe; color: #000; }
    .run-btn {
        background: #28a745;
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 14px;
    }
    .run-btn:hover { background: #218838; }
</style>
"""

SQL_EDITOR_HTML = """
<div class="sql-editor-container">
    <div class="sql-editor-wrapper">
        <textarea
            id="sql-editor"
            class="sql-editor-textarea"
            placeholder="Enter SQL query or drag tables to canvas..."
            spellcheck="false"
        ></textarea>
        <div id="autocomplete-dropdown" class="autocomplete-dropdown"></div>
    </div>
    <div style="margin-top: 10px;">
        <button class="run-btn" onclick="executeSQL()">Run SQL</button>
    </div>
</div>
"""

SQL_EDITOR_JS = """
<script>
const SQL_KEYWORDS = [
    'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'LIKE',
    'ORDER BY', 'GROUP BY', 'HAVING', 'LIMIT', 'OFFSET', 'AS',
    'JOIN', 'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL OUTER JOIN', 'CROSS JOIN',
    'ON', 'USING', 'UNION', 'UNION ALL', 'EXCEPT', 'INTERSECT',
    'INSERT INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE FROM',
    'CREATE TABLE', 'DROP TABLE', 'ALTER TABLE', 'RENAME TO',
    'PRIMARY KEY', 'FOREIGN KEY', 'REFERENCES', 'UNIQUE', 'DEFAULT',
    'NULL', 'NOT NULL', 'AUTO_INCREMENT', 'INTEGER', 'VARCHAR', 'TEXT', 'BOOLEAN',
    'DATE', 'DATETIME', 'TIMESTAMP', 'FLOAT', 'DOUBLE', 'DECIMAL',
    'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'DISTINCT', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END',
    'EXISTS', 'BETWEEN', 'IS NULL', 'IS NOT NULL', 'CAST', 'COALESCE',
    'ASC', 'DESC', 'NULLS FIRST', 'NULLS LAST',
    'WITH', 'RECURSIVE', 'OVER', 'PARTITION BY', 'ROW_NUMBER', 'RANK', 'DENSE_RANK'
];

let autocompleteData = { tables: [], columns: {} };
let currentSuggestion = null;
let suggestionIndex = -1;

async function loadAutocompleteData() {
    try {
        const response = await fetch('/api/tables');
        const tables = await response.json();
        autocompleteData.tables = tables;

        for (const table of tables) {
            try {
                const colResponse = await fetch(`/api/table/${table}`);
                const colData = await colResponse.json();
                autocompleteData.columns[table] = colData.columns.map(c => c.column_name);
            } catch (e) {}
        }
    } catch (e) {
        console.log('Failed to load autocomplete data');
    }
}

function getCaretPosition(textarea) {
    return textarea.selectionStart;
}

function getWordBeforeCursor(text, pos) {
    const before = text.substring(0, pos);
    const match = before.match(/[\\w\\.]+$/);
    return match ? match[0] : '';
}

function showAutocomplete(textarea) {
    const word = getWordBeforeCursor(textarea.value, getCaretPosition(textarea));
    if (word.length < 1) {
        hideAutocomplete();
        return;
    }

    const suggestions = getSuggestions(word);
    if (suggestions.length === 0) {
        hideAutocomplete();
        return;
    }

    const dropdown = document.getElementById('autocomplete-dropdown');
    dropdown.innerHTML = suggestions.map((s, i) => {
        let badge = '';
        if (s.type === 'keyword') badge = '<span class="type-badge keyword">KEYWORD</span>';
        else if (s.type === 'table') badge = '<span class="type-badge table">TABLE</span>';
        else if (s.type === 'column') badge = '<span class="type-badge column">COLUMN</span>';
        return '<div class="autocomplete-item" data-value="' + s.value + '" data-type="' + s.type + '">' + s.value + badge + '</div>';
    }).join('');

    const rect = textarea.getBoundingClientRect();
    dropdown.style.left = rect.left + 'px';
    dropdown.style.top = (rect.bottom + 5) + 'px';
    dropdown.style.width = Math.min(300, rect.width) + 'px';
    dropdown.classList.add('active');

    currentSuggestion = suggestions;
    suggestionIndex = -1;

    dropdown.querySelectorAll('.autocomplete-item').forEach((item, i) => {
        item.addEventListener('click', () => {
            insertSuggestion(item.dataset.value);
        });
    });
}

function getSuggestions(word) {
    const suggestions = [];
    const wordLower = word.toLowerCase();

    SQL_KEYWORDS.forEach(kw => {
        if (kw.toLowerCase().startsWith(wordLower)) {
            suggestions.push({ value: kw, type: 'keyword' });
        }
    });

    autocompleteData.tables.forEach(t => {
        if (t.toLowerCase().startsWith(wordLower)) {
            suggestions.push({ value: t, type: 'table' });
        }
    });

    Object.keys(autocompleteData.columns).forEach(table => {
        autocompleteData.columns[table].forEach(col => {
            const fullName = table + '.' + col;
            if (fullName.toLowerCase().startsWith(wordLower)) {
                suggestions.push({ value: fullName, type: 'column' });
            } else if (col.toLowerCase().startsWith(wordLower)) {
                suggestions.push({ value: col, type: 'column' });
            }
        });
    });

    return suggestions.slice(0, 10);
}

function hideAutocomplete() {
    const dropdown = document.getElementById('autocomplete-dropdown');
    dropdown.classList.remove('active');
    currentSuggestion = null;
    suggestionIndex = -1;
}

function insertSuggestion(value) {
    const textarea = document.getElementById('sql-editor');
    const pos = getCaretPosition(textarea);
    const word = getWordBeforeCursor(textarea.value, pos);

    textarea.value = textarea.value.substring(0, pos - word.length) + value + textarea.value.substring(pos);
    textarea.selectionStart = textarea.selectionEnd = pos - word.length + value.length;

    hideAutocomplete();
    textarea.focus();
}

function handleKeyDown(e) {
    const dropdown = document.getElementById('autocomplete-dropdown');
    if (!dropdown.classList.contains('active')) return;

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        suggestionIndex = Math.min(suggestionIndex + 1, currentSuggestion.length - 1);
        updateSelectedItem();
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        suggestionIndex = Math.max(suggestionIndex - 1, 0);
        updateSelectedItem();
    } else if (e.key === 'Enter' && suggestionIndex >= 0) {
        e.preventDefault();
        insertSuggestion(currentSuggestion[suggestionIndex].value);
    } else if (e.key === 'Escape') {
        hideAutocomplete();
    }
}

function updateSelectedItem() {
    const items = document.querySelectorAll('.autocomplete-item');
    items.forEach((item, i) => {
        item.classList.toggle('selected', i === suggestionIndex);
    });
}

document.getElementById('sql-editor').addEventListener('input', function() {
    showAutocomplete(this);
});

document.getElementById('sql-editor').addEventListener('blur', function() {
    setTimeout(hideAutocomplete, 200);
});

loadAutocompleteData();
</script>
"""

def get_sql_editor_html():
    return SQL_EDITOR_CSS + SQL_EDITOR_HTML + SQL_EDITOR_JS
