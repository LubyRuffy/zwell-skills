# zwell-skills

集中管理个人 Codex Skills。

## 安装与使用

1. 使用 `npx skills` 从 GitHub 安装到全局技能目录，由工具维护各客户端的安装关系：

```bash
npx skills add LubyRuffy/zwell-skills --skill gogogo --global --yes
```

2. 更新前先盘点已有客户端入口：

```bash
npx skills list --global --json
```

再按已有客户端范围重装指定技能；`<已安装客户端>` 替换为已确认的客户端标识，可指定多个：

```bash
npx skills add LubyRuffy/zwell-skills --skill gogogo --global --yes --agent <已安装客户端>
```

客户端可能在会话开始时加载技能，更新后按对应客户端的加载方式开启新会话或重新加载。

## 维护与交付

`skills/<name>/` 是技能的源码。修改后验证并提交到本仓库，推送到 GitHub 并核对远端提交，再按上述已有客户端范围执行 `npx skills add` 重装更新；首次安装选择本次需要的客户端。

`npx skills update <name> --global --yes` 会重新检测客户端，仅在确认探测结果不会增加安装范围时使用。多个客户端共享同一规范目录时，可选择一个已有的共享目录客户端更新该目录，随后逐一验证所有已有入口；存在独立副本时必须覆盖其对应客户端。

交付必须核对安装锁中的来源与技能目录版本，并验证已有客户端入口解析到已发布内容。只改 `~/.agents/skills`、只改某个客户端的副本或只推送源码，均未完成交付。更新限定到本次技能，保留其他技能、客户端安装关系和无关配置；不通过手工复制替代 `npx skills`。

开发规则与检查命令见 [AGENTS.md](AGENTS.md)。

## 已有技能

- gogogo：把后续请求切换为完整闭环执行模式；若已给 issue 编号或 URL 则跳过建 issue，否则先建 issue，再持续推进到实现、验证、review、集成、部署与收尾。主要用于**单人开发模式**，默认从刚拉取的最新主线创建独立 worktree 分支；严格测试和 review 后先提交并推送开发分支，再同步本地 main、合入和复验，最后从完整 main 推送与交付。每次任务无论是否发布，收尾都必须实测用户启动目录 HEAD、本地主线和远端主线 SHA 一致、领先/落后为 0 且工作区干净；分叉先审查并安全合并，存在无关工作时保留现场并报告同步未完成。开发前检查 Wails 3 / Make 等发布部署任务，缺少 PC 或移动端 Release 入口时提醒补齐，并验证发布版本自动递增。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill gogogo --global --yes`

- goglab：公司仓库 GitLab 闭环执行模式；通过 `go env GOPRIVATE` 排除 `github.com` 后识别公司仓库，使用 `glab` 管理 issue、分支、MR 与 CI，强制从最新主线切本地分支开发，禁止直推主分支，MR 提交后必须等 CI 通过才能算完。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill goglab --global --yes`

- github-issue：GitHub Issue 闭环处理流程（创建 worktree、修复、PR、合并、清理）。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill github-issue --global --yes`

- golang-quality-optimizer：Go 代码质量优化与简化（不改行为前提下重构、修 lint/staticcheck、补测试、并发与性能质量加固）。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill golang-quality-optimizer --global --yes`

- utm-vm-cross-platform-it：macOS 宿主机通过 UTM 编排 Linux/Windows/macOS VM 运行跨平台集成测试（保留 ci-* 命名与 ci/cipass 默认账号，优先 SSH，可选 WinRM，必要时 utmctl exec 兜底）。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill utm-vm-cross-platform-it --global --yes`

- release：为 Go 服务、CLI、库、Wails 桌面应用和 Capacitor 移动应用检查或配置发布链路；按项目现有契约补齐版本递增、严格测试、签名、上传及远端验收。
    - 安装：`npx skills add LubyRuffy/zwell-skills --skill release --global --yes`
