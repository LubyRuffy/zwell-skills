---
name: goglab
description: 将后续请求切换为公司仓库 GitLab 的完整闭环执行模式：优先识别公司仓库上的 issue 编号、`#N` 或 issue URL；若没有则先用 `glab issue create` 创建追踪 issue。公司仓库的识别规则是：读取 `go env GOPRIVATE`，排除 `github.com` 及其子路径后，剩余域名统称为公司仓库，文档中不要泄露这些私有仓库地址。凡涉及公司仓库开发，任务开始前都必须先读取并参考 `https://book.fofa.info/raw/docs/ai-infrastructure/index.md`，再立即加载其中要求的 GitLab 操作规范与快速失败规范。随后先同步默认分支到远端最新，再从最新主线新开本地分支完成实现、验证、代码审查、提交与推送，使用 `glab mr create` 提交 Merge Request 而不是直接推送受保护主分支，并强制等待 GitLab 自动化 CI / merge checks 结束且确认通过后才算完成。适用于用户说“goglab”、要求“从 issue 到 MR 跑完整个流程”、或明确提到公司 GitLab issue / MR / CI 闭环时。
---

# Goglab

## Overview

把 `goglab` 视为公司仓库 GitLab 版的闭环执行模式。它负责把用户后续描述解释为“按 issue -> 分支 -> MR -> CI 的顺序连续执行”，并把具体实现委托给最匹配的项目或领域 skill。

默认只处理公司仓库里的 GitLab 仓库。公司仓库的判定方式是：执行 `go env GOPRIVATE`，把其中 `github.com` 及其子路径排除掉，剩余域名一律按公司仓库处理；写文档时不要把这些私有仓库地址裸出来。这里的硬约束比 `gogogo` 更狠：不允许直接 push 默认分支，不允许绕过 MR，不允许在 CI 还没绿的时候装死收工。

在这些仓库上开发前，先参考 FOFA AI 基础设施导航：
- 基础导航：`https://book.fofa.info/raw/docs/ai-infrastructure/index.md`
- GitLab 操作规范：`https://book.fofa.info/raw/docs/ai-infrastructure/workflow/dev/gitlab.md`
- 快速失败规范：`https://book.fofa.info/raw/docs/ai-infrastructure/common/fail-fast.md`

别装没看见。按照该导航的硬要求，凡涉及公司仓库的任何 GitLab 操作，都必须在任务开始前立即加载 `gitlab.md` 与 `fail-fast.md`。

## Workflow

1. 识别 `goglab` 后面的真实任务，并提炼交付目标、目标仓库、目标 GitLab 主机、是否涉及 issue、是否涉及部署。
2. 用 `go env GOPRIVATE` 识别公司仓库域名，排除 `github.com` 及其子路径后，把剩余域名统称为公司仓库；文档与对外说明中不要泄露这些私有仓库地址。
3. 用 `git remote get-url origin` 或用户给出的 URL 确认目标仓库是否属于公司仓库；若不是，停止套用本 skill，改用更合适的流程。
4. 一旦确认目标属于公司仓库，立即加载并参考：
   - `https://book.fofa.info/raw/docs/ai-infrastructure/index.md`
   - `https://book.fofa.info/raw/docs/ai-infrastructure/workflow/dev/gitlab.md`
   - `https://book.fofa.info/raw/docs/ai-infrastructure/common/fail-fast.md`
5. 判断描述中是否已经包含 issue 编号、`#N`、issue URL 或其他明确可解析的 issue 引用。
6. 如果已经有 issue 引用，直接把该 issue 作为后续实现、MR 与收尾的追踪主线。
7. 如果没有 issue 引用，先用 `glab issue create` 在目标仓库创建追踪 issue，再继续闭环。
8. 在任何代码修改前，先确认 `glab` 已对目标主机完成认证；若未认证，执行 `glab auth login --hostname <host>` 或项目要求的等价流程。
9. 在任何代码修改前，先把默认分支同步到远端最新；默认做法是切到默认分支后执行 `git pull --ff-only`，或执行项目 skill 规定的更严格等价流程。
10. 从已同步的默认分支新建本地开发分支；可以使用本地分支或 worktree，但禁止直接在默认分支上改代码。
11. 识别当前任务对应的最具体 skill，并优先调用它完成实现、测试、review、部署等项目细节。
12. 本地实现完成后运行相关测试与构建验证，修掉阻断问题，再提交代码并把开发分支推到远端。
13. 使用 `glab mr create` 创建或复用 Merge Request，确保 issue、MR、分支、提交说明能互相追踪。
14. MR 提交后，必须持续等待 GitLab 自动化 CI / merge checks 结束并确认通过；默认使用 `glab ci status --branch <branch> --live`，或项目 skill 规定的更严格等价流程。
15. 若 CI 失败，继续定位、修复、重新推送并再次等待，直到 CI 绿为止；不要把“MR 已创建”当成交付完成。
16. 若用户要求“关闭 / 合并 / 完成 / 上线”，且审批与权限允许，则在 CI 通过后继续合并 MR、关闭 issue、清理本地与远端分支；否则至少要把 MR 留在可评审、CI 已通过的状态再结束。

默认闭环顺序：

1. 建立或确认 issue 追踪主线
2. 用 `go env GOPRIVATE` 识别公司仓库范围，并确认目标仓库属于公司仓库
3. 确认 `glab` 认证状态
4. 同步默认分支到远端最新
5. 从最新默认分支新开本地开发分支
6. 复现或确认事实
7. 实现修复或功能
8. 运行相关测试与构建验证
9. 做提交前代码审查，并修复阻断问题
10. 提交并推送开发分支
11. 创建或复用 MR
12. 等待 CI / merge checks 通过
13. 按需合并 MR、关闭 issue、清理分支与 worktree

## Delegation Rules

- `goglab` 只负责定义节奏与 GitLab 门禁，不负责替代项目 skill。
- 发现仓库里已经有更具体的 skill 时，优先委托给它。例如：
  - 某个项目已有专用排障、部署、上线验证 skill 时，优先用该项目 skill。
  - 若仓库存在专门的 GitLab issue / MR skill，优先服从那个 skill 的仓库细则，`goglab` 只补充“不要中途停、必须经 MR 和 CI 才能算完”的执行语义。
- 若没有更具体的 skill，再退回通用工程流程自行执行。
- 若项目 skill 没有更严格的同步规则，默认强制在首次代码修改前同步默认分支。
- 若项目 skill 没有更严格的 Git 约束，默认禁止直接 push 默认分支，所有交付必须经过开发分支 + MR + CI。

## Stop Rules

只有在以下情况才中途停下并向用户确认：

- 缺少必要权限、凭据或账号状态，且无法自行补齐
- 目标仓库不在公司仓库范围内
- 本地存在未提交改动、分支分叉或其他状态，导致无法安全同步默认分支，且又无法通过 stash、额外提交、独立 worktree 或其他安全方式自行化解
- 项目有额外的审批、变更窗口、生产冻结或发布门禁，而仓库内找不到明确规则
- 用户的真实意图与已有 issue、代码、线上事实明显冲突
- CI 持续失败但缺少日志、环境、权限或外部依赖，导致无法继续定位
- MR 已经绿了，但合并需要人工审批、受保护分支特权或外部 reviewer 明确确认，当前账号无法继续推进

除这些阻断条件外，不要把 `goglab` 当成“先做一半再汇报”的指令。

## Git Rules

- 默认把仓库默认分支视为受保护主线；它不一定叫 `main`，别拿脚趾头假设。
- 在任何代码修改之前，必须先把本地默认分支同步到远端最新；默认顺序是切到默认分支后执行 `git pull --ff-only`，或执行项目 skill 规定的更严格等价流程。
- 开发必须从最新默认分支新开本地分支；可以使用 worktree，但禁止直接在默认分支上改代码。
- 默认不允许直接 `git push origin <default-branch>`，也不允许把默认分支当 feature branch 用。
- 本地验证通过后，只能 push 开发分支，再通过 MR 把改动带回默认分支。
- 若当前分支就是默认分支，先切出开发分支再动手；别在主线上裸奔。
- 若使用了本地临时分支或 worktree，任务完成后要清理掉已经不需要的本地开发分支；别把垃圾分支养成遗产项目。

## GitLab Rules

- 优先使用 `glab` 处理 issue、MR 与 CI 状态，不要手写一堆重复 API 请求。
- 解析 issue 时可直接使用：
  - `glab issue view <id>`
  - `glab issue view <issue-url>`
- 创建 issue 时优先使用：
  - `glab issue create -t "<title>" -d "<description>"`
- 复用已有 MR 时优先检查：
  - `glab mr list --source-branch <branch> -R <group/project>`
- 创建 MR 时优先使用：
  - `glab mr create --source-branch <branch> --target-branch <default-branch> --related-issue <issue-id> --title "<title>" --description "<body>"`
- 若需要在创建 MR 时顺手推送分支，可使用 `glab mr create --push ...`；否则先 `git push -u origin <branch>` 再创建 MR。
- 若用户明确要求合并，且权限允许，优先使用：
  - `glab mr merge <mr-id> --squash --remove-source-branch`
- 若仓库启用了更严格的审批或 auto-merge 规则，服从仓库规则；`goglab` 的底线只是“不能绕过 MR 和 CI”。

## CI Rules

- MR 创建后，必须显式等待 pipeline 结束；不要只看“pipeline started”就装看不见。
- 默认使用：
  - `glab ci status --branch <branch> --live`
- 若需要查看更完整的 pipeline 详情，可使用：
  - `glab ci view --branch <branch>`
- 只有在 CI / merge checks 明确通过后，才能把当前阶段标记为完成。
- 若 CI 失败，先在当前分支修复，再重新推送并再次等待；不要把失败的红灯 MR 交给用户擦屁股。
- 若 CI 通过但 MR 仍被审批或分支保护规则拦住，说明代码门禁阶段完成，但闭环尚未彻底结束；继续推进能推进的部分，并明确剩余人工门禁。

## Decision Rules

- 默认用户画像是公司仓库里想把活一路推完的单人开发，不假设能直接动受保护主分支。
- 若没有明确相反要求，目标主线是仓库默认分支，交付通道是“本地开发分支 -> 远端分支 -> MR -> CI -> 合并”。
- 若用户没有明确要求创建 issue，但没有可追踪的 issue 入口，默认先补一个 issue，别让 MR 像野生提交一样乱飞。
- 若用户没有明确要求保留长期开发分支，MR 合并完成后默认删除源分支并清理本地分支。
- 若用户只要求“提 MR 并等 CI”，则在 MR 可评审且 CI 通过后结束；若用户明确要求“合并 / 关闭 / 上线”，则继续推进到 MR 合并、issue 收尾和后续验证。
- 进入结束阶段时，不要凭印象假设“应该已经好了”；必须看到 CI 通过这个硬信号。

## Examples

- `goglab 修复 #123`
- `goglab 处理 <公司仓库 issue URL>`
- `goglab 把这个导入问题从建 issue 到提 MR 跑完整，等 CI 绿了再停`
- `goglab 修复这个 bug，不能碰主分支，提 MR 后等流水线过完`
