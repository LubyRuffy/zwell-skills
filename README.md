# zwell-skills

集中管理个人 Codex Skills。

## 安装与使用

1. 使用官方安装器安装技能：

```bash
$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/github-issue
```

2. 重启 Codex 以加载新技能。

## 已有技能

- gogogo：把后续请求切换为完整闭环执行模式；若已给 issue 编号或 URL 则跳过建 issue，否则先建 issue，再持续推进到实现、验证、review、集成、部署与收尾。主要用于**单人开发模式**，默认从刚拉取的最新主线创建独立 worktree 分支；严格测试和 review 后集成回完整主线再交付。开发前检查 Wails 3 / Make 等发布部署任务，缺少 PC 或移动端 Release 入口时提醒补齐，并验证发布版本自动递增。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/gogogo`

- goglab：公司仓库 GitLab 闭环执行模式；通过 `go env GOPRIVATE` 排除 `github.com` 后识别公司仓库，使用 `glab` 管理 issue、分支、MR 与 CI，强制从最新主线切本地分支开发，禁止直推主分支，MR 提交后必须等 CI 通过才能算完。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/goglab`

- github-issue：GitHub Issue 闭环处理流程（创建 worktree、修复、PR、合并、清理）。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/github-issue`

- golang-quality-optimizer：Go 代码质量优化与简化（不改行为前提下重构、修 lint/staticcheck、补测试、并发与性能质量加固）。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/golang-quality-optimizer`

- utm-vm-cross-platform-it：macOS 宿主机通过 UTM 编排 Linux/Windows/macOS VM 运行跨平台集成测试（保留 ci-* 命名与 ci/cipass 默认账号，优先 SSH，可选 WinRM，必要时 utmctl exec 兜底）。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/utm-vm-cross-platform-it`

- release：为 Go 服务、CLI、库、Wails 桌面应用和 Capacitor 移动应用检查或配置发布链路；按项目现有契约补齐版本递增、严格测试、签名、上传及远端验收。
    - 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/release`
