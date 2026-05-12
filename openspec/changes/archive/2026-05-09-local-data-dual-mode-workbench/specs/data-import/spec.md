## ADDED Requirements

### Requirement: CSV文件导入
系统SHALL支持拖拽CSV文件到导入区域进行数据加载。

#### Scenario: 拖拽CSV文件导入
- **WHEN**用户将CSV文件拖拽到左侧数据资产导航栏的导入区域
- **THEN**系统自动解析CSV文件并创建对应的DuckDB表

### Requirement: Excel文件导入
系统SHALL支持导入XLSX/XLS格式的Excel文件，支持多Sheet选择。

#### Scenario: 导入多Sheet Excel文件
- **WHEN**用户导入包含多个Sheet的Excel文件
- **THEN**系统弹出模态框让用户勾选需要加载的Sheet
- **AND**用户可以为每个Sheet指定表名

### Requirement: 表名自定义
系统SHALL允许用户在导入时自定义表名。

#### Scenario: 修改默认表名
- **WHEN**用户在导入对话框中修改表名输入框
- **THEN**系统使用用户指定的表名创建DuckDB表

### Requirement: 字段类型识别
系统SHALL自动识别导入文件的字段类型（数字、文本、日期等）。

#### Scenario: 类型自动识别
- **WHEN**系统解析导入文件
- **THEN**系统自动推断每个字段的数据类型并显示对应图标
- **AND**用户可以在导入对话框中修改字段类型

### Requirement: 标题行位置选择
系统SHALL允许用户指定标题行的位置（第几行作为列名）。

#### Scenario: 指定标题行
- **WHEN**用户导入文件时
- **THEN**系统显示标题行位置选择框（默认第1行）
- **AND**用户可以调整标题行位置

### Requirement: 内容起始行选择
系统SHALL允许用户指定内容起始行的位置。

#### Scenario: 指定内容起始行
- **WHEN**用户导入文件时
- **THEN**系统显示内容起始行选择框（默认标题行+1）
- **AND**用户可以调整内容起始行位置