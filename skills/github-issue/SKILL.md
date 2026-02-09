---
name: github-issue
description: 处理 GitHub Issue 的完整闭环：获取 issue 详情、创建并进入 worktree 分支、修复问题、创建关联 issue 的 PR、squash 合并、清理本地/远程分支与 worktree，并在需要时关闭 issue。适用于用户输入“修复 issue 3”“#3”或 issue URL 等开始修复，以及用户输入“关闭/close/完成”结束并合并的场景。
---

# GitHub Issue 工作流

## 概览
按两阶段执行：
- 阶段1（拉取 issue 并解决问题）：创建 worktree 分支并完成修复。
- 阶段2（推送 PR 并 close）：提交、rebase、创建/合并 PR、清理分支与 worktree、关闭 issue。
按需阶段：
- 阶段2.5（过程记录）：当用户说“把过程记录一下”时，作为 GitHub Issue 评论提交。
贯穿全过程的强制要求：
- 发现的问题、用户反馈、结论与思考，必须作为“过程记录”评论到 GitHub Issue（用 `gh issue comment`）。
- 最终 PR 说明必须包含“问题原因”和“修复方案”。
- 若本次排查/修复耗时较长且流程复杂（例如多轮定位、涉及环境/CI/worktree 等坑），在提交 PR 前将可复用的经验教训沉淀到仓库 `AGENTS.md`，随 PR 一起提交，便于下次提速与避免重复踩坑。

## 决策流程
- 用户提供 issue 号码 / #N / issue URL：执行“阶段1（拉取 issue 并解决问题）”。
- 用户说“把过程记录一下/记录过程/补记过程”等：执行“阶段2.5（过程记录）”。
- 用户说“关闭/close/完成”等：执行“阶段2（推送 PR 并 close）”。
- 若关闭请求时没有当前 issue 上下文：询问要关闭哪个 issue。

## 需要保持的上下文
- repo（owner/name）
- issue_number
- issue_title
- default_branch
- worktree_path
- branch_name
- base_repo_path
- process_notes（过程记录要点：问题/反馈/结论）

## 阶段2.5：过程记录（按需触发）
触发条件：用户明确要求“把过程记录一下/记录过程/补记过程”等。

执行动作：整理当前进展与结论，提交为 GitHub Issue 评论（可重复追加）。

## 过程记录（强制原则）
在修复过程中只要出现以下信息，立即写入 issue 评论并持续追加：
- 发现的问题或定位结果
- 用户反馈或复现条件变化
- 结论、反思、权衡、已验证/未验证的假设

推荐统一格式（按需补充/更新）：
```
gh issue comment <num> --repo <owner/name> --body $'## 过程记录\n- 发现的问题：...\n- 用户反馈：...\n- 结论/思考：...\n- 影响范围：...\n- 验证情况：...'
```

## 阶段1：拉取 issue 并解决问题

1. 解析 issue 引用
   - URL：提取 owner/name 与 issue 号。
   - “#N”或“N”：使用当前仓库（`git remote origin` 或 `gh repo view`）。
2. 获取 issue 详情与默认分支
   - `gh issue view <num> --repo <owner/name> --json title,body,labels,assignees -q '.title'`
   - `gh repo view <owner/name> --json defaultBranchRef -q '.defaultBranchRef.name'`
   - 若 gh 命令提示未登录，再提醒用户执行 `gh auth login`。
2.1 解析并处理 issue 中的图片（强制）
   - 获取 issue body：
     - `gh issue view <num> --repo <owner/name> --json body -q '.body'`
   - 从 body 中提取图片链接（Markdown `![](...)` 或裸 URL），保存到本地目录：
     - 目录：`$base_repo_path/.issue-assets/issue-<num>/`
     - 示例提取（任一即可）：
       - `python - <<'PY'\nimport os,re,sys\nbody=sys.stdin.read()\nurls=re.findall(r'!\\[[^\\]]*\\]\\(([^)]+)\\)', body)+re.findall(r'(https?://\\S+)', body)\nfor u in urls:\n  if any(k in u for k in [\"user-images\", \"github.com\", \"githubusercontent\", \"assets\"]):\n    print(u)\nPY`
   - 下载图片：
     - `mkdir -p "$base_repo_path/.issue-assets/issue-<num>"\ncd "$base_repo_path/.issue-assets/issue-<num>"\nwhile read -r u; do curl -L -o \"$(basename \"${u%%\\?*}\")\" \"$u\"; done`
   - 理解图片内容并写入过程记录：
     - 在支持图片查看的环境中打开并逐张描述关键内容（例如报错信息、UI状态、日志片段、对比图）。
     - 若无法查看图片，至少记录“图片内容待确认”的风险点与影响范围。
   - 任何从图片中得到的关键信息，都必须追加到“过程记录”评论中。
3. 解析仓库根目录并拉取最新
   - `base_repo_path=$(git rev-parse --show-toplevel)`
   - `git -C "$base_repo_path" fetch origin`
4. 主 worktree 脏态检查（强制，防止误改 main）
   - `git -C "$base_repo_path" status --porcelain` 必须为空。
   - 若不为空：说明主 worktree 有未提交改动（常见原因：误在 main 上改了文件，导致后续 `git pull`/`worktree add`/rebase 等都受影响）。
     - 若能确认这些改动就是本次 issue 相关（或明显是误改），按“误改救援流程（主 worktree -> worktree）”处理后再继续。
     - 若无法确认改动归属（可能是用户自己的 WIP）：先停止并询问用户要如何处理（commit / stash / 放弃 / 迁移到其他分支）。不要擅自 `reset --hard`。
5. 生成分支与 worktree 路径
   - `branch_name=issue-<num>`（需要时加 slug）
   - `worktree_path=<base_repo_path>/.worktrees/<branch_name>`
6. 创建或复用 worktree
   - 若已存在：直接复用。
   - 否则：
     - `git -C "$base_repo_path" worktree add -b "$branch_name" "$worktree_path" "origin/$default_branch"`
7. 进入 worktree 并修复
   - `cd "$worktree_path"`
   - **进入后立即做“防误改检查”**：
     - `pwd` 应等于 `$worktree_path`
     - `git rev-parse --show-toplevel` 应等于 `$worktree_path`
     - `git rev-parse --abbrev-ref HEAD` 应为 `issue-<num>` 分支
     - `git status -sb` 不应显示 `main` 分支
   - 修改代码并跑必要测试/构建（所有命令必须在 `$worktree_path` 执行）。
   - 如果是后端 bug，必须尽可能先通过单元测试复现，再修改代码；确实无法单测时，再使用集成测试复现并说明原因。
   - 过程中发现问题/收到反馈/得到结论时，立即按“过程记录（强制）”写入 issue 评论。
   - 可暂不提交，留到“关闭/完成”阶段统一提交。

## 防误改主分支约束（强制）
- **严禁**在 `$base_repo_path`（主 worktree）直接修改/应用补丁/复制文件。
- 仅允许在 `$base_repo_path` 执行：`fetch`、`worktree add/remove/prune`、`gh pr merge` 等管理命令。
- 任何 `cp` / `apply` / `git apply` / 编辑器写入都必须指向 `$worktree_path`。
- 若发现主仓库有改动（`git -C "$base_repo_path" status -sb` 不是干净的 `main`），立刻停止：按“误改救援流程（主 worktree -> worktree）”处理，确保 `$base_repo_path` 恢复干净后再继续。
- 运行测试/构建时，必须显式 `workdir` 为 `$worktree_path`（或子目录），避免默认落在主仓库。

### Codex 工具级防呆（强制）
- **所有会改动文件的操作必须使用 `$worktree_path` 绝对路径**（例如 `$worktree_path/internal/foo/bar.go`），不要对仓库相对路径（如 `internal/foo/bar.go`）做编辑/打补丁，否则极易落到主 worktree。
- **所有 shell 命令必须显式指定目录**：
  - Git 命令优先用 `git -C "$base_repo_path" ...` 或 `git -C "$worktree_path" ...`。
  - 构建/测试命令必须在 worktree 下执行：`cd "$worktree_path"` 后再跑，或在工具调用里显式 `workdir="$worktree_path"`。
- 每次准备写代码（apply_patch / heredoc / 生成文件 / gofmt）前，先执行并人工确认输出：
  - `git -C "$base_repo_path" status -sb`
  - `git -C "$worktree_path" status -sb`
  - `git -C "$worktree_path" rev-parse --show-toplevel`

### 误改救援流程（主 worktree -> worktree）
目标：把误落在 `$base_repo_path` 的改动安全迁移到 `$worktree_path`，并恢复主 worktree 干净状态，避免 `git pull` 失败。

1. 在主 worktree 创建救援 stash（包含未跟踪文件）
   - `git -C "$base_repo_path" stash push -u -m "codex-rescue: move changes into $branch_name"`
2. 确保 worktree 已创建并处于目标分支
   - `git -C "$base_repo_path" worktree list`
   - `git -C "$worktree_path" rev-parse --abbrev-ref HEAD`
3. 在 worktree 应用救援 stash
   - `git -C "$worktree_path" stash list`
   - `git -C "$worktree_path" stash pop`（若不是最新一条，改用 `stash pop stash@{N}`）
4. 复核：主 worktree 已干净、改动已迁移
   - `git -C "$base_repo_path" status --porcelain` 应为空
   - `git -C "$worktree_path" status -sb` 应能看到对应改动
5. 若 `stash pop` 有冲突：按冲突流程解决，但仍需保证最终 `$base_repo_path` 干净。

## 阶段2：推送 PR 并 close

1. 确认上下文
   - 若缺少 repo/issue/branch/worktree 等信息，询问用户。
2. 提交前检查
   - `cd "$worktree_path"`
   - `git status -sb`
   - 若有改动：`git add -A`
2.1. 经验沉淀到 `AGENTS.md`（条件触发）
   - 触发条件：本次排查/修复耗时较长且流程复杂，且存在可复用的坑点/排查路径/命令。
   - 执行动作：在 `$worktree_path/AGENTS.md` 追加一段简短“经验教训”，并纳入本次提交（避免在 `$base_repo_path` 误改）。
   - 内容要求：只写可复用、可操作、可检索的要点；避免粘贴大段日志/输出；避免写入密钥等敏感信息。
   - 推荐模板（按需精简）：
     ```
     ## 经验教训：Issue #<num> / PR #<pr_number>
     - 现象：...
     - 根因：...
     - 排查路径（关键步骤/关键命令）：...
     - 修复要点：...
     - 验证方式：...
     ```
   - 若仓库不存在 `AGENTS.md`：先询问用户是否要创建；若不创建，至少把这段经验补充到 issue“过程记录”评论中。
3. 提交（保持单提交，方便 squash）
   - `git commit -m "Fix #<num>: <issue_title>"`
4. rebase 到最新默认分支
   - `git fetch origin`
   - `git rebase "origin/$default_branch"`
   - 如有冲突，解决后再跑必要测试。
4.1. 补充最终结论/思考
   - 若尚未记录最终结论或关键权衡，追加一条 issue 评论进行总结（遵循“过程记录（强制）”格式）。
5. 创建或复用 PR（关联 issue）
   - 查找已有 PR：
     - `gh pr list --repo <owner/name> --head "$branch_name" --state open --json number -q '.[0].number'`
   - 若无：
     - `gh pr create --repo <owner/name> --base "$default_branch" --head "$branch_name" --title "Fix #<num>: <title>" --body "Fixes #<num>\n\n## 问题原因\n<原因>\n\n## 修复方案\n<方案>\n\n## 验证\n- <测试/验证>"`
6. squash 合并并删除远程分支
   - **固定约定**：在主 worktree（`$base_repo_path`）执行合并，或在非仓库目录执行并带 `--repo <owner/name>`，避免 worktree 占用默认分支导致报错。
   - `cd "$base_repo_path" && gh pr merge <pr_number> --squash --delete-branch --repo <owner/name>`
   - 若需要等待 CI：可用 `--auto --squash --delete-branch`。
7. 关闭 issue（如未自动关闭）
   - `gh issue view <num> --repo <owner/name> --json state -q .state`
   - 若仍为 open：`gh issue close <num> --repo <owner/name> --comment "Closed via PR #<pr_number>"`
8. 清理本地 worktree 与分支
   - `git -C "$base_repo_path" worktree remove "$worktree_path"`
   - `git -C "$base_repo_path" branch -D "$branch_name"`
   - `git -C "$base_repo_path" worktree prune`

## 异常与边界情况
- issue URL 指向不同仓库：询问是否克隆及克隆路径。
- 分支/worktree 已存在：复用并更新上下文。
- PR 已合并或 issue 已关闭：跳过重复步骤并反馈。
- 合并被检查阻塞：使用 `gh pr merge --auto --squash --delete-branch`。
- worktree 场景下 `gh pr merge` 报 `fatal: '<default_branch>' is already used by worktree`：原因是 gh 会尝试在当前 worktree 中 checkout 默认分支（例如 main），但该分支已被主 worktree 占用。解决方案：
  - 切换到主 worktree（`$base_repo_path`）再执行合并命令。
  - 或在非仓库目录执行 `gh pr merge <pr_number> --squash --delete-branch --repo <owner/name>`，避免受当前 worktree 影响。
  - 若仍受本地 git 限制，可先去掉 `--delete-branch` 用 API 合并，再在主 worktree 删除本地分支与 worktree。
