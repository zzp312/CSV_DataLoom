## ADDED Requirements

### Requirement: SQL实时同步
系统SHALL将画布上的所有操作实时转化为SQL语句显示在编辑器中。

#### Scenario: 画布操作同步到编辑器
- **WHEN**用户在画布上进行拖拽、连线、勾选字段等操作
- **THEN**编辑器中的SQL语句自动更新为对应的标准SQL

### Requirement: SQL语法高亮
系统SHALL提供SQL语法高亮功能。

#### Scenario: 语法高亮显示
- **WHEN**编辑器中显示SQL语句
- **THEN**关键字、表名、字段名以不同颜色高亮显示

### Requirement: 自动补全
系统SHALL支持表名和字段名的自动补全。

#### Scenario: 输入时自动补全
- **WHEN**用户在编辑器中输入表名或字段名的前几个字符
- **THEN**系统弹出候选列表供用户选择

### Requirement: SQL反向解析
系统SHALL尝试将用户编辑的SQL反向解析并更新画布状态。

#### Scenario: SQL修改同步到画布
- **WHEN**用户直接在编辑器中修改SQL语句
- **THEN**系统尝试解析SQL并更新画布上的表节点和连线
- **AND**如果解析失败，提示"复杂查询仅支持代码模式"

### Requirement: 运行SQL
系统SHALL支持点击运行按钮执行SQL查询。

#### Scenario: 执行SQL查询
- **WHEN**用户点击运行按钮
- **THEN**系统将SQL发送到DuckDB执行，并在右侧显示结果