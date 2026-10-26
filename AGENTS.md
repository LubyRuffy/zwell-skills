# 技能仓库开发规则

本仓库的 `skills/<name>/` 是个人技能的唯一维护源，发布目标是
`LubyRuffy/zwell-skills`。多个客户端通过 `npx skills` 管理的全局安装使用这些技能。

## 交付契约

- 在源码中修改技能，并同步受影响的 `agents/openai.yaml` 和 README。
- 验证和 review 后提交、推送到 GitHub，核对远端主线确实包含本次完整结果，并同步本地 `main`。
- 发布后先盘点 `npx skills list --global --json` 和实际客户端入口，再运行
  `npx skills add LubyRuffy/zwell-skills --skill <name> --global --yes --agent <已安装客户端>` 重装指定技能。
  共享目录可选择一个已有的共享目录客户端更新，但必须检查所有已有入口；独立副本须覆盖其对应客户端。
- `npx skills update <name> --global --yes` 会重新检测客户端，仅在确认不会增加安装范围时使用。
  首次安装由本次需求确定客户端范围；不能用更新旧技能的授权增加客户端。
- 必须检查安装锁的来源、技能目录版本，以及此前已安装客户端的实际入口和文件内容。
  仅更新源码或本地副本不能宣称交付完成；不得手工复制到客户端目录冒充安装更新。
- 只更新本次技能，不执行不带技能名的批量更新；保留其他技能和客户端配置。
  不用 `--all` 或增加客户端来绕过现有安装关系。
- 本仓库的技能更新沿用用户已明确的发布与安装要求，默认交付包含上述完整链路；
  不能因后续请求简写为“修复提示词”就停在本地副本。用户明确限定草稿或禁止推送、安装时遵守该限制。

## 验证

```bash
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" skills/gogogo
git diff --check
npx skills list --global --json
```

校验目标替换为实际修改的技能。结构校验不能代替行为验证；技能包含可执行检查时，
在隔离的临时仓库中验证其成功、拒绝和必要的并发场景。测试证据放在仓库外。
完成前核对实际安装文件与发布提交中的 `skills/<name>/` 一致；安装命令退出成功不能代替该检查。
