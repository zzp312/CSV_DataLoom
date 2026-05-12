## ADDED Requirements

### Requirement: 拖拽建表
系统SHALL支持从左侧导航栏拖拽表到中间画布区域。

#### Scenario: 拖拽表到画布
- **WHEN**用户从左侧数据资产导航栏拖拽一个表到中间画布
- **THEN**画布上显示该表的可视化节点，包含表名和字段列表

### Requirement: 连线关联
系统SHALL支持在画布上通过拖拽建立表之间的关联关系。

#### Scenario: 建立表关联
- **WHEN**用户从表A的某个字段拖拽到表B的某个字段
- **THEN**系统在两个字段之间绘制连线，并自动生成INNER JOIN逻辑

### Requirement: 关联方式切换
系统SHALL支持切换关联方式（内连接、左连接、右连接、全连接）。

#### Scenario: 切换JOIN类型
- **WHEN**用户点击连线上的切换按钮
- **THEN**系统循环切换JOIN类型（INNER JOIN → LEFT JOIN → RIGHT JOIN → FULL JOIN）

### Requirement: 字段勾选
系统SHALL支持在画布表节点上勾选需要展示的字段。

#### Scenario: 勾选字段
- **WHEN**用户在画布的表节点上勾选或取消勾选字段
- **THEN**系统更新SELECT语句中的字段列表

### Requirement: 筛选条件配置
系统SHALL支持为表添加筛选条件。

#### Scenario: 添加筛选条件
- **WHEN**用户点击表节点上的"添加筛选条件"按钮
- **THEN**系统弹出筛选配置面板，支持选择字段、运算符和值
- **AND**系统自动生成WHERE子句