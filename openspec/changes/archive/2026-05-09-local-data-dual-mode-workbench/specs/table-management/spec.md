## ADDED Requirements

### Requirement: 表结构树状展示
系统SHALL以树状结构展示已加载的表及其字段。

#### Scenario: 展开表结构
- **WHEN**用户点击左侧导航栏的表名
- **THEN**展开显示该表的所有字段列表

### Requirement: 字段类型图标
系统SHALL为每个字段显示对应的数据类型图标。

#### Scenario: 显示类型图标
- **WHEN**展示字段列表时
- **THEN**数字类型显示🔢图标
- **AND**文本类型显示🔤图标
- **AND**日期类型显示📅图标

### Requirement: 表重命名
系统SHALL支持对已加载的表进行重命名。

#### Scenario: 修改表名
- **WHEN**用户右键点击表名选择重命名
- **THEN**表名变为可编辑状态
- **AND**修改后更新DuckDB中的表名

### Requirement: 删除表
系统SHALL支持从DuckDB中删除已加载的表。

#### Scenario: 删除表
- **WHEN**用户右键点击表名选择删除
- **THEN**系统弹出确认对话框
- **AND**确认后从DuckDB中删除该表
- **AND**从左侧导航栏移除该表