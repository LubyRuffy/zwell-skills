# zwell-skills

集中管理个人 Codex Skills。

## 安装与使用

1. 克隆仓库：

```bash
git clone https://github.com/LubyRuffy/zwell-skills.git
```

2. 将需要的技能复制到 `CODEX_HOME`：

```bash
# CODEX_HOME 默认是 ~/.codex
export CODEX_HOME=${CODEX_HOME:-~/.codex}

# 安装单个技能
cp -R zwell-skills/skills/github-issue "$CODEX_HOME/skills/local/"
```

3. 在 Codex 中直接使用技能名称即可触发。

## 已有技能

- github-issue：GitHub Issue 闭环处理流程（创建 worktree、修复、PR、合并、清理）。
