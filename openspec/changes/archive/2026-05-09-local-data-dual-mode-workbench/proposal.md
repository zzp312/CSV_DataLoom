## Why

数据分析师和开发者在处理本地CSV/Excel文件时面临两大痛点：一是Excel的行数限制和SQL命令行的学习门槛，二是大数据量（十万级以上）处理时的性能瓶颈。传统工具基于Pandas全内存加载，导致软件卡顿甚至崩溃。本项目旨在打造一款轻量级桌面端ETL工具，通过DuckDB嵌入式列式数据库实现高性能数据处理，同时提供可视化拖拽与手写SQL双模式，兼顾小白用户与专业开发者。

## What Changes

- 新建"本地数据双模工作台"桌面应用，支持Windows/Mac/Linux跨平台
- 核心引擎从Pandas升级为DuckDB，支持向量化执行和外存查询，百万行数据处理性能提升数倍
- 实现左-中-右三栏式界面布局：左侧数据资产导航、中间可视化画布/SQL编辑器、右侧结果预览与导出
- 支持CSV/XLSX文件拖拽上传，多Sheet选择与表名重命名
- 可视化画布模式：拖拽建表、连线关联（支持多种JOIN方式）、字段勾选、筛选条件配置
- SQL编辑器模式：实时同步画布操作、语法高亮、表名/字段名自动补全
- 分页加载技术：使用Flet PaginatedDataTable实现百万级数据流畅展示
- 一键导出功能：支持导出CSV和智能生成SQL建表+插入脚本

## Capabilities

### New Capabilities

- `data-import`: CSV/XLSX文件导入，支持多Sheet选择、表名重命名、字段类型识别
- `visual-canvas`: 可视化画布，拖拽建表、连线关联、字段勾选、筛选条件配置
- `sql-editor`: SQL编辑器，语法高亮、自动补全、画布与编辑器双向同步
- `data-preview`: 分页预览查询结果，显示总行数和执行耗时
- `data-export`: 导出CSV文件，智能生成SQL脚本（DROP TABLE、CREATE TABLE、INSERT INTO）
- `table-management`: 表结构管理，树状展示已加载表及其字段，数据类型图标标识

### Modified Capabilities

- 无

## Impact

- 新增依赖：DuckDB（数据处理引擎）、Flet（GUI框架）、Pandas（Excel读取）、SQLGlot（SQL解析）
- 创建全新项目结构，无现有代码影响
- 需要学习Flet框架和DuckDB SQL语法