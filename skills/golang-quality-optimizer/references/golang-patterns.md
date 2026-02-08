# Go 惯用法与反模式速查

本参考文件汇总常用 Go（Golang）惯用法与质量相关模式，用于在重构/简化时快速对齐风格与工程实践。

## 核心原则

- **清晰优先**：能一眼看懂的代码胜过“聪明”的技巧。
- **零值可用**：设计类型让零值即合理可用，减少必须初始化的坑。
- **接收接口，返回结构体**：入参用接口降低耦合；返回具体类型避免无意义抽象。
- **优先标准库**：能用标准库解决的问题，不要引入不必要依赖或自造轮子。

## 错误处理（推荐做法）

- **带上下文 wrap**：`fmt.Errorf("op %s: %w", arg, err)`，既保留 root cause 又便于定位。
- **可判别的错误**：
  - 常见分支用哨兵错误 `var ErrNotFound = errors.New("...")`
  - 需要携带字段时用自定义类型，并配合 `errors.As`
- **检查方式**：
  - `errors.Is(err, target)`：判别链上是否包含某个错误
  - `errors.As(err, &typed)`：抽取错误类型
- **不要吞错**：`_ = ...` 只能用于“确实无关紧要”的 best-effort 清理，并在代码里说明理由。

## 并发（高频风险点）

- **生命周期**：每个 goroutine 都要有退出条件；避免 goroutine leak。
- **取消与超时**：对 IO/阻塞调用使用 `context`，并确保向下传递。
- **协作收口**：多 goroutine 协作优先 `errgroup` 或 `WaitGroup + error channel`，并统一关闭/回收策略。
- **通道约定**：谁负责 `close(ch)` 必须明确；发送方关闭更常见。

并发细节见：`references/concurrency.md`。

## 接口与结构设计

- **小接口**：一个接口只表达一类能力，避免“上帝接口”。
- **在使用处定义接口**：让依赖面更贴近调用方需求。
- **函数式选项（Functional Options）**：用于可选配置，避免构造函数参数爆炸。

接口/组合细节见：`references/interfaces.md`。

## 包组织与工程结构

- 包名简短、语义明确，避免 stutter（例如 `user.User` 这种重复）。
- 避免包级可变状态；优先依赖注入。
- 模块与目录组织见：`references/project-structure.md`。

## 性能与内存（先测再改）

- **已知大小的 slice 预分配**：减少扩容与分配。
- **避免循环字符串拼接**：优先 `strings.Builder` 或标准库 `strings.Join`。
- **复用热点分配**：确实有收益时再考虑 `sync.Pool`（注意其语义与 GC 影响）。

## 工具链命令（常用）

```bash
# build
go build ./...

# test
go test ./...
go test -race ./...
go test -cover ./...

# static analysis
go vet ./...
staticcheck ./...
golangci-lint run

# modules
go mod tidy
go mod verify

# formatting
gofmt -w .
goimports -w .
```

## golangci-lint（建议启用的基础 linter 集合）

把“工程质量”交给工具自动守护，减少人工 review 的低价值消耗。

```yaml
linters:
  enable:
    - errcheck
    - gosimple
    - govet
    - ineffassign
    - staticcheck
    - unused
    - gofmt
    - goimports
    - misspell
    - unconvert
    - unparam

linters-settings:
  errcheck:
    check-type-assertions: true
  govet:
    check-shadowing: true

issues:
  exclude-use-default: false
```

## 常见反模式（避免）

- 长函数里使用 naked return，读者很难知道返回了什么。
- 用 `panic` 处理正常错误路径（除非是不可恢复的程序员错误且有明确策略）。
- 把 `context.Context` 塞进 struct 字段而不是作为第一个参数。
- 同一类型混用值/指针接收者导致语义不一致（除非明确且有注释说明）。

