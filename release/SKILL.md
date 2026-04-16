---
name: release
description: 为 Go 项目（CLI 工具、Wails 桌面应用、纯库）自动生成完整的发布基础设施，包括 VERSION 文件、Makefile release 目标、.goreleaser.yaml 配置，并提供一键发布流程说明。当用户说"帮我配置发布""添加 release 流程""setup goreleaser""初始化发布""generate release config"或需要为项目搭建版本管理与发布能力时触发。
---

# Release Skill

为 Go 项目自动生成完整的发布基础设施，无需手动写配置。

## 执行流程

### 第一步：探查项目类型

读取项目根目录，判断项目类型（可能同时属于多种）。建议优先级如下：

1. **Wails 桌面应用**：存在 `wails.json` 或 `build/config.yml`，且通常会存在 `wails` 相关脚本和 `frontend` 目录。
2. **单二进制 CLI**：根目录存在 `main.go`，或 `cmd/` 下仅一个 `main.go` 主入口。
3. **多二进制 CLI**：`cmd/` 下存在多个子目录，每个子目录有独立 `main.go`。
4. **Go 库**：存在 `go.mod`，但上述二进制入口均不存在，且通常只包含 `*.go` 库源码。

同时收集：
- `go.mod` 中的 `module` 路径（用于 ldflags）
- `go.mod` 中的 Go 版本
- `cmd/` 下各子目录名（多二进制项目）
- GitHub remote URL（推断 `owner/repo`）
- 是否已存在 `VERSION`、`Makefile`、`.goreleaser.yaml`

> 提示：若项目包含子模块（`go.work`）或 `cmd/` 目录中既有样例/实验子命令，建议手动确认最终目标文件（CLI/库/Wails）以免误判。

### 第二步：生成文件

根据项目类型生成或追加以下文件，**已存在且内容合理则跳过**：

1. `VERSION` — 版本号单一来源
2. `Makefile` — 版本管理与发布目标
3. `.goreleaser.yaml` — 构建与发布配置
4. （可选）`.github/workflows/release.yml` — 手动触发的 CI 发布

### 约束说明（非高风险优化项）

- `VERSION` 采用 `x.y.z` 的三段语义化版本（如 `0.1.2`）。若项目有 `v1.2.3-beta` 等预发布需求，可在此基础上再扩展脚本，但当前模板默认不直接支持。
- 对不满足语义化格式的版本号，先修正后再执行 bump/release，避免 `awk` 计算偏差。
- Wails 与纯 CLI 项目共享 `release` 流程逻辑时，建议明确分开 `RELEASE_TYPE`（例如 `cli`/`wails`）进行定制，减少误配置风险。

---

## 生成模板

### VERSION 文件

```
0.0.1
```

---

### Makefile（追加到现有文件，或新建）

```makefile
SHELL   := /bin/bash
VERSION := $(shell cat VERSION 2>/dev/null | tr -d '[:space:]')
TAG     := v$(VERSION)
REPO    := $(shell git remote get-url origin 2>/dev/null | sed 's|.*github.com[:/]\(.*\)\.git|\1|;s|.*github.com[:/]\(.*\)|\1|')
SEMVER_RE := ^[0-9]+\.[0-9]+\.[0-9]+$

.PHONY: version bump-patch bump-minor bump-major \
        release-check release-dry release version-check

# ── 版本查看 ──
version:
	@echo $(TAG)

# ── 语义化版本校验 ──
version-check:
	@if ! echo $(VERSION) | grep -Eq "$(SEMVER_RE)"; then \
		echo "❌ VERSION 格式不合法：必须为 x.y.z（例如 1.2.3）"; \
		exit 1; \
	fi

# ── 版本号递增 ──
bump-patch:
	@echo $$(echo $(VERSION) | awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}') > VERSION
	@echo "VERSION → v$$(cat VERSION | tr -d '[:space:]')"

bump-minor:
	@echo $$(echo $(VERSION) | awk -F. '{printf "%d.%d.0", $$1, $$2+1}') > VERSION
	@echo "VERSION → v$$(cat VERSION | tr -d '[:space:]')"

bump-major:
	@echo $$(echo $(VERSION) | awk -F. '{printf "%d.0.0", $$1+1}') > VERSION
	@echo "VERSION → v$$(cat VERSION | tr -d '[:space:]')"

# ── 验证 goreleaser 配置 ──
release-check:
	goreleaser check
	@$(MAKE) version-check

# ── 快照构建（不推送、不发布） ──
release-dry:
	@echo "📦 快照构建（不发布）…"
	@$(MAKE) version-check
	@GITHUB_TOKEN=$${GITHUB_TOKEN:-$$(gh auth token)} goreleaser release --snapshot --clean --skip=publish

# ── 一键发布 ──
release:
	@test -n "$(VERSION)" || { echo "❌ VERSION 文件为空"; exit 1; }
	@$(MAKE) version-check
	@test "$$(git branch --show-current)" = "main" || { echo "❌ 当前不在 main 分支"; exit 1; }
	@command -v goreleaser >/dev/null 2>&1 || { echo "❌ 未找到 goreleaser: https://goreleaser.com/install"; exit 1; }
	@command -v gh >/dev/null 2>&1 || { echo "❌ 未找到 gh CLI: https://cli.github.com"; exit 1; }
	@gh auth status -h github.com >/dev/null 2>&1 || { echo "❌ gh 未登录，请执行 gh auth login"; exit 1; }
	@if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$$(git ls-files --others --exclude-standard)" ]; then \
		echo "📝 提交工作区变更…"; \
		git add -A && git commit -m "chore: prepare release $(TAG)"; \
	fi
	@TAG_CUR="v$$(cat VERSION | tr -d '[:space:]')"; \
	if git tag -l "$$TAG_CUR" | grep -q "$$TAG_CUR"; then \
		TAG_EPOCH=$$(git log -1 --format=%ct "$$TAG_CUR" 2>/dev/null || echo 0); \
		NOW_EPOCH=$$(date +%s); \
		AGE=$$(( NOW_EPOCH - TAG_EPOCH )); \
		if [ "$$AGE" -gt 86400 ]; then \
			echo "⏰ $$TAG_CUR 已存在且超过 1 天，自动递增补丁版本…"; \
			NEW_VER=$$(cat VERSION | tr -d '[:space:]' | awk -F. '{printf "%d.%d.%d", $$1, $$2, $$3+1}'); \
			echo "$$NEW_VER" > VERSION; \
			git add VERSION && git commit -m "chore: bump version to v$$NEW_VER"; \
			TAG_CUR="v$$NEW_VER"; \
		else \
			echo "🏷️  $$TAG_CUR 已存在但不超过 1 天，覆盖…"; \
			git tag -d "$$TAG_CUR"; \
			git push origin ":refs/tags/$$TAG_CUR" 2>/dev/null || true; \
		fi; \
	fi; \
	TAG_FINAL="v$$(cat VERSION | tr -d '[:space:]')"; \
	echo "🏷️  创建标签 $$TAG_FINAL …"; \
	git tag -a "$$TAG_FINAL" -m "release $$TAG_FINAL"; \
	echo "🚀 推送到远端…"; \
	git push origin main --tags; \
	echo "📦 本地编译并发布 $$TAG_FINAL …"; \
	GITHUB_TOKEN=$${GITHUB_TOKEN:-$$(gh auth token)} goreleaser release --clean; \
	echo "🧹 清理残留 draft…"; \
	for draft_id in $$(gh api repos/$(REPO)/releases --jq '.[] | select(.draft==true) | .id' 2>/dev/null); do \
		gh api -X DELETE "repos/$(REPO)/releases/$$draft_id" 2>/dev/null || true; \
	done; \
	echo ""; \
	echo "✅ $$TAG_FINAL 已发布: https://github.com/$(REPO)/releases/tag/$$TAG_FINAL"
```

---

### .goreleaser.yaml — CLI 工具（单二进制）

```yaml
# yaml-language-server: $schema=https://goreleaser.com/static/schema.json
version: 2

project_name: <BINARY_NAME>

builds:
  - id: <BINARY_NAME>
    main: .         # 或 ./cmd/<BINARY_NAME>
    binary: <BINARY_NAME>
    goos: [linux, darwin, windows]
    goarch: [amd64, arm64]
    env:
      - CGO_ENABLED=0
    flags: [-trimpath, -buildvcs=false]
    ldflags:
      - -s -w
      - -X main.Version={{ .Version }}
      - -X main.Commit={{ .Commit }}
      - -X main.BuildTime={{ .Date }}

archives:
  - id: default
    formats: [tar.gz]
    format_overrides:
      - goos: windows
        formats: [zip]
    name_template: "{{ .ProjectName }}_{{ .Version }}_{{ .Os }}_{{ .Arch }}"

checksum:
  name_template: checksums.txt

snapshot:
  version_template: "{{ incpatch .Version }}-next"

changelog:
  sort: asc
  filters:
    exclude: ['^docs:', '^test:', '^chore:']

release:
  github:
    owner: <GITHUB_OWNER>
    name: <GITHUB_REPO>
  prerelease: auto
  make_latest: true
  name_template: "{{ .ProjectName }} {{ .Tag }}"
```

---

### .goreleaser.yaml — Wails 桌面应用（macOS arm64 示例）

```yaml
# yaml-language-server: $schema=https://goreleaser.com/static/schema.json
version: 2

project_name: <APP_NAME>
dist: dist/goreleaser

before:
  hooks:
    - sh -c 'cd <FRONTEND_DIR> && npm ci --no-audit --no-fund'
    - sh -c 'cd <FRONTEND_DIR> && npm run build'

builds:
  - id: <APP_NAME>-darwin-arm64
    dir: <DESKTOP_DIR>       # 含独立 go.mod 的桌面工程目录，如 cmd/myapp
    main: .
    binary: <APP_NAME>
    goos: [darwin]
    goarch: [arm64]
    env:
      - CGO_ENABLED=1
      - MACOSX_DEPLOYMENT_TARGET=10.15
      - CGO_CFLAGS=-mmacosx-version-min=10.15
      - CGO_LDFLAGS=-mmacosx-version-min=10.15
    tags: [with_clash_api, with_gvisor]    # 按项目实际 build tags 调整
    flags: [-trimpath, -buildvcs=false]
    ldflags:
      - -s -w
      - -X <MODULE_PATH>/internal/server.BackendVersion={{ .Version }}
      - -X <MODULE_PATH>/internal/server.BuildCommit={{ .Commit }}
      - -X <MODULE_PATH>/internal/server.BuildTime={{ .Date }}
    hooks:
      post:
        - sh -c 'scripts/package-macos-app-goreleaser.sh "{{ .Path }}" "{{ .Version }}" "{{ .Os }}" "{{ .Arch }}"'

archives:
  - id: <APP_NAME>-archive
    ids: [<APP_NAME>-darwin-arm64]
    formats: [none]

checksum:
  name_template: checksums.txt
  extra_files:
    - glob: ./dist/goreleaser/<APP_NAME>_*_darwin_arm64_app.zip

snapshot:
  version_template: "{{ incpatch .Version }}-next"

changelog:
  sort: asc

release:
  extra_files:
    - glob: ./dist/goreleaser/<APP_NAME>_*_darwin_arm64_app.zip
  github:
    owner: <GITHUB_OWNER>
    name: <GITHUB_REPO>
  prerelease: auto
  make_latest: true
  name_template: "<APP_DISPLAY_NAME> {{ .Tag }}"
```

> Wails 项目不需要调用 `wails3 build` 命令；goreleaser 直接调用 `go build`，只需确保 `frontend/bindings/` 已通过 `wails3 generate bindings` 更新。

---

### .github/workflows/release.yml（可选，手动触发）

### Wails/CGo 项目（推荐）

```yaml
name: release
on:
  workflow_dispatch:

permissions:
  contents: write
  packages: write

concurrency:
  group: release-workflow
  cancel-in-progress: false

defaults:
  run:
    shell: bash

jobs:
  release:
    runs-on: macos-latest   # Wails/CGO 项目；纯 CLI 可改为 ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - name: Setup Node
        uses: actions/setup-node@v4
        with: { node-version: '20' }   # Wails 项目需要；CLI 可删除
      - uses: goreleaser/goreleaser-action@v6
        with:
          version: latest
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

> 推送 `v*` tag **不**自动触发此 workflow（`workflow_dispatch` 仅手动触发），避免与本地 `make release` 竞争。

### 纯 CLI 建议

```yaml
name: release
on:
  workflow_dispatch:

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with: { fetch-depth: 0 }
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - uses: goreleaser/goreleaser-action@v6
        with:
          version: latest
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

> Wails 项目可先执行前端构建步骤，再执行 goreleaser；纯 CLI 可去掉 Node 相关步骤。

---

## 占位符替换说明

生成文件后，根据实际项目替换以下占位符：

| 占位符 | 替换为 |
|--------|--------|
| `<BINARY_NAME>` | 可执行文件名，如 `mytool` |
| `<APP_NAME>` | 应用名，如 `myapp` |
| `<APP_DISPLAY_NAME>` | GitHub Release 展示名，如 `My App` |
| `<FRONTEND_DIR>` | 前端目录路径，如 `cmd/myapp/frontend` |
| `<DESKTOP_DIR>` | 桌面端 Go 工程目录，如 `cmd/myapp` |
| `<MODULE_PATH>` | go.mod 中的 module 路径 |
| `<GITHUB_OWNER>` | GitHub 用户名或组织名 |
| `<GITHUB_REPO>` | GitHub 仓库名 |

可通过以下命令自动获取：

```bash
# module 路径
head -1 go.mod | awk '{print $2}'

# GitHub owner/repo
git remote get-url origin | sed 's|.*github.com[:/]\(.*\)\.git|\1|;s|.*github.com[:/]\(.*\)|\1|'
```

---

## 前置工具检查

```bash
# 安装 goreleaser（macOS）
brew install goreleaser

# 安装 gh CLI（macOS）
brew install gh

# 登录 GitHub
gh auth login
```

补充校验（推荐）：

```bash
make version-check
make release-check
make release-dry
```

---

## 日常使用速查

```bash
make version          # 查看当前版本
make bump-patch       # 0.0.1 → 0.0.2
make bump-minor       # 0.0.1 → 0.1.0
make bump-major       # 0.0.1 → 1.0.0
make release-check    # 验证 .goreleaser.yaml 语法
make release-dry      # 本地构建快照（不发布）
make release          # 一键打 tag → 编译 → 发布
```
