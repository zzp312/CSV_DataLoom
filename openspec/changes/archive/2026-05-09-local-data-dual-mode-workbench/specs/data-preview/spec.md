## ADDED Requirements

### Requirement: 分页展示
系统SHALL使用分页方式展示查询结果，默认每页显示50-100行。

#### Scenario: 分页浏览结果
- **WHEN**用户执行查询后
- **THEN**右侧结果面板显示第一页数据（最多100行）
- **AND**底部显示分页导航和总行数

### Requirement: 动态加载
系统SHALL支持通过LIMIT和OFFSET从DuckDB动态读取数据。

#### Scenario: 切换分页
- **WHEN**用户点击下一页或指定页码
- **THEN**系统通过LIMIT和OFFSET查询对应页的数据
- **AND**界面只渲染当前页的数据

### Requirement: 结果统计
系统SHALL显示查询结果的总行数和执行耗时。

#### Scenario: 显示统计信息
- **WHEN**查询执行完成
- **THEN**结果面板底部显示"共X行，耗时Y秒"

### Requirement: 虚拟滚动
系统SHALL支持滚动到底部时自动加载下一页数据。

#### Scenario: 滚动加载
- **WHEN**用户滚动到当前页底部
- **THEN**系统自动加载下一页数据并追加到列表