"""
Visual Canvas Component
HTML/JS for drag-and-drop table nodes with connection lines
"""

CANVAS_HTML = """
<style>
    .canvas-container {
        width: 100%;
        height: 300px;
        border: 1px solid #ddd;
        border-radius: 4px;
        position: relative;
        overflow: hidden;
        background: #fafafa;
    }
    .canvas-table-node {
        position: absolute;
        min-width: 150px;
        background: white;
        border: 2px solid #4285f4;
        border-radius: 6px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        cursor: move;
        font-size: 12px;
    }
    .canvas-table-node .node-header {
        background: #4285f4;
        color: white;
        padding: 4px 8px;
        border-radius: 4px 4px 0 0;
        font-weight: bold;
        cursor: move;
    }
    .canvas-table-node .node-fields {
        padding: 4px;
        max-height: 150px;
        overflow-y: auto;
    }
    .canvas-table-node .field-item {
        padding: 2px 4px;
        cursor: pointer;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .canvas-table-node .field-item:hover {
        background: #e3f2fd;
    }
    .canvas-table-node .field-item.selected {
        background: #bbdefb;
    }
    .canvas-table-node .field-item input {
        cursor: pointer;
    }
    .canvas-table-node .node-actions {
        padding: 4px;
        border-top: 1px solid #eee;
        display: flex;
        gap: 4px;
    }
    .canvas-table-node .node-actions button {
        flex: 1;
        padding: 2px 6px;
        font-size: 11px;
        background: #f5f5f5;
        border: 1px solid #ddd;
        border-radius: 3px;
        cursor: pointer;
    }
    .canvas-table-node .node-actions button:hover {
        background: #e0e0e0;
    }
    .join-line {
        stroke: #666;
        stroke-width: 2;
        fill: none;
    }
    .join-line:hover {
        stroke: #4285f4;
        stroke-width: 3;
    }
    .join-marker {
        fill: #666;
        cursor: pointer;
    }
    .join-marker:hover {
        fill: #4285f4;
    }
    .canvas-svg {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
    }
    .canvas-svg path {
        pointer-events: stroke;
    }
    .filter-panel {
        position: absolute;
        background: white;
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 10px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        z-index: 100;
        min-width: 200px;
    }
    .filter-panel h4 {
        margin: 0 0 8px 0;
        font-size: 12px;
    }
    .filter-panel select, .filter-panel input {
        width: 100%;
        padding: 4px;
        margin-bottom: 4px;
        font-size: 12px;
    }
    .connection-point {
        fill: #4285f4;
        stroke: white;
        stroke-width: 2;
        cursor: crosshair;
        opacity: 0;
        transition: opacity 0.2s;
    }
    .canvas-table-node:hover .connection-point {
        opacity: 1;
    }
</style>

<div id="canvas-mode" style="display: none;">
    <div class="canvas-container" id="canvas-container">
        <svg class="canvas-svg" id="canvas-svg">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
                </marker>
            </defs>
        </svg>
    </div>
    <div style="margin-top: 10px;">
        <button class="btn" onclick="clearCanvas()">清空画布</button>
        <button class="btn" onclick="runCanvasQuery()">执行查询</button>
    </div>
</div>

<script>
const canvasGenerator = new CanvasSQLGenerator();
let canvasState = { tables: {}, joins: [] };
let draggingNode = null;
let dragOffset = { x: 0, y: 0 };
let connectingFrom = null;

class CanvasSQLGenerator {
    constructor() {
        this.state = { tables: {}, joins: [] };
    }

    addTable(tableName, x = 50, y = 50) {
        const alias = this.generateAlias(tableName);
        this.state.tables[alias] = {
            tableName,
            alias,
            x, y,
            selectedFields: [],
            filters: []
        };
        return alias;
    }

    removeTable(alias) {
        delete this.state.tables[alias];
        this.state.joins = this.state.joins.filter(j =>
            j.leftTable !== alias && j.rightTable !== alias
        );
    }

    toggleField(alias, fieldName) {
        const table = this.state.tables[alias];
        if (!table) return;
        const idx = table.selectedFields.indexOf(fieldName);
        if (idx >= 0) {
            table.selectedFields.splice(idx, 1);
        } else {
            table.selectedFields.push(fieldName);
        }
    }

    addFilter(alias, field, operator, value) {
        const table = this.state.tables[alias];
        if (!table) return;
        table.filters.push({ field, operator, value });
    }

    removeFilter(alias, field, operator, value) {
        const table = this.state.tables[alias];
        if (!table) return;
        table.filters = table.filters.filter(f =>
            !(f.field === field && f.operator === operator && f.value === value)
        );
    }

    addJoin(leftTable, leftField, rightTable, rightField, joinType = 'INNER JOIN') {
        this.state.joins.push({
            leftTable, leftField, rightTable, rightField, joinType
        });
    }

    removeJoin(leftTable, leftField, rightTable, rightField) {
        this.state.joins = this.state.joins.filter(j =>
            !(j.leftTable === leftTable && j.leftField === leftField &&
              j.rightTable === rightTable && j.rightField === rightField)
        );
    }

    cycleJoinType(leftTable, leftField, rightTable, rightField) {
        const joinTypes = ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'];
        const join = this.state.joins.find(j =>
            j.leftTable === leftTable && j.leftField === leftField &&
            j.rightTable === rightTable && j.rightField === rightField
        );
        if (join) {
            const idx = joinTypes.indexOf(join.joinType);
            join.joinType = joinTypes[(idx + 1) % joinTypes.length];
        }
    }

    generateAlias(tableName) {
        const words = tableName.toLowerCase().split('_');
        if (words.length > 1) {
            return words.map(w => w[0]).join('');
        }
        return tableName.substring(0, 2);
    }

    generateSQL() {
        if (Object.keys(this.state.tables).length === 0) return '';

        const selectParts = [];
        const whereParts = [];

        for (const [alias, table] of Object.entries(this.state.tables)) {
            if (table.selectedFields.length > 0) {
                table.selectedFields.forEach(f => {
                    selectParts.push(`${alias}.${f}`);
                });
            } else {
                selectParts.push(`${alias}.*`);
            }

            table.filters.forEach(f => {
                whereParts.push(this.formatCondition(alias, f.field, f.operator, f.value));
            });
        }

        const selectClause = 'SELECT ' + (selectParts.length > 0 ? selectParts.join(', ') : '*');

        const mainAlias = Object.keys(this.state.tables)[0];
        const mainTable = this.state.tables[mainAlias];
        let fromClause = `FROM ${mainTable.tableName} AS ${mainAlias}`;

        this.state.joins.forEach(join => {
            fromClause += ` ${join.joinType} ${this.state.tables[join.rightTable].tableName} AS ${join.rightTable} ON ${join.leftTable}.${join.leftField} = ${join.rightTable}.${join.rightField}`;
        });

        const whereClause = whereParts.length > 0 ? ' WHERE ' + whereParts.join(' AND ') : '';

        return [selectClause, fromClause, whereClause].join(' ');
    }

    formatCondition(alias, field, operator, value) {
        if (operator === '=' || operator === '!=' || operator === '<' || operator === '>' ||
            operator === '<=' || operator === '>=') {
            return `${alias}.${field} ${operator} '${value}'`;
        } else if (operator === 'LIKE') {
            return `${alias}.${field} LIKE '%${value}%'`;
        } else if (operator === 'IN') {
            const values = value.split(',').map(v => `'${v.trim()}'`).join(', ');
            return `${alias}.${field} IN (${values})`;
        } else if (operator === 'IS NULL') {
            return `${alias}.${field} IS NULL`;
        } else if (operator === 'IS NOT NULL') {
            return `${alias}.${field} IS NOT NULL`;
        }
        return `${alias}.${field} ${operator} '${value}'`;
    }

    getState() {
        return JSON.parse(JSON.stringify(this.state));
    }

    loadState(state) {
        this.state = JSON.parse(JSON.stringify(state));
    }

    reset() {
        this.state = { tables: {}, joins: [] };
    }
}

function renderCanvas() {
    const container = document.getElementById('canvas-container');
    const svg = document.getElementById('canvas-svg');

    document.querySelectorAll('.canvas-table-node').forEach(n => n.remove());
    svg.querySelectorAll('path').forEach(p => p.remove());

    const state = canvasGenerator.getState();

    for (const [alias, table] of Object.entries(state.tables)) {
        const node = createTableNode(alias, table);
        container.appendChild(node);
    }

    state.joins.forEach(join => {
        drawJoinLine(join);
    });
}

function createTableNode(alias, table) {
    const node = document.createElement('div');
    node.className = 'canvas-table-node';
    node.id = `node-${alias}`;
    node.style.left = table.x + 'px';
    node.style.top = table.y + 'px';

    node.innerHTML = `
        <div class="node-header">${table.tableName}</div>
        <div class="node-fields" id="fields-${alias}"></div>
        <div class="node-actions">
            <button onclick="showFilterPanel('${alias}')">+ 筛选</button>
            <button onclick="removeNode('${alias}')">移除</button>
        </div>
    `;

    node.addEventListener('mousedown', (e) => {
        if (e.target.classList.contains('node-header')) {
            draggingNode = { alias, node };
            const rect = node.getBoundingClientRect();
            dragOffset = { x: e.clientX - rect.left, y: e.clientY - rect.top };
        }
    });

    loadTableFields(alias, table.tableName, table.selectedFields);

    return node;
}

async function loadTableFields(alias, tableName, selectedFields = []) {
    const fieldsContainer = document.getElementById(`fields-${alias}`);
    if (!fieldsContainer) return;

    try {
        const response = await fetch(`/api/table/${tableName}`);
        const data = await response.json();

        fieldsContainer.innerHTML = data.columns.map(col => {
            const isSelected = selectedFields.includes(col.column_name);
            return `
                <div class="field-item ${isSelected ? 'selected' : ''}">
                    <input type="checkbox" ${isSelected ? 'checked' : ''}
                           onchange="toggleField('${alias}', '${col.column_name}')">
                    <span>${col.column_name}</span>
                    <small style="color:#999">${col.data_type}</small>
                </div>
            `;
        }).join('');
    } catch (err) {
        fieldsContainer.innerHTML = '<div style="color:red;font-size:11px">Failed to load fields</div>';
    }
}

function toggleField(alias, fieldName) {
    canvasGenerator.toggleField(alias, fieldName);
    const state = canvasGenerator.getState();
    updateSQLDisplay(canvasGenerator.generateSQL());
}

function removeNode(alias) {
    canvasGenerator.removeTable(alias);
    renderCanvas();
    updateSQLDisplay(canvasGenerator.generateSQL());
}

function showFilterPanel(alias) {
    const existing = document.querySelector('.filter-panel');
    if (existing) existing.remove();

    const table = canvasGenerator.getState().tables[alias];
    if (!table) return;

    const panel = document.createElement('div');
    panel.className = 'filter-panel';
    panel.innerHTML = `
        <h4>Filter: ${table.tableName}</h4>
        <select id="filter-field">
            <option value="">选择字段...</option>
        </select>
        <select id="filter-operator">
            <option value="=">=</option>
            <option value="!=">!=</option>
            <option value="<"><</option>
            <option value=">">></option>
            <option value="<="><=</option>
            <option value=">=">>=</option>
            <option value="LIKE">LIKE</option>
            <option value="IS NULL">IS NULL</option>
        </select>
        <input type="text" id="filter-value" placeholder="Value">
        <button class="btn btn-sm" onclick="applyFilter('${alias}')">应用</button>
        <button class="btn btn-sm" onclick="this.parentElement.remove()">取消</button>
    `;

    fetch(`/api/table/${table.tableName}`)
        .then(r => r.json())
        .then(data => {
            const select = panel.querySelector('#filter-field');
            data.columns.forEach(col => {
                const opt = document.createElement('option');
                opt.value = col.column_name;
                opt.textContent = col.column_name;
                select.appendChild(opt);
            });
        });

    const node = document.getElementById(`node-${alias}`);
    const rect = node.getBoundingClientRect();
    const containerRect = document.getElementById('canvas-container').getBoundingClientRect();
    panel.style.left = (rect.right - containerRect.left + 10) + 'px';
    panel.style.top = rect.top - containerRect.top + 'px';

    document.getElementById('canvas-container').appendChild(panel);
}

function applyFilter(alias) {
    const field = document.querySelector('#filter-field').value;
    const operator = document.querySelector('#filter-operator').value;
    const value = document.querySelector('#filter-value').value;

    if (!field) {
        alert('Please select a field');
        return;
    }

    canvasGenerator.addFilter(alias, field, operator, value);
    document.querySelector('.filter-panel').remove();
    updateSQLDisplay(canvasGenerator.generateSQL());
}

function drawJoinLine(join) {
    const svg = document.getElementById('canvas-svg');
    const leftNode = document.getElementById(`node-${join.leftTable}`);
    const rightNode = document.getElementById(`node-${join.rightTable}`);

    if (!leftNode || !rightNode) return;

    const leftRect = leftNode.getBoundingClientRect();
    const rightRect = rightNode.getBoundingClientRect();
    const svgRect = svg.getBoundingClientRect();

    const x1 = leftRect.right - svgRect.left;
    const y1 = leftRect.top + leftRect.height / 2 - svgRect.top;
    const x2 = rightRect.left - svgRect.left;
    const y2 = rightRect.top + rightRect.height / 2 - svgRect.top;

    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const midX = (x1 + x2) / 2;
    path.setAttribute('d', `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`);
    path.setAttribute('class', 'join-line');
    path.setAttribute('marker-end', 'url(#arrowhead)');
    path.dataset.join = JSON.stringify(join);

    path.addEventListener('click', () => {
        canvasGenerator.cycleJoinType(join.leftTable, join.leftField, join.rightTable, join.rightField);
        renderCanvas();
        updateSQLDisplay(canvasGenerator.generateSQL());
    });

    svg.appendChild(path);
}

function clearCanvas() {
    canvasGenerator.reset();
    renderCanvas();
    updateSQLDisplay('');
}

function runCanvasQuery() {
    const sql = canvasGenerator.generateSQL();
    if (!sql) {
        alert('No query to run. Add tables to the canvas first.');
        return;
    }
    document.getElementById('sql-input').value = sql;
    runSQL(1);
}

function updateSQLDisplay(sql) {
    document.getElementById('sql-input').value = sql;
}

document.addEventListener('mousemove', (e) => {
    if (draggingNode) {
        const container = document.getElementById('canvas-container');
        const rect = container.getBoundingClientRect();
        const x = e.clientX - rect.left - dragOffset.x;
        const y = e.clientY - rect.top - dragOffset.y;

        draggingNode.node.style.left = Math.max(0, Math.min(x, rect.width - 150)) + 'px';
        draggingNode.node.style.top = Math.max(0, Math.min(y, rect.height - 100)) + 'px';

        canvasGenerator.state.tables[draggingNode.alias].x = parseInt(draggingNode.node.style.left);
        canvasGenerator.state.tables[draggingNode.alias].y = parseInt(draggingNode.node.style.top);

        renderCanvas();
    }
});

document.addEventListener('mouseup', () => {
    draggingNode = null;
});

function addTableToCanvas(tableName) {
    const container = document.getElementById('canvas-container');
    const rect = container.getBoundingClientRect();
    const x = 50 + Math.random() * (rect.width - 250);
    const y = 50 + Math.random() * (rect.height - 200);

    const alias = canvasGenerator.addTable(tableName, x, y);
    renderCanvas();
    updateSQLDisplay(canvasGenerator.generateSQL());
}
</script>
"""