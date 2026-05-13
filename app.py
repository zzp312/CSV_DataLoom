from flask import Flask, render_template_string, request, jsonify, send_file
import pandas as pd
import duckdb
import os
import io
import time
from src.core.duckdb_manager import DuckDBManager
from src.utils.test_runner import TestRunner

app = Flask(__name__)
db_manager = DuckDBManager()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>本地数据双模工作台</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
        .container { display: flex; height: calc(100vh - 100px); gap: 0; }
        .left-panel { width: 300px; border-right: 1px solid #ddd; padding: 10px; overflow-y: auto; flex-shrink: 0; }
        .middle-panel { flex: 1; display: flex; flex-direction: column; padding: 10px; overflow: hidden; }
        .resizer { width: 6px; cursor: col-resize; background: #e0e0e0; }
        .resizer:hover { background: #ccc; }
        .btn { padding: 8px 16px; background: #4285f4; color: white; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #3367d6; }
        .btn-sm { padding: 4px 8px; font-size: 12px; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        .upload-area { border: 2px dashed #4285f4; border-radius: 8px; padding: 20px; text-align: center; margin-bottom: 10px; }
        .upload-area:hover { border-color: #3367d6; }
        textarea { width: 100%; height: 150px; margin-bottom: 10px; padding: 8px; box-sizing: border-box; font-family: 'Consolas', monospace; font-size: 14px; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; table-layout: fixed; }
        th, td { border: 1px solid #ddd; padding: 4px; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; position: relative; }
        th { background: #f5f5f5; }
        .cell-tooltip { position: absolute; bottom: 100%; left: 0; background: #333; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; z-index: 1000; white-space: normal; max-width: 300px; display: none; }
        td:hover .cell-tooltip { display: block; }
        .modal { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px; z-index: 1000; max-width: 80%; max-height: 80%; overflow-y: auto; }
        .modal.active { display: block; }
        .modal-backdrop { display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 999; }
        .modal-backdrop.active { display: block; }
        input { margin: 5px 0; padding: 4px; width: 200px; }
        .success { color: green; }
        .error { color: red; }
        .pagination { margin-top: 10px; display: flex; gap: 5px; align-items: center; }
        
        .bottom-drawer { position: fixed; bottom: 0; left: 0; right: 0; height: 100px; background: white; border-top: 1px solid #ddd; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); z-index: 500; overflow: hidden; }
        .drawer-header { display: flex; justify-content: space-between; align-items: center; padding: 10px 15px; background: #f5f5f5; border-bottom: 1px solid #ddd; cursor: pointer; }
        .drawer-header:hover { background: #eee; }
        .drawer-title { font-weight: bold; color: #4285f4; }
        .drawer-toggle { font-size: 16px; }
        .drawer-resizer { height: 4px; background: #ccc; cursor: ns-resize; }
        .drawer-resizer:hover { background: #999; }
        .drawer-content { padding: 10px; height: calc(100% - 46px); overflow-y: auto; }
        .drawer-actions { display: flex; gap: 10px; margin-bottom: 10px; }
        .drawer-actions button { padding: 4px 8px; font-size: 12px; }
        .drawer-pagination { position: absolute; top: 6px; right: 10px; display: flex; gap: 5px; align-items: center; }
        .drawer-pagination button { padding: 4px 10px; font-size: 12px; }
        .drawer-pagination span { font-size: 12px; color: #666; }
        
        .column-select-modal { display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 20px; border: 1px solid #ddd; border-radius: 8px; z-index: 1000; width: 400px; max-height: 80%; overflow-y: auto; }
        .column-select-modal.active { display: block; }
        .column-select-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 1px solid #eee; }
        .column-select-header h3 { margin: 0; }
        .column-select-actions { display: flex; gap: 10px; }
        .column-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #eee; }
        .column-item:hover { background: #f5f5f5; }
        .column-name { flex: 1; }
        .column-item button { padding: 2px 6px; font-size: 11px; }
        .column-item button.hide-btn { background: #fff3e0; border: 1px solid #ff9800; color: #e65100; }
        .column-item button.show-btn { background: #e3f2fd; border: 1px solid #4285f4; color: #1565c0; }
        .pagination button { padding: 4px 10px; }
        .pagination span { font-size: 12px; color: #666; }

        .mode-tabs { margin-bottom: 10px; display: flex; gap: 5px; }
        .mode-tab { padding: 6px 12px; background: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; }
        .mode-tab.active { background: #4285f4; color: white; border-color: #4285f4; }

        .canvas-container { width: 100%; height: 280px; border: 1px solid #ddd; border-radius: 4px; position: relative; overflow: hidden; background: #fafafa; cursor: grab; }
        .canvas-container:active { cursor: grabbing; }
        .canvas-inner { position: absolute; top: 0; left: 0; width: 2000px; height: 2000px; transform-origin: top left; transition: transform 0.15s ease-out; }
        .canvas-table-node { position: absolute; min-width: 160px; background: white; border: 2px solid #4285f4; border-radius: 6px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); cursor: move; font-size: 12px; transform-origin: top left; }
        .canvas-table-node .node-header { background: #4285f4; color: white; padding: 5px 10px; border-radius: 4px 4px 0 0; font-weight: bold; cursor: move; position: relative; }
        .canvas-table-node .node-header .filter-count { position: absolute; right: 5px; top: 5px; font-size: 10px; background: #ff9800; padding: 1px 4px; border-radius: 10px; }
        .canvas-table-node .node-fields { padding: 4px; max-height: 80px; overflow-y: auto; }
        .canvas-table-node .field-item { padding: 2px 4px; cursor: pointer; display: flex; align-items: center; gap: 4px; }
        .canvas-table-node .field-item:hover { background: #e3f2fd; }
        .canvas-table-node .field-item.selected { background: #bbdefb; }
        .canvas-table-node .field-item .field-name { flex: 1; }
        .canvas-table-node .field-item .field-type { font-size: 10px; color: #999; }
        .canvas-table-node .node-filters { padding: 4px; border-top: 1px dashed #ddd; background: #fff8e1; }
        .canvas-table-node .node-filters .filter-item { display: flex; align-items: center; gap: 4px; font-size: 10px; color: #e65100; }
        .canvas-table-node .node-filters .filter-item .remove-filter { cursor: pointer; color: #999; }
        .canvas-table-node .node-filters .filter-item .remove-filter:hover { color: #f00; }
        .canvas-table-node .node-actions { padding: 4px; border-top: 1px solid #eee; display: flex; gap: 4px; }
        .canvas-table-node .node-actions button { flex: 1; padding: 2px 6px; font-size: 11px; background: #f5f5f5; border: 1px solid #ddd; border-radius: 3px; cursor: pointer; }
        .canvas-table-node .node-actions button:hover { background: #e0e0e0; }
        .canvas-table-node .connection-point { width: 8px; height: 8px; background: #4285f4; border-radius: 50%; position: absolute; cursor: crosshair; opacity: 0; transition: opacity 0.2s; z-index: 10; }
        .canvas-table-node.main-table { border-color: #ff9800; box-shadow: 0 0 10px rgba(255, 152, 0, 0.3); }
        .canvas-table-node.main-table .node-header { background: #ff9800; }
        .canvas-table-node .node-header .main-indicator { color: #ffeb3b; font-size: 14px; margin-left: 4px; }
        .canvas-table-node:hover .connection-point { opacity: 1; }
        .canvas-table-node .connection-point.top { top: -4px; left: 50%; transform: translateX(-50%); }
        .canvas-table-node .connection-point.bottom { bottom: -4px; left: 50%; transform: translateX(-50%); }
        .canvas-table-node .connection-point.left { left: -4px; top: 50%; transform: translateY(-50%); }
        .canvas-table-node .connection-point.right { right: -4px; top: 50%; transform: translateY(-50%); }
        .join-line { stroke: #4285f4; stroke-width: 2; fill: none; }
        .join-line:hover { stroke: #ff5722; stroke-width: 3; }
        .canvas-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; }
        .canvas-svg path { pointer-events: stroke; }
        .join-marker { fill: #4285f4; cursor: pointer; }
        .join-marker:hover { fill: #ff5722; }
        .filter-panel { position: absolute; background: white; border: 1px solid #ddd; border-radius: 4px; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.15); z-index: 100; min-width: 200px; }
        .filter-panel select, .filter-panel input { width: 100%; padding: 4px; margin-bottom: 4px; font-size: 12px; }
        .canvas-hint { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; color: #999; font-size: 13px; pointer-events: none; }
        .canvas-hint .hint-icon { font-size: 32px; margin-bottom: 8px; }
        .tooltip { position: absolute; background: #333; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px; z-index: 1000; pointer-events: none; display: none; }
        .tooltip.visible { display: block; }
        
        .table-tooltip { position: fixed; background: white; border: 1px solid #ddd; border-radius: 6px; box-shadow: 2px 2px 10px rgba(0,0,0,0.15); padding: 8px; z-index: 1000; pointer-events: none; display: none; min-width: 200px; max-width: 600px; max-height: 400px; overflow-y: auto; }
        .table-tooltip.visible { display: block; }
        .table-tooltip .tooltip-header { font-weight: bold; color: #4285f4; margin-bottom: 6px; padding-bottom: 4px; border-bottom: 1px solid #eee; }
        .table-tooltip .tooltip-content { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 8px; }
        .table-tooltip .tooltip-row { display: flex; gap: 8px; padding: 2px 0; font-size: 12px; }
        .table-tooltip .tooltip-field { flex: 1; color: #333; }
        .table-tooltip .tooltip-type { color: #999; font-size: 11px; }
        
        .data-panel { margin-top: 10px; border: 1px solid #ddd; border-radius: 4px; padding: 10px; display: none; }
        .data-panel.visible { display: block; }
        .data-panel .panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .data-panel .panel-title { font-weight: bold; color: #4285f4; }
        .data-panel .close-btn { cursor: pointer; color: #999; font-size: 14px; }
        .data-panel .close-btn:hover { color: #f00; }
        .data-panel .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .data-panel .data-table th, .data-panel .data-table td { border: 1px solid #ddd; padding: 4px; text-align: left; }
        .data-panel .data-table th { background: #f5f5f5; font-weight: bold; }
        .data-panel .data-pagination { margin-top: 10px; display: flex; gap: 5px; align-items: center; justify-content: center; }
        .data-panel .data-pagination button { padding: 4px 10px; font-size: 12px; }
        
        /* SQL Syntax Highlighting */
        .sql-editor-container { position: relative; }
        .sql-editor { width: 100%; min-height: 150px; max-height: 300px; margin-bottom: 10px; padding: 8px; box-sizing: border-box; font-family: 'Consolas', monospace; font-size: 14px; background: #282c34; color: #abb2bf; border: 1px solid #3e4451; border-radius: 4px; overflow: auto; white-space: pre-wrap; word-wrap: break-word; }
        .sql-display { width: 100%; min-height: 150px; margin-bottom: 10px; padding: 8px; box-sizing: border-box; font-family: 'Consolas', monospace; font-size: 14px; background: #282c34; color: #abb2bf; border: 1px solid #3e4451; border-radius: 4px; white-space: pre-wrap; overflow-x: auto; }
        .sql-keyword { color: #c678dd; font-weight: bold; }
        .sql-function { color: #61afef; }
        .sql-string { color: #98c379; }
        .sql-number { color: #d19a66; }
        .sql-comment { color: #5c6370; font-style: italic; }
        .sql-table { color: #e5c07b; }
        .sql-field { color: #61afef; }
        .sql-operator { color: #abb2bf; }
        .sql-parenthesis { color: #abb2bf; }
    </style>
</head>
<body>
    <div class="container">
        <div class="left-panel">
            <h3>📁 导入数据</h3>
            <div class="upload-area" onclick="document.getElementById('file-input').click()">
                <input type="file" id="file-input" accept=".csv,.xlsx,.xls" style="display:none">
                <div>📥 点击选择文件</div>
                <div style="font-size: 12px; color: #666;">或拖放到此处</div>
                <div style="font-size: 11px; color: #999;">.csv .xlsx .xls</div>
            </div>
            <div id="import-status"></div>
            
            <div id="csv-settings" style="display: none; margin-top: 10px;">
                <h4>CSV设置</h4>
                <input type="text" id="table-name" placeholder="表名"><br>
                <input type="number" id="header-row" value="0" placeholder="表头行">
                <input type="number" id="content-row" value="1" placeholder="内容行"><br>
                <button class="btn" onclick="importCSV()">导入CSV</button>
            </div>
            
            <div id="excel-settings" style="display: none; margin-top: 10px;">
                <h4>Excel设置</h4>
                <div id="sheet-list"></div>
                <button class="btn" onclick="importExcel()">导入Excel</button>
            </div>
            
            <hr>
            <h3>📋 数据资产</h3>
            <div id="table-list"></div>
        </div>
        
        <div class="middle-panel">
            <h3>SQL编辑器</h3>
            
            <div class="mode-tabs">
                <button class="mode-tab active" onclick="switchMode('code')">代码模式</button>
                <button class="mode-tab" onclick="switchMode('canvas')">画布模式</button>
                <button class="mode-tab" onclick="switchMode('test')">测试</button>
            </div>
            
            <div id="code-mode">
                <div class="sql-editor-container">
                    <div class="sql-editor" contenteditable="true" id="sql-input" spellcheck="false" oninput="onSQLInput()">SELECT * FROM </div>
                </div>
                <button class="btn btn-success" onclick="runSQL()">▶️ 运行</button>
                <button class="btn" onclick="parseSQLToCanvas()" style="margin-left: 5px;">🔄 解析到画布</button>
            </div>
            
            <div id="canvas-mode" style="display: none;">
                <p style="font-size: 12px; color: #666;">💡 点击数据资产中的表添加到画布。悬停在节点上查看连接点。</p>
                <div class="canvas-container" id="canvas-container">
                    <div class="canvas-inner" id="canvas-inner">
                        <svg class="canvas-svg" id="canvas-svg">
                            <defs>
                                <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                                    <polygon points="0 0, 10 3.5, 0 7" fill="#4285f4"/>
                                </marker>
                            </defs>
                        </svg>
                        <div id="canvas-hint" class="canvas-hint">
                            <div class="hint-icon">📋</div>
                            <div>点击数据资产中的表</div>
                            <div style="font-size: 11px;">添加到画布</div>
                        </div>
                    </div>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 8px; align-items: center;">
                    <button class="btn" onclick="clearCanvas()">🗑️ 清空</button>
                    <button class="btn" onclick="saveLayout()">💾 保存</button>
                    <button class="btn" onclick="loadLayout()">📂 加载</button>
                    <button class="btn btn-success" onclick="runCanvasQuery()">▶️ 执行查询</button>
                    <div style="display: flex; gap: 4px; margin-left: auto;">
                        <button class="btn btn-sm" onclick="zoomCanvas(0.1)">+</button>
                        <button class="btn btn-sm" onclick="zoomCanvas(-0.1)">-</button>
                        <button class="btn btn-sm" onclick="resetZoom()">1:1</button>
                    </div>
                    <span style="font-size: 11px; color: #666; margin-left: 10px;">提示: 点击连接点创建关联 | 双击表设为主表</span>
                </div>
                
                <div class="data-panel" id="data-panel">
                    <div class="panel-header">
                        <span class="panel-title" id="panel-title">表数据</span>
                        <span class="close-btn" onclick="hideDataPanel()">✕</span>
                    </div>
                    <div id="data-results" style="max-height: 200px; overflow-y: auto;"></div>
                    <div class="data-pagination" id="data-pagination">
                        <button id="data-prev-btn" onclick="prevDataPage()" disabled>◀️ 上一页</button>
                        <span id="data-page-info">第 1 页 / 共 1 页</span>
                        <button id="data-next-btn" onclick="nextDataPage()" disabled>下一页 ▶️</button>
                    </div>
                </div>
            </div>
            
            <div id="test-mode" style="display: none;">
                <h4>测试与验证</h4>
                <button class="btn" onclick="runTests()">运行所有测试</button>
                <div id="test-results" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        <div class="resizer" id="resizer" onmousedown="startResize(event)"></div>
        
    </div>

    <div class="bottom-drawer" id="bottom-drawer">
        <div class="drawer-resizer" id="drawer-resizer"></div>
        <div class="drawer-header">
            <span class="drawer-title" id="drawer-title">结果：就绪</span>
            <span class="drawer-toggle" id="drawer-toggle" onclick="toggleDrawer()">▼</span>
            <div class="drawer-pagination" id="pagination" style="display: none;">
                <button class="btn btn-sm" onclick="prevPage()" id="prev-btn">◀ 上一页</button>
                <span id="page-info">第 1 页 / 共 1 页</span>
                <button class="btn btn-sm" onclick="nextPage()" id="next-btn">下一页 ▶</button>
            </div>
        </div>
        <div class="drawer-content" id="drawer-content">
            <div class="drawer-actions">
                <button onclick="showColumnSelector()">⚙️ 列设置</button>
                <select id="export-format">
                    <option value="csv">CSV</option>
                    <option value="sql">SQL脚本</option>
                </select>
                <button class="btn btn-sm" onclick="exportData()">下载</button>
            </div>
            <div id="result-stats"></div>
            <div id="result-table" style="max-height: calc(100% - 50px); overflow-y: auto;"></div>
        </div>
    </div>

    <div class="modal-backdrop" id="modal-backdrop" onclick="closeModal()"></div>
    <div class="modal" id="modal">
        <h3 id="modal-title"></h3>
        <div id="modal-content"></div>
        <button class="btn" onclick="closeModal()">关闭</button>
    </div>

    <div class="column-select-modal" id="column-select-modal">
        <div class="column-select-header">
            <h3>列可见性设置</h3>
            <div class="column-select-actions">
                <button onclick="resetColumnVisibility()">恢复默认</button>
                <button onclick="showAllColumns()">全部显示</button>
                <button onclick="hideAllColumns()">全部隐藏</button>
                <button onclick="closeColumnSelector()">关闭</button>
            </div>
        </div>
        <div id="column-list"></div>
    </div>

    <script>
        let currentPage = 1;
        let totalPages = 1;
        let currentSql = '';
        const pageSize = 50;

        let canvasState = { tables: {}, joins: [] };
        let draggingNode = null;
        let dragOffset = { x: 0, y: 0 };
        
        function escapeQuotes(str) {
            return str.split("'").join("\\\\'");
        }

        async function loadTables() {
            let response = await fetch('/api/tables');
            let tables = await response.json();
            let list = document.getElementById('table-list');
            list.innerHTML = tables.length ? tables.map(t => `<div style="padding: 4px; cursor: pointer;" onclick="selectTable('${escapeQuotes(t)}')">📊 ${t}</div>`).join('') : '<div style="color: #999;">No tables</div>';
        }

        function selectTable(name) {
            const mode = document.querySelector('.mode-tab.active').textContent;
            if (mode === '画布模式') {
                addTableToCanvas(name);
            } else {
                document.getElementById('sql-input').textContent = `SELECT * FROM ${name}`;
            }
        }

        function switchMode(mode) {
            document.querySelectorAll('.mode-tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');

            document.getElementById('code-mode').style.display = mode === 'code' ? 'block' : 'none';
            document.getElementById('canvas-mode').style.display = mode === 'canvas' ? 'block' : 'none';
            document.getElementById('test-mode').style.display = mode === 'test' ? 'block' : 'none';
        }

        function handleFileSelect(event) {
            let file = event.target.files[0];
            if (!file) return;
            
            let ext = file.name.split('.').pop().toLowerCase();
            if (ext === 'csv') {
                document.getElementById('table-name').value = file.name.replace('.csv', '');
                document.getElementById('csv-settings').style.display = 'block';
                document.getElementById('excel-settings').style.display = 'none';
            } else if (ext === 'xlsx' || ext === 'xls') {
                loadExcelSheets(file);
            }
        }

        async function loadExcelSheets(file) {
            let formData = new FormData();
            formData.append('file', file);
            let response = await fetch('/api/excel/sheets', { method: 'POST', body: formData });
            let sheets = await response.json();
            
            let list = document.getElementById('sheet-list');
            list.innerHTML = sheets.map(s => `<label><input type="checkbox" checked value="${s}"> ${s}</label><br>`).join('');
            document.getElementById('excel-settings').style.display = 'block';
            document.getElementById('csv-settings').style.display = 'none';
        }

        async function importCSV() {
            let file = document.getElementById('file-input').files[0];
            if (!file) return;
            
            let formData = new FormData();
            formData.append('file', file);
            formData.append('table_name', document.getElementById('table-name').value);
            formData.append('header_row', document.getElementById('header-row').value);
            formData.append('content_row', document.getElementById('content-row').value);
            
            let response = await fetch('/api/import/csv', { method: 'POST', body: formData });
            let result = await response.json();
            
            document.getElementById('import-status').innerHTML = result.success ? 
                `<div class="success">✓ ${result.message}</div>` : 
                `<div class="error">✗ ${result.message}</div>`;
            
            if (result.success) {
                loadTables();
                document.getElementById('csv-settings').style.display = 'none';
                document.getElementById('file-input').value = '';
            }
        }

        async function importExcel() {
            let file = document.getElementById('file-input').files[0];
            if (!file) return;
            
            let checkboxes = document.querySelectorAll('#sheet-list input:checked');
            let sheets = Array.from(checkboxes).map(c => c.value);
            
            let formData = new FormData();
            formData.append('file', file);
            formData.append('sheets', JSON.stringify(sheets));
            
            let response = await fetch('/api/import/excel', { method: 'POST', body: formData });
            let result = await response.json();
            
            document.getElementById('import-status').innerHTML = result.success ? 
                `<div class="success">✓ ${result.message}</div>` : 
                `<div class="error">✗ ${result.message}</div>`;
            
            if (result.success) {
                loadTables();
                document.getElementById('excel-settings').style.display = 'none';
                document.getElementById('file-input').value = '';
            }
        }

        async function runSQL(page = 1) {
            let sql = getSQLText();
            currentSql = sql;
            currentPage = page;
            
            let response = await fetch('/api/query', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ sql, page, page_size: pageSize, columns: visibleColumns })
            });
            let result = await response.json();
            
            if (result.success) {
                document.getElementById('result-stats').innerHTML = `Rows: ${result.total_rows} | Time: ${result.time.toFixed(2)}s`;
                document.getElementById('result-table').innerHTML = result.html;
                
                if (result.columns) {
                    allColumns = result.columns;
                    if (visibleColumns.length === 0) {
                        visibleColumns = [...allColumns];
                    }
                }
                
                totalPages = Math.ceil(result.total_rows / pageSize);
                document.getElementById('page-info').textContent = `Page ${currentPage} of ${totalPages}`;
                document.getElementById('pagination').style.display = totalPages > 1 ? 'flex' : 'none';
                document.getElementById('prev-btn').disabled = currentPage <= 1;
                document.getElementById('next-btn').disabled = currentPage >= totalPages;
                
                document.getElementById('drawer-title').textContent = `Results: ${result.total_rows} rows`;
                expandDrawer();
            } else {
                document.getElementById('result-stats').innerHTML = `<div class="error">Error: ${result.message}</div>`;
                document.getElementById('result-table').innerHTML = '';
                document.getElementById('pagination').style.display = 'none';
            }
        }

        function prevPage() {
            if (currentPage > 1) runSQL(currentPage - 1);
        }

        function nextPage() {
            if (currentPage < totalPages) runSQL(currentPage + 1);
        }

        async function exportData() {
            let format = document.getElementById('export-format').value;
            let sql = document.getElementById('sql-input').value;
            window.location.href = `/api/export/${format}?sql=${encodeURIComponent(sql)}`;
        }

        function showModal(title, content) {
            document.getElementById('modal-title').textContent = title;
            document.getElementById('modal-content').innerHTML = content;
            document.getElementById('modal').classList.add('active');
            document.getElementById('modal-backdrop').classList.add('active');
        }

        function closeModal() {
            document.getElementById('modal').classList.remove('active');
            document.getElementById('modal-backdrop').classList.remove('active');
        }

        function startResize(e) {
            e.preventDefault();
            document.addEventListener('mousemove', resize);
            document.addEventListener('mouseup', stopResize);
        }

        function resize(e) {
            const rightPanel = document.getElementById('right-panel');
            const container = document.querySelector('.container');
            const containerWidth = container.offsetWidth;
            const newWidth = containerWidth - e.clientX;
            
            if (newWidth > 200 && newWidth < 800) {
                rightPanel.style.width = newWidth + 'px';
            }
        }

        function stopResize() {
            document.removeEventListener('mousemove', resize);
            document.removeEventListener('mouseup', stopResize);
        }

        // Canvas Functions
        let connectingFrom = null;
        let connectingField = null;

        function addTableToCanvas(tableName) {
            const container = document.getElementById('canvas-container');
            const rect = container.getBoundingClientRect();
            const x = 50 + Math.random() * (rect.width - 280);
            const y = 50 + Math.random() * (rect.height - 200);

            const alias = generateAlias(tableName);
            canvasState.tables[alias] = {
                tableName: tableName,
                alias: alias,
                x: x,
                y: y,
                selectedFields: [],
                filters: []
            };

            document.getElementById('canvas-hint').style.display = 'none';
            renderCanvas();
            updateSQLFromCanvas();
        }

        function setMainTable(alias) {
            canvasState.mainTable = alias;
            renderCanvas();
            updateSQLFromCanvas();
            showToast('主表已设置为: ' + canvasState.tables[alias].tableName);
        }

        function showToast(message) {
            const toast = document.createElement('div');
            toast.style.cssText = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: #4285f4; color: white; padding: 10px 20px; border-radius: 4px; z-index: 2000; box-shadow: 2px 2px 10px rgba(0,0,0,0.2);';
            toast.textContent = message;
            document.body.appendChild(toast);
            setTimeout(() => { toast.remove(); }, 2000);
        }

        function generateAlias(tableName) {
            const timestamp = Date.now().toString(36);
            const random = Math.floor(Math.random() * 1000).toString(36);
            const base = tableName.toLowerCase().replace(new RegExp('[^a-z0-9]', 'g'), '');
            const prefix = base.length > 3 ? base.substring(0, 3) : base;
            const alias = prefix + '_' + timestamp + '_' + random;
            return alias.substring(0, 15);
        }

        function renderCanvas() {
            const container = document.getElementById('canvas-container');
            const svg = document.getElementById('canvas-svg');

            container.querySelectorAll('.canvas-table-node').forEach(n => n.remove());
            svg.querySelectorAll('path').forEach(p => p.remove());

            for (const [alias, table] of Object.entries(canvasState.tables)) {
                const node = createTableNode(alias, table);
                container.appendChild(node);
            }

            drawJoinLines();
        }

        function drawJoinLines() {
            const svg = document.getElementById('canvas-svg');

            canvasState.joins.forEach((join, index) => {
                const leftNode = document.getElementById('node-' + join.leftTable);
                const rightNode = document.getElementById('node-' + join.rightTable);

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
                path.setAttribute('data-join-index', index);

                path.addEventListener('click', function() {
                    cycleJoinType(index);
                });

                path.addEventListener('contextmenu', function(e) {
                    e.preventDefault();
                    removeJoin(index);
                });

                svg.appendChild(path);
            });
        }

        function cycleJoinType(index) {
            const joinTypes = ['INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN'];
            const join = canvasState.joins[index];
            const currentIdx = joinTypes.indexOf(join.joinType);
            join.joinType = joinTypes[(currentIdx + 1) % joinTypes.length];
            renderCanvas();
            updateSQLFromCanvas();
        }

        function removeJoin(index) {
            canvasState.joins.splice(index, 1);
            renderCanvas();
            updateSQLFromCanvas();
        }

        function createTableNode(alias, table) {
            const node = document.createElement('div');
            node.className = 'canvas-table-node';
            node.id = 'node-' + alias;
            node.style.left = table.x + 'px';
            node.style.top = table.y + 'px';

            const filterCount = table.filters.length > 0 ? `<span class="filter-count">${table.filters.length}</span>` : '';
            
            let filtersHtml = '';
            if (table.filters.length > 0) {
                filtersHtml = `<div class="node-filters">${table.filters.map((f, i) => 
                    `<div class="filter-item">${f.field} ${f.operator} ${f.value || 'NULL'}<span class="remove-filter" onclick="removeFilter('${escapeQuotes(alias)}', ${i})">✕</span></div>`
                ).join('')}</div>`;
            }

            const isMainTable = canvasState.mainTable === alias;
            const mainIndicator = isMainTable ? ' <span class="main-indicator">★</span>' : '';
            node.innerHTML = `<div class="node-header">${table.tableName}${mainIndicator}${filterCount}</div>` +
                `<div class="node-fields" id="fields-${alias}"></div>` +
                filtersHtml +
                `<div class="node-actions">` +
                `<button title="添加筛选条件">+ 筛选</button>` +
                `<button title="从画布移除表">移除</button></div>` +
                `<div class="connection-point top" title="点击开始连接"></div>` +
                `<div class="connection-point bottom" title="点击开始连接"></div>` +
                `<div class="connection-point left" title="点击开始连接"></div>` +
                `<div class="connection-point right" title="点击开始连接"></div>`;
            
            if (isMainTable) {
                node.classList.add('main-table');
            }

            node.addEventListener('mousedown', function(e) {
                if (e.target.classList.contains('node-header')) {
                    hideTableTooltip();
                    draggingNode = { alias: alias, node: node };
                    const rect = node.getBoundingClientRect();
                    dragOffset = { x: e.clientX - rect.left, y: e.clientY - rect.top };
                }
            });

            node.addEventListener('mouseenter', function(e) {
                if (!draggingNode) {
                    showTableTooltip(e, alias, table.tableName);
                }
            });

            node.addEventListener('mouseleave', function() {
                hideTableTooltip();
            });

            node.addEventListener('click', function(e) {
                if (!e.target.classList.contains('connection-point') && 
                    !e.target.classList.contains('remove-filter') &&
                    !e.target.closest('.node-actions')) {
                    loadTableData(table.tableName);
                }
            });

            node.addEventListener('dblclick', function(e) {
                if (!e.target.classList.contains('connection-point') &&
                    !e.target.closest('.node-actions')) {
                    setMainTable(alias);
                }
            });

            node.querySelectorAll('.connection-point').forEach(point => {
                point.addEventListener('click', function(e) {
                    e.stopPropagation();
                    handleConnectionPointClick(alias, point);
                });
            });

            node.querySelector('.node-actions button:first-child').addEventListener('click', function() {
                showFilterPanel(alias);
            });
            node.querySelector('.node-actions button:last-child').addEventListener('click', function() {
                removeNode(alias);
            });

            loadTableFields(alias, table.tableName);
            return node;
        }

        async function loadTableFields(alias, tableName) {
            const fieldsContainer = document.getElementById('fields-' + alias);
            if (!fieldsContainer) return;

            try {
                const timestamp = Date.now();
                const response = await fetch('/api/table/' + encodeURIComponent(tableName) + '?t=' + timestamp, {
                    method: 'GET',
                    headers: {
                        'Cache-Control': 'no-cache',
                        'Pragma': 'no-cache',
                    },
                });
                const data = await response.json();

                fieldsContainer.innerHTML = data.columns.map(col => {
                    const isSelected = canvasState.tables[alias].selectedFields.includes(col.column_name);
                    return `<div class="field-item ${isSelected ? 'selected' : ''}">` +
                        `<input type="checkbox" ${isSelected ? 'checked' : ''} onchange="toggleField('${escapeQuotes(alias)}', '${escapeQuotes(col.column_name)}')">` +
                        `<span>${col.column_name}</span></div>`;
                }).join('');
            } catch (err) {
                fieldsContainer.innerHTML = '<div style="color:red;font-size:11px">Failed to load</div>';
            }
        }

        function populateSelectWithTableFields(selectElement, tableName, callback) {
            selectElement.innerHTML = '<option value="">选择字段...</option>';
            
            const timestamp = Date.now();
            fetch('/api/table/' + encodeURIComponent(tableName) + '?t=' + timestamp)
                .then(r => r.json())
                .then(data => {
                    if (data && data.columns) {
                        data.columns.forEach(col => {
                            const opt = document.createElement('option');
                            opt.value = col.column_name;
                            opt.textContent = col.column_name;
                            selectElement.appendChild(opt);
                        });
                    }
                    if (callback) callback();
                })
                .catch(err => {
                    console.error('populateSelectWithTableFields error:', tableName, err);
                    if (callback) callback();
                });
        }

        function toggleField(alias, fieldName) {
            const table = canvasState.tables[alias];
            const idx = table.selectedFields.indexOf(fieldName);
            if (idx >= 0) {
                table.selectedFields.splice(idx, 1);
            } else {
                table.selectedFields.push(fieldName);
            }
            updateSQLFromCanvas();
        }

        function removeNode(alias) {
            delete canvasState.tables[alias];
            canvasState.joins = canvasState.joins.filter(j => j.leftTable !== alias && j.rightTable !== alias);
            
            document.querySelectorAll('.filter-panel').forEach(p => p.remove());
            
            if (Object.keys(canvasState.tables).length === 0) {
                document.getElementById('canvas-hint').style.display = 'block';
            }
            
            renderCanvas();
            updateSQLFromCanvas();
        }

        function removeFilter(alias, index) {
            canvasState.tables[alias].filters.splice(index, 1);
            renderCanvas();
            updateSQLFromCanvas();
        }
        
        // SQL Syntax Highlighting - simplified to avoid regex issues
        function highlightSQL(sql) {
            return sql; // Return plain text for now, no highlighting
        }
        
        // SQL Input Handler - no complex highlighting for now
        function onSQLInput() {
            // Just update content, no special handling
        }
        
        // Parse SQL to Canvas (simple parser)
        function parseSQLToCanvas() {
            const sqlEditor = document.getElementById('sql-input');
            const sql = sqlEditor.textContent.trim();
            
            if (!sql) {
                alert('请先输入SQL查询语句。');
                return;
            }
            
            alert('SQL解析到画布功能暂时不可用，请直接在画布模式中操作。');
        }

        function handleConnectionPointClick(alias, point) {
            if (!connectingFrom) {
                connectingFrom = { alias: alias, point: point, startX: event.clientX, startY: event.clientY };
                point.style.background = '#ff5722';
                point.style.transform = point.style.transform + ' scale(1.5)';
                
                document.addEventListener('mousemove', handleConnectionDrag);
                document.addEventListener('mouseup', handleConnectionDrop);
            } else if (connectingFrom.alias !== alias) {
                const fromAlias = connectingFrom.alias;
                const toAlias = alias;
                
                cancelConnection();
                showFieldSelector(fromAlias, toAlias);
            } else {
                cancelConnection();
            }
        }

        function handleConnectionDrop(e) {
            const targetPoint = findConnectionPointAt(e.clientX, e.clientY);
            
            if (targetPoint && connectingFrom && targetPoint.alias !== connectingFrom.alias) {
                showFieldSelector(connectingFrom.alias, targetPoint.alias);
            }
            
            cancelConnection();
        }

        function handleConnectionDrag(e) {
            if (!connectingFrom) return;
            
            const svg = document.getElementById('canvas-svg');
            const container = document.getElementById('canvas-container');
            const rect = container.getBoundingClientRect();
            
            svg.querySelectorAll('.temp-line').forEach(p => p.remove());
            
            const x1 = connectingFrom.point.getBoundingClientRect().left + 4 - rect.left;
            const y1 = connectingFrom.point.getBoundingClientRect().top + 4 - rect.top;
            const x2 = e.clientX - rect.left;
            const y2 = e.clientY - rect.top;
            
            const midX = (x1 + x2) / 2;
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('d', `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`);
            path.setAttribute('class', 'join-line temp-line');
            path.setAttribute('stroke-dasharray', '5,5');
            svg.appendChild(path);
            
            document.querySelectorAll('.connection-point').forEach(p => {
                if (p !== connectingFrom.point) {
                    p.style.background = '#4285f4';
                    p.style.transform = p.style.transform.replace(' scale(1.5)', '');
                }
            });
            
            const targetPoint = findConnectionPointAt(e.clientX, e.clientY);
            if (targetPoint && targetPoint.alias !== connectingFrom.alias) {
                targetPoint.point.style.background = '#ff5722';
                targetPoint.point.style.transform = targetPoint.point.style.transform.replace(' scale(1.5)', '') + ' scale(1.5)';
            }
        }

        function findConnectionPointAt(clientX, clientY) {
            const points = document.querySelectorAll('.connection-point');
            for (const point of points) {
                const rect = point.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                const distance = Math.sqrt(Math.pow(clientX - centerX, 2) + Math.pow(clientY - centerY, 2));
                if (distance < 20) {
                    const node = point.closest('.canvas-table-node');
                    const alias = node.id.replace('node-', '');
                    return { point: point, alias: alias };
                }
            }
            return null;
        }

        function cancelConnection() {
            if (connectingFrom) {
                connectingFrom.point.style.background = '#4285f4';
                connectingFrom.point.style.transform = connectingFrom.point.style.transform.replace(' scale(1.5)', '');
                connectingFrom = null;
            }
            document.removeEventListener('mousemove', handleConnectionDrag);
            document.removeEventListener('mouseup', handleConnectionDrop);
            
            document.querySelectorAll('.temp-line').forEach(p => p.remove());
            document.querySelectorAll('.connection-point').forEach(p => {
                p.style.background = '#4285f4';
                p.style.transform = p.style.transform.replace(' scale(1.5)', '');
            });
        }

        async function showFieldSelector(fromAlias, toAlias) {
            const existing = document.querySelector('.filter-panel');
            if (existing) existing.remove();

            const panel = document.createElement('div');
            panel.className = 'filter-panel';
            panel.innerHTML = '<h4>创建关联</h4>' +
                '<select id="from-field"><option value="">源字段...</option></select>' +
                '<select id="to-field"><option value="">目标字段...</option></select>' +
                '<select id="join-type">' +
                '<option value="INNER JOIN">INNER JOIN</option>' +
                '<option value="LEFT JOIN">LEFT JOIN</option>' +
                '<option value="RIGHT JOIN">RIGHT JOIN</option>' +
                '<option value="FULL JOIN">FULL JOIN</option>' +
                '</select>' +
                '<button class="btn btn-sm" id="create-join-btn">✓ 创建</button>' +
                '<button class="btn btn-sm" id="cancel-join-btn">✕ 取消</button>';

            document.getElementById('canvas-container').appendChild(panel);

            await new Promise(resolve => {
                populateSelectWithTableFields(panel.querySelector('#from-field'),
                    canvasState.tables[fromAlias].tableName, resolve);
            });
            await new Promise(resolve => {
                populateSelectWithTableFields(panel.querySelector('#to-field'),
                    canvasState.tables[toAlias].tableName, resolve);
            });

            panel.querySelector('#create-join-btn').addEventListener('click', function() {
                const fromField = panel.querySelector('#from-field').value;
                const toField = panel.querySelector('#to-field').value;
                const joinType = panel.querySelector('#join-type').value;

                if (!fromField || !toField) {
                    return;
                }

                canvasState.joins.push({
                    leftTable: fromAlias,
                    leftField: fromField,
                    rightTable: toAlias,
                    rightField: toField,
                    joinType: joinType
                });

                panel.remove();
                renderCanvas();
                updateSQLFromCanvas();
            });

            panel.querySelector('#cancel-join-btn').addEventListener('click', function() {
                panel.remove();
            });

            const fromNode = document.getElementById('node-' + fromAlias);
            const fromRect = fromNode.getBoundingClientRect();
            const containerRect = document.getElementById('canvas-container').getBoundingClientRect();
            panel.style.left = (fromRect.right - containerRect.left + 10) + 'px';
            panel.style.top = (fromRect.top - containerRect.top) + 'px';
        }

        function showFilterPanel(alias) {
            const existing = document.querySelector('.filter-panel');
            if (existing) existing.remove();

            const panel = document.createElement('div');
            panel.className = 'filter-panel';
            panel.innerHTML = '<h4>筛选条件</h4>' +
                '<select id="filter-field"><option value="">选择字段...</option></select>' +
                '<select id="filter-operator">' +
                '<option value="=">=</option>' +
                '<option value="!=">!=</option>' +
                '<option value="<"><</option>' +
                '<option value="<="><=</option>' +
                '<option value=">">></option>' +
                '<option value=">=">>=</option>' +
                '<option value="LIKE">LIKE</option>' +
                '<option value="NOT LIKE">NOT LIKE</option>' +
                '<option value="IN">IN</option>' +
                '<option value="NOT IN">NOT IN</option>' +
                '<option value="IS NULL">IS NULL</option>' +
                '<option value="IS NOT NULL">IS NOT NULL</option>' +
                '<option value="BETWEEN">BETWEEN</option>' +
                '</select>' +
                '<input type="text" id="filter-value" placeholder="Value (comma-separate for IN)">' +
                '<button class="btn btn-sm" id="apply-filter-btn">应用</button>' +
                '<button class="btn btn-sm" id="cancel-filter-btn">取消</button>';
            
            panel.querySelector('#apply-filter-btn').addEventListener('click', function() {
                applyFilter(alias);
            });
            panel.querySelector('#cancel-filter-btn').addEventListener('click', function() {
                panel.remove();
            });

            const table = canvasState.tables[alias];
            populateSelectWithTableFields(panel.querySelector('#filter-field'), table.tableName);

            const node = document.getElementById('node-' + alias);
            const rect = node.getBoundingClientRect();
            const containerRect = document.getElementById('canvas-container').getBoundingClientRect();
            panel.style.left = (rect.right - containerRect.left + 10) + 'px';
            panel.style.top = (rect.top - containerRect.top) + 'px';

            document.getElementById('canvas-container').appendChild(panel);
        }

        function applyFilter(alias) {
            const field = document.querySelector('#filter-field').value;
            const operator = document.querySelector('#filter-operator').value;
            const value = document.querySelector('#filter-value').value;

            if (!field) return;

            canvasState.tables[alias].filters.push({ field: field, operator: operator, value: value });
            document.querySelector('.filter-panel').remove();
            renderCanvas();
            updateSQLFromCanvas();
        }

        function clearCanvas() {
            canvasState = { tables: {}, joins: [] };
            document.getElementById('canvas-hint').style.display = 'block';
            renderCanvas();
            updateSQLFromCanvas();
        }

        // Canvas zoom functions
        let currentZoom = 1.0;
        const MIN_ZOOM = 0.5;
        const MAX_ZOOM = 2.0;

        function zoomCanvas(delta) {
            currentZoom = Math.min(Math.max(MIN_ZOOM, currentZoom + delta), MAX_ZOOM);
            applyZoom();
        }

        function resetZoom() {
            currentZoom = 1.0;
            applyZoom();
        }

        let canvasOffsetX = 0;
        let canvasOffsetY = 0;
        let isDraggingCanvas = false;
        let dragStartX = 0;
        let dragStartY = 0;
        let lastOffsetX = 0;
        let lastOffsetY = 0;

        function applyZoom() {
            const canvasInner = document.getElementById('canvas-inner');
            canvasInner.style.transform = 'translate(' + canvasOffsetX + 'px, ' + canvasOffsetY + 'px) scale(' + currentZoom + ')';
        }

        function initCanvasDrag() {
            const container = document.getElementById('canvas-container');
            
            container.addEventListener('mousedown', function(e) {
                if (e.target === container || e.target.classList.contains('canvas-inner') || e.target.classList.contains('canvas-svg')) {
                    isDraggingCanvas = true;
                    dragStartX = e.clientX;
                    dragStartY = e.clientY;
                    lastOffsetX = canvasOffsetX;
                    lastOffsetY = canvasOffsetY;
                    e.preventDefault();
                }
            });
            
            container.addEventListener('wheel', function(e) {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.1 : 0.1;
                zoomCanvas(delta);
            }, { passive: false });
            
            document.addEventListener('mousemove', function(e) {
                if (isDraggingCanvas) {
                    canvasOffsetX = lastOffsetX + (e.clientX - dragStartX);
                    canvasOffsetY = lastOffsetY + (e.clientY - dragStartY);
                    applyZoom();
                }
            });
            
            document.addEventListener('mouseup', function() {
                isDraggingCanvas = false;
            });
        }

        document.addEventListener('DOMContentLoaded', initCanvasDrag);

        // Canvas layout save/load functions
        const STORAGE_KEY = 'canvas-layout';

        function saveLayout() {
            const layoutData = {
                canvasState: canvasState,
                zoom: currentZoom,
                timestamp: new Date().toISOString()
            };
            
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(layoutData));
                alert('Layout saved successfully!');
            } catch (error) {
                alert('Failed to save layout: ' + error.message);
            }
        }

        function loadLayout() {
            try {
                const savedData = localStorage.getItem(STORAGE_KEY);
                
                if (!savedData) {
                    alert('No saved layout found!');
                    return;
                }
                
                const layoutData = JSON.parse(savedData);
                
                // Restore canvas state
                canvasState = layoutData.canvasState || { tables: {}, joins: [] };
                
                // Restore zoom
                if (layoutData.zoom) {
                    currentZoom = layoutData.zoom;
                    applyZoom();
                }
                
                // Re-render canvas
                renderCanvas();
                updateSQLFromCanvas();
                
                // Update hint visibility
                document.getElementById('canvas-hint').style.display = 
                    Object.keys(canvasState.tables).length === 0 ? 'block' : 'none';
                
                alert('Layout loaded successfully!');
            } catch (error) {
                alert('Failed to load layout: ' + error.message);
            }
        }

        function runCanvasQuery() {
            const sql = generateSQLFromCanvas();
            if (!sql) return;
            document.getElementById('sql-input').value = sql;
            runSQL();
        }

        function generateSQLFromCanvas() {
            if (Object.keys(canvasState.tables).length === 0) return '';

            const selectParts = [];
            const whereParts = [];

            for (const [alias, table] of Object.entries(canvasState.tables)) {
                if (table.selectedFields.length > 0) {
                    table.selectedFields.forEach(f => selectParts.push(alias + '.' + f));
                } else {
                    selectParts.push(alias + '.*');
                }

                table.filters.forEach(f => {
                    whereParts.push(formatCondition(alias, f.field, f.operator, f.value));
                });
            }

            const selectClause = 'SELECT ' + (selectParts.length > 0 ? selectParts.join(', ') : '*');
            
            let mainAlias = canvasState.mainTable || Object.keys(canvasState.tables)[0];
            
            if (!mainAlias || !canvasState.tables[mainAlias]) {
                mainAlias = Object.keys(canvasState.tables)[0];
            }
            
            const mainTable = canvasState.tables[mainAlias];
            if (!mainTable) return '';
            
            let fromClause = 'FROM ' + mainTable.tableName + ' AS ' + mainAlias;

            if (canvasState.joins.length > 0) {
                const addedTables = new Set([mainAlias]);
                let joinsAdded = true;
                
                while (joinsAdded) {
                    joinsAdded = false;
                    canvasState.joins.forEach(join => {
                        const rightTable = canvasState.tables[join.rightTable];
                        if (!rightTable) return;
                        
                        if (addedTables.has(join.leftTable) && !addedTables.has(join.rightTable)) {
                            fromClause += ' ' + join.joinType + ' ' + rightTable.tableName + ' AS ' + join.rightTable + ' ON ' + join.leftTable + '.' + join.leftField + ' = ' + join.rightTable + '.' + join.rightField;
                            addedTables.add(join.rightTable);
                            joinsAdded = true;
                        }
                    });
                }
            }

            const whereClause = whereParts.length > 0 ? ' WHERE ' + whereParts.join(' AND ') : '';

            return [selectClause, fromClause, whereClause].join(' ');
        }

        function formatCondition(alias, field, operator, value) {
            if (operator === 'IS NULL' || operator === 'IS NOT NULL') {
                return alias + '.' + field + ' ' + operator;
            } else if (operator === 'IN' || operator === 'NOT IN') {
                const values = value.split(',').map(v => "'" + v.trim() + "'").join(', ');
                return alias + '.' + field + ' ' + operator + ' (' + values + ')';
            } else if (operator === 'BETWEEN') {
                const parts = value.split(',').map(v => v.trim());
                if (parts.length >= 2) {
                    return alias + '.' + field + ' BETWEEN ' + "'" + parts[0] + "' AND '" + parts[1] + "'";
                }
                return alias + '.' + field + " BETWEEN '" + value + "' AND ''";
            }
            return alias + '.' + field + ' ' + operator + " '" + value + "'";
        }

        function updateSQLFromCanvas() {
            const sql = generateSQLFromCanvas();
            const sqlEditor = document.getElementById('sql-input');
            sqlEditor.innerHTML = highlightSQL(sql);
        }
        
        function getSQLText() {
            const sqlEditor = document.getElementById('sql-input');
            return sqlEditor.textContent;
        }

        document.addEventListener('mousemove', function(e) {
            if (draggingNode) {
                const container = document.getElementById('canvas-container');
                const rect = container.getBoundingClientRect();
                const x = e.clientX - rect.left - dragOffset.x;
                const y = e.clientY - rect.top - dragOffset.y;

                draggingNode.node.style.left = Math.max(0, Math.min(x, rect.width - 150)) + 'px';
                draggingNode.node.style.top = Math.max(0, Math.min(y, rect.height - 100)) + 'px';

                canvasState.tables[draggingNode.alias].x = parseInt(draggingNode.node.style.left);
                canvasState.tables[draggingNode.alias].y = parseInt(draggingNode.node.style.top);

                renderCanvas();
            }
        });

        document.addEventListener('mouseup', function() {
            draggingNode = null;
        });

        let tooltipData = {};
        let currentTableDataPage = 1;
        let currentTableDataTotalPages = 1;
        let currentTableDataName = '';
        let tooltipTimeout = null;
        let currentTooltipTable = null;

        async function showTableTooltip(e, alias, tableName) {
            currentTooltipTable = tableName;
            
            tooltipTimeout = setTimeout(async function() {
                if (draggingNode) return;
                
                if (!tooltipData[tableName]) {
                    const response = await fetch('/api/table/' + encodeURIComponent(tableName) + '?t=' + Date.now());
                    const data = await response.json();
                    tooltipData[tableName] = data.columns || [];
                }

                const columns = tooltipData[tableName];
                if (columns.length === 0) return;

                let tooltip = document.getElementById('table-tooltip');
                if (!tooltip) {
                    tooltip = document.createElement('div');
                    tooltip.id = 'table-tooltip';
                    tooltip.className = 'table-tooltip';
                    document.body.appendChild(tooltip);
                }

                let html = `<div class="tooltip-header">${tableName}</div><div class="tooltip-content">`;
                columns.forEach(col => {
                    html += `<div class="tooltip-row"><span class="tooltip-field">${col.column_name}</span><span class="tooltip-type">${col.data_type}</span></div>`;
                });
                html += `</div>`;
                tooltip.innerHTML = html;

                tooltip.style.left = (e.clientX + 15) + 'px';
                tooltip.style.top = (e.clientY + 15) + 'px';
                tooltip.classList.add('visible');
            }, 500);
        }

        function hideTableTooltip() {
            if (tooltipTimeout) {
                clearTimeout(tooltipTimeout);
                tooltipTimeout = null;
            }
            const tooltip = document.getElementById('table-tooltip');
            if (tooltip) {
                tooltip.classList.remove('visible');
            }
        }

        async function loadTableData(tableName) {
            currentTableDataName = tableName;
            currentTableDataPage = 1;
            
            const response = await fetch('/api/table/data/' + encodeURIComponent(tableName) + '?page=1&page_size=50');
            const result = await response.json();

            if (result.success) {
                document.getElementById('panel-title').textContent = 'Table: ' + tableName;
                document.getElementById('data-results').innerHTML = result.html;
                
                currentTableDataTotalPages = Math.ceil(result.total_rows / 50);
                document.getElementById('data-page-info').textContent = `Page ${currentTableDataPage} of ${currentTableDataTotalPages}`;
                document.getElementById('data-prev-btn').disabled = currentTableDataPage <= 1;
                document.getElementById('data-next-btn').disabled = currentTableDataPage >= currentTableDataTotalPages;
                
                document.getElementById('data-panel').classList.add('visible');
            }
        }

        function hideDataPanel() {
            document.getElementById('data-panel').classList.remove('visible');
        }

        let visibleColumns = [];
        let allColumns = [];
        let isDrawerExpanded = false;

        function toggleDrawer() {
            const drawer = document.getElementById('bottom-drawer');
            const toggle = document.getElementById('drawer-toggle');
            
            if (isDrawerExpanded) {
                drawer.style.height = '100px';
                toggle.textContent = '▼';
                isDrawerExpanded = false;
            } else {
                drawer.style.height = '400px';
                toggle.textContent = '▲';
                isDrawerExpanded = true;
            }
        }

        function expandDrawer() {
            const drawer = document.getElementById('bottom-drawer');
            const toggle = document.getElementById('drawer-toggle');
            drawer.style.height = '400px';
            toggle.textContent = '▲';
            isDrawerExpanded = true;
        }

        function initDrawerResize() {
            const resizer = document.getElementById('drawer-resizer');
            const drawer = document.getElementById('bottom-drawer');
            let isResizing = false;
            
            resizer.addEventListener('mousedown', function(e) {
                isResizing = true;
                document.addEventListener('mousemove', onDrawerResize);
                document.addEventListener('mouseup', stopDrawerResize);
                e.preventDefault();
            });
            
            function onDrawerResize(e) {
                if (!isResizing) return;
                
                const containerHeight = window.innerHeight;
                const newHeight = containerHeight - e.clientY;
                
                if (newHeight >= 100 && newHeight <= containerHeight - 50) {
                    drawer.style.height = newHeight + 'px';
                    isDrawerExpanded = newHeight > 100;
                }
            }
            
            function stopDrawerResize() {
                isResizing = false;
                document.removeEventListener('mousemove', onDrawerResize);
                document.removeEventListener('mouseup', stopDrawerResize);
            }
        }

        document.addEventListener('DOMContentLoaded', initDrawerResize);

        function showColumnSelector() {
            const modal = document.getElementById('column-select-modal');
            modal.classList.add('active');
            updateColumnSelectorUI();
        }

        function updateColumnSelectorUI() {
            let html = '';
            allColumns.forEach(col => {
                const isVisible = visibleColumns.includes(col);
                html += `<div class="column-item">
                    <span class="column-name">${col}</span>
                    <button class="${isVisible ? 'hide-btn' : 'show-btn'}" onclick="toggleColumn('${escapeQuotes(col)}')">
                        ${isVisible ? '✕ 隐藏' : '✓ 显示'}
                    </button>
                </div>`;
            });
            document.getElementById('column-list').innerHTML = html;
        }

        function closeColumnSelector() {
            document.getElementById('column-select-modal').classList.remove('active');
        }

        function toggleColumn(col) {
            const idx = visibleColumns.indexOf(col);
            if (idx >= 0) {
                visibleColumns.splice(idx, 1);
            } else {
                visibleColumns.push(col);
            }
            updateColumnSelectorUI();
            updateResultTableColumns();
        }

        function resetColumnVisibility() {
            visibleColumns = [...allColumns];
            updateColumnSelectorUI();
            updateResultTableColumns();
        }

        function showAllColumns() {
            visibleColumns = [...allColumns];
            updateColumnSelectorUI();
            updateResultTableColumns();
        }

        function hideAllColumns() {
            visibleColumns = [];
            updateColumnSelectorUI();
            updateResultTableColumns();
        }

        function updateResultTableColumns() {
            const table = document.querySelector('#result-table table');
            if (!table) return;
            
            const headers = table.querySelectorAll('th');
            const rows = table.querySelectorAll('tr');
            
            headers.forEach((th, idx) => {
                const colName = th.textContent.trim();
                const isVisible = visibleColumns.includes(colName);
                th.style.display = isVisible ? '' : 'none';
                
                rows.forEach(row => {
                    const cell = row.querySelectorAll('td')[idx];
                    if (cell) {
                        cell.style.display = isVisible ? '' : 'none';
                    }
                });
            });
        }

        async function prevDataPage() {
            if (currentTableDataPage > 1) {
                currentTableDataPage--;
                await loadTableDataPage(currentTableDataName, currentTableDataPage);
            }
        }

        async function nextDataPage() {
            if (currentTableDataPage < currentTableDataTotalPages) {
                currentTableDataPage++;
                await loadTableDataPage(currentTableDataName, currentTableDataPage);
            }
        }

        async function loadTableDataPage(tableName, page) {
            const response = await fetch('/api/table/data/' + encodeURIComponent(tableName) + '?page=' + page + '&page_size=50');
            const result = await response.json();

            if (result.success) {
                document.getElementById('data-results').innerHTML = result.html;
                document.getElementById('data-page-info').textContent = `Page ${page} of ${currentTableDataTotalPages}`;
                document.getElementById('data-prev-btn').disabled = page <= 1;
                document.getElementById('data-next-btn').disabled = page >= currentTableDataTotalPages;
            }
        }

        async function runTests() {
            let response = await fetch('/api/tests/run', { method: 'POST' });
            let result = await response.json();

            let html = '<table><tr><th>测试</th><th>状态</th><th>消息</th><th>时长</th></tr>';
            result.results.forEach(r => {
                html += `<tr><td>${r.name}</td><td style="color:${r.passed ? 'green' : 'red'}">` +
                    (r.passed ? '✓ 通过' : '✗ 失败') + `</td><td>${r.message}</td><td>${r.duration.toFixed(3)}秒</td></tr>`;
            });
            html += '</table>';
            html += `<p><strong>总结:</strong> ${result.passed}/${result.total} 通过 (${result.success_rate.toFixed(1)}%)</p>`;

            document.getElementById('test-results').innerHTML = html;
        }

        document.getElementById('file-input').addEventListener('change', handleFileSelect);

        loadTables();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/tables')
def get_tables():
    tables = db_manager.get_tables()
    unique_tables = list(dict.fromkeys(tables))
    return jsonify(unique_tables)

@app.route('/api/table/<name>')
def get_table_info(name):
    import urllib.parse
    decoded_name = urllib.parse.unquote(name)
    
    try:
        columns = db_manager.get_table_columns(decoded_name)
        rows = db_manager.get_row_count(decoded_name)
        
        if columns is None:
            columns = []
        
        response = jsonify({'columns': columns, 'rows': rows})
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
    except Exception as e:
        return jsonify({'error': str(e), 'columns': [], 'rows': 0}), 500

@app.route('/api/table/data/<name>')
def get_table_data(name):
    import urllib.parse
    decoded_name = urllib.parse.unquote(name)
    
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        offset = (page - 1) * page_size
        
        total_rows = db_manager.get_row_count(decoded_name)
        df = db_manager.fetch_df(f'SELECT * FROM "{decoded_name}" LIMIT {page_size} OFFSET {offset}')
        
        if df.empty:
            html = '<p>No data found</p>'
        else:
            html = '<table class="data-table"><tr>'
            for col in df.columns:
                html += f'<th>{col}</th>'
            html += '</tr>'
            
            for _, row in df.iterrows():
                html += '<tr>'
                for val in row:
                    html += f'<td>{val}</td>'
                html += '</tr>'
            html += '</table>'
        
        return jsonify({'success': True, 'html': html, 'total_rows': total_rows})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/excel/sheets', methods=['POST'])
def excel_sheets():
    try:
        file = request.files['file']
        xls = pd.ExcelFile(file)
        return jsonify(xls.sheet_names)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/import/csv', methods=['POST'])
def import_csv():
    try:
        file = request.files['file']
        table_name = request.form['table_name']
        header_row = int(request.form['header_row'])
        content_row = int(request.form['content_row'])

        if not table_name:
            return jsonify({'success': False, 'message': 'Table name is required'})

        skip_rows = content_row - (header_row + 1)
        if skip_rows < 0:
            skip_rows = 0

        file.seek(0)
        df = pd.read_csv(file, header=header_row, skiprows=skip_rows if skip_rows > 0 else None, dtype=str)

        if df.empty or len(df.columns) == 0:
            return jsonify({'success': False, 'message': 'DataFrame is empty or has no columns'})

        db_manager.save_df(df, table_name)

        return jsonify({'success': True, 'message': f'CSV imported: {table_name} ({len(df)} rows)'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/import/excel', methods=['POST'])
def import_excel():
    try:
        file = request.files['file']
        file_name = file.filename
        base_name = os.path.splitext(file_name)[0]
        sheets = request.form.getlist('sheets')

        if not sheets:
            xls = pd.ExcelFile(file)
            sheets = xls.sheet_names
        else:
            import json
            sheets = json.loads(sheets[0])

        imported_count = 0
        
        for sheet_name in sheets:
            existing_tables = db_manager.get_tables()
            
            file.seek(0)
            df = pd.read_excel(file, sheet_name=sheet_name, dtype=str)

            if df.empty or len(df.columns) == 0:
                continue

            base_table_name = sheet_name.lower().replace(' ', '_') + '_' + base_name.lower().replace(' ', '_')
            table_name = base_table_name
            suffix = 1
            
            while table_name in existing_tables:
                table_name = f"{base_table_name}_{suffix}"
                suffix += 1
            
            db_manager.save_df(df, table_name)
            imported_count += 1

        return jsonify({'success': True, 'message': f'Excel imported: {imported_count} sheet(s) from {file_name}'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/query', methods=['POST'])
def query():
    try:
        sql = request.json['sql']
        page = request.json.get('page', 1)
        page_size = request.json.get('page_size', 50)
        visible_columns = request.json.get('columns', [])

        start_time = time.time()
        df = db_manager.fetch_df(sql)
        elapsed = time.time() - start_time

        all_columns = df.columns.tolist()
        
        if visible_columns and len(visible_columns) > 0:
            valid_columns = [col for col in visible_columns if col in all_columns]
            df = df[valid_columns]

        total_rows = len(df)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_df = df.iloc[start_idx:end_idx]

        html = generate_table_html(paginated_df)
        return jsonify({'success': True, 'total_rows': total_rows, 'rows': len(paginated_df), 'time': elapsed, 'html': html, 'columns': all_columns})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def generate_table_html(df):
    if df.empty:
        return '<p>No data found</p>'
    
    html = '<table class="data-table"><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr>'
    
    for _, row in df.iterrows():
        html += '<tr>'
        for val in row:
            cell_val = str(val) if val is not None else ''
            html += f'<td>{cell_val}<span class="cell-tooltip">{cell_val}</span></td>'
        html += '</tr>'
    html += '</table>'
    
    return html

@app.route('/api/tests/run', methods=['POST'])
def run_tests():
    try:
        test_runner = TestRunner(db_manager)
        test_runner.run_all_tests()
        return jsonify(test_runner.get_summary())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/csv')
def export_csv():
    try:
        sql = request.args['sql']
        df = db_manager.fetch_df(sql)
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return send_file(io.BytesIO(buffer.getvalue().encode()), mimetype='text/csv', download_name='result.csv')
    except Exception as e:
        return str(e), 500

@app.route('/api/export/sql')
def export_sql():
    try:
        sql = request.args['sql']
        df = db_manager.fetch_df(sql)

        from src.utils.sql_generator import generate_create_table, generate_insert_statements
        create_sql = generate_create_table('exported_table', df)
        insert_sql = generate_insert_statements('exported_table', df, batch_size=100)
        sql_script = create_sql + '\n\n' + insert_sql

        return send_file(io.BytesIO(sql_script.encode()), mimetype='text/plain', download_name='result.sql')
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)