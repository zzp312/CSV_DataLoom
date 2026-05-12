## ADDED Requirements

### Requirement: 导出CSV
系统SHALL支持将查询结果导出为CSV文件。

#### Scenario: 导出CSV文件
- **WHEN**用户点击"导出CSV"按钮
- **THEN**系统将当前结果集保存为CSV文件

### Requirement: 导出SQL脚本
系统SHALL支持生成包含建表和插入语句的SQL脚本。

#### Scenario: 生成SQL脚本
- **WHEN**用户点击"导出SQL脚本"按钮
- **THEN**系统分析结果集的每一列数据类型
- **AND**生成包含DROP TABLE IF EXISTS、CREATE TABLE和INSERT INTO的完整SQL文件

### Requirement: 智能类型推断
系统SHALL根据数据内容智能推断SQL字段类型。

#### Scenario: 自动识别字段类型
- **WHEN**系统生成CREATE TABLE语句
- **THEN**纯数字字段自动定义为INT或DECIMAL
- **AND**文本字段自动定义为VARCHAR
- **AND**日期字段自动定义为DATE或DATETIME

### Requirement: 批量INSERT
系统SHALL支持批量INSERT语句生成。

#### Scenario: 生成批量插入语句
- **WHEN**生成INSERT INTO语句时
- **THEN**系统将多条记录合并为一条INSERT语句（多行VALUES）