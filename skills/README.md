# Skills 目录

- release：为 Go 项目（CLI 工具、Wails 桌面应用、纯库）生成发布基础设施（`VERSION`、`Makefile`、`.goreleaser.yaml`）并提供 release 流程说明。
- 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/release`

- gogogo：把后续请求切换为完整闭环执行模式；若已给 issue 编号或 URL 则跳过建 issue，否则先建 issue，再持续推进到实现、验证、review、集成、部署与收尾。
- 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/gogogo`

- github-issue：GitHub Issue 闭环处理流程（创建 worktree、修复、PR、合并、清理）。
- 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/github-issue`

- golang-quality-optimizer：Go 代码质量优化与简化（不改行为前提下重构、修 lint/staticcheck、补测试、并发与性能质量加固）。
- 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/golang-quality-optimizer`

- utm-vm-cross-platform-it：macOS 宿主机通过 UTM 编排 Linux/Windows/macOS VM 运行跨平台集成测试（保留 ci-* 命名与 ci/cipass 默认账号，优先 SSH，可选 WinRM，必要时 utmctl exec 兜底）。
- 安装：`$skill-installer install https://github.com/LubyRuffy/zwell-skills/tree/main/skills/utm-vm-cross-platform-it`
