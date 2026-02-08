---
name: golang-quality-optimizer
description: 面向 Go/Golang 代码的质量优化与简化：在不改变行为的前提下重构、降低复杂度、提升可读性/可维护性，并通过 gofmt/goimports、go test、go vet、staticcheck/golangci-lint、-race、benchmark/pprof 等手段验证。适用于“帮我重构/简化/优化 Go 代码”“修 golangci-lint/staticcheck 报错”“提升测试覆盖率/并发安全/性能”等场景。
---

# Golang 质量优化器

## 核心原则（不可破）

- 行为保持：默认不改变对外 API、语义与边界条件；若需要行为变化，先明确说明并征求确认。
- 先可验证再重构：尽量先跑通当前测试/检查作为基线，再逐步改动并持续回归。
- 清晰优先：选择“更好读、更好改、更好测”的实现；避免为了更少代码行数而写得晦涩。
- 聚焦范围：默认只优化本次修改相关的代码路径；扩大范围前先解释收益与风险。

## 工作流（按顺序执行）

1. 明确范围与目标
   - 目标类型：可读性/一致性、可测试性、并发安全、性能、修复 lint/staticcheck。
   - 改动边界：是否允许改公开 API、是否允许调整错误类型/错误信息、是否需要兼容旧行为。

2. 建立基线（尽量在改动前执行）
   - 格式化与导入：`gofmt` / `goimports`
   - 测试：`go test ./...`，必要时 `go test -race ./...`
   - 静态分析：`go vet ./...`，可选 `staticcheck ./...`
   - Lint：若项目使用 `golangci-lint`，跑 `golangci-lint run`
   - 可直接用：`scripts/go_quality_check.sh`

3. 简化与重构（保证语义不变）
   - 减少嵌套：优先“错误提前返回”，让 happy path 更扁平。
   - 消除重复：提取共享逻辑，但避免过度抽象（抽象要能降低整体认知负担）。
   - 命名与职责：提升变量/函数命名可读性；拆分超长函数，但保持高内聚。
   - 优先标准库：能用标准库/常见惯用法解决就不要自造轮子。
   - 参考：`references/simplification-playbook.md`、`references/golang-patterns.md`

4. 质量加固（按需）
   - 错误处理：提供足够上下文并可 `errors.Is/As`；避免吞错；避免用 `panic` 做控制流。
   - context：所有阻塞/IO/远程调用应接收 `context.Context` 作为第一个参数并向下传递；支持取消/超时。
   - 并发：明确 goroutine 生命周期与退出条件；避免泄漏；按需用 `errgroup`/`WaitGroup`/限流/背压。
   - 接口：小接口；在使用处定义；“接收接口，返回结构体”；必要时做编译期断言。
   - 性能：先测再改；写 benchmark/pprof 证明收益；注意分配、热路径、字符串拼接、slice 预分配等。
   - 深入材料：`references/concurrency.md`、`references/interfaces.md`、`references/testing.md`、`references/generics.md`

5. 测试补齐（强制要求）
   - 新增和修改的后端函数必须有单元测试覆盖并通过（优先表驱动测试 + subtests）。
   - 需要并发安全的逻辑：增加 `-race` 覆盖的测试路径。
   - 需要性能保障的逻辑：补 benchmark（必要时加 `b.ReportAllocs()`）。

6. 复跑检查并收口
   - 复跑第 2 步的检查，确保通过；如因环境缺工具被跳过，要明确说明并给出安装/替代建议。
   - 输出变更摘要：只记录“影响理解/维护”的关键变化点；避免长篇复述代码本身。

## 常见“必须/禁止”

必须：
- `gofmt`（必要时 `goimports`）保持格式与 import 一致。
- 错误显式处理；需要时 `fmt.Errorf("...: %w", err)` 包装并提供上下文。
- 对阻塞操作使用 `context.Context` 并处理取消/超时。
- 为新增/修改函数补单元测试并通过。

禁止：
- 为了“更短”而写晦涩技巧（嵌套三元、复杂匿名函数链等）。
- 无生命周期管理地创建 goroutine。
- 对正常错误路径使用 `panic`。
- 无理由忽略 error（`_ = ...` 需要解释为什么安全）。

## 输出模板（建议）

- 你改了什么：按模块/职责分组列关键点（3-8 条为宜）。
- 为什么更好：对应“可读性/一致性/可测试性/并发安全/性能”的收益。
- 你验证了什么：列出执行过的命令与结果（或说明为何无法执行）。
- 风险/待确认：若有行为可能变化、边界条件不确定，明确标记并请求确认。

## 资源导航

- `scripts/go_quality_check.sh`：一键跑常见检查（尽量只读，缺工具会提示）。
- `references/simplification-playbook.md`：Go 代码简化准则（受 code-simplifier 思路启发）。
- `references/golang-patterns.md`：Go 惯用法/反模式/工具链建议（整理自 golang-patterns）。
- `references/concurrency.md`：并发模式与生命周期（来自 golang-pro）。
- `references/testing.md`：测试与基准（来自 golang-pro）。
- `references/interfaces.md`：接口与组合（来自 golang-pro）。
- `references/generics.md`：泛型（来自 golang-pro）。
- `references/project-structure.md`：项目结构与 go.mod（来自 golang-pro）。
