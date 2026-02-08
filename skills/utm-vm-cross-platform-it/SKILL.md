---
name: utm-vm-cross-platform-it
description: Design and implement cross-platform integration testing orchestrated from a macOS host using UTM virtual machines (Linux/Windows/macOS guests) via utmctl + SSH/WinRM. Use when you need to run real system-level integration tests across OSes (e.g., certificate/trust store, drivers, installers, privileged operations), especially on Apple Silicon, while keeping CI conventions like ci-Windows/ci-Linux/ci-macOS naming and default ci/cipass accounts.
---

# UTM VM 跨平台集成测试（宿主机编排）

## 目标

在 macOS 宿主机上，用 UTM 启动/控制 Linux、Windows（可选 macOS）虚拟机，并在 guest 内执行真实集成测试；宿主机负责“编排与触发”，guest 负责“实际系统级动作”。要求保留 CI 约定：VM 命名 `ci-Windows/ci-Linux/ci-macOS`（或 `ci-os-*`），默认账号 `ci/cipass`，优先 SSH，Windows 可选 WinRM，必要时 `utmctl exec` 兜底。

## 工作流（按顺序执行）

### 1. 明确范围与成功标准

- 明确“宿主机 OS”：默认只支持 macOS 宿主机（UTM + utmctl）。若用户要求 Linux 宿主机，说明不属于本技能的默认路径。
- 明确“需要覆盖的 guest OS”：Linux / Windows / macOS；以及是否要三平台一次性编排（类似 `all_platform`）。
- 明确“集成测试要验证的系统动作”：例如系统信任库、系统证书存储、安装器、服务管理、权限提升等。
- 明确“可重复性与观测性要求”：必须 `-v` 输出；必须可设置超时；失败要能定位到是“启动/找 IP/连不上/权限不足/测试失败”。

### 2. 固化命名与默认账号（强约定）

- VM 名称与 hostname：默认用 `ci-Windows`、`ci-Linux`、`ci-macOS`（或 `ci-os-windows`/`ci-os-linux`/`ci-os-macos`），并在自动选择时优先 `ci-os*`，其次 `ci-*`。
- 默认账号：`ci`；默认密码：`cipass`。

把这些约定写进项目文档，并在代码里实现“可覆盖但有默认”的行为（环境变量/配置文件均可）。

更细的建议见：`references/naming-and-defaults.md`。

### 3. 选择触发通道：SSH 优先，WinRM/utmctl 兜底

- Linux guest：优先 SSH（能 stream 输出、适配 sudo/root）；若 SSH 端口不通且 utmctl 存在，fallback `utmctl exec`。
- Windows guest：优先 SSH（OpenSSH Server）；可选 WinRM（5985 + NTLM，pywinrm）；两者都不可用时 fallback `utmctl exec`。
- macOS guest：优先 SSH（规避部分后端对 `ip-address/exec` 的限制）。

准备清单见：`references/requirements.md`。

### 4. 实现 VM 发现、启动、获取 IP（可靠性优先）

- `utmctl` 路径允许覆盖（默认 `/Applications/UTM.app/Contents/MacOS/utmctl`）。
- VM 标识选择优先级：显式配置 > `utmctl list` 自动挑选（按 `ci-os*`/`ci-*`）> 磁盘猜测（Documents 下 `.utm` bundle）> 端口扫描兜底。
- 获取 IP：`utmctl ip-address` 重试；遇到后端不支持或 AppleEvent/OSStatus 错误时，直接让上层走 fallback（扫描或 SSH 直连配置）。
- 启动 VM：best-effort 先 `utmctl start --hide`，再 `utmctl start`（兼容 headless/交互差异）。

实现要点见：`references/utmctl-and-ip-discovery.md`。

### 5. 设计“宿主机编排测试”与“guest 内系统测试”的分层

- 把系统级断言放到“guest 侧测试”（例如 Linux root 写 trust store、Windows 写证书存储）。
- 宿主机侧只做：启动 VM、发现 IP、传输代码/定位 repo、远程执行命令、采集输出、做最小限度的健康检查。
- 若项目是 Go：建议用 build tags 或等价机制区分。

Go 的落地骨架见：`references/go-pattern.md`。

### 6. 代码分发/同步（可选但常用）

- 若 guest 里已预置 repo：通过配置 `*_REPO_DIR` 直接使用。
- 若未预置：实现“宿主机打包并传输”的路径。
  - Linux：tar.gz + SSH stdin 解压
  - Windows：优先 WinRM 路径用宿主机临时 HTTP server 分发 zip；或用 scp/ssh（若可用）

### 7. 权限与凭据（必须可覆盖，默认可用）

- Linux：优先 `sudo -n`；失败后可选 `sudo -S`（stdin 注入密码）。默认账号 `ci/cipass` 时，允许在 CI 自动兜底，但不要在日志里打印密码。
- Windows：测试若需要管理员权限，要求 guest 侧账号具备管理员权限；WinRM/SSH 都用 `ci/cipass` 作为默认，但必须允许覆盖。

### 8. 文档化与可运行命令

- 输出一份“与业务无关”的独立文档（放到项目 `docs/`），内容至少包括：
  - VM 命名与默认账号约定
  - guest 侧前置条件（SSH/WinRM/Go/权限）
  - 一键运行命令（包含 env vars）
  - 常见失败与排障
  - CI 运行形态建议（登录会话 vs no-login）

### 9. 验证与回归

- 修改代码后必须保证项目可编译、相关测试可通过。
- 新增后端函数要补单测（如果项目有这类约束）。
- 集成测试默认应可被显式开关控制（例如通过 env var 启用），避免本地开发误触发。

## 参考资料（按需加载）

- `references/requirements.md`：宿主机/guest 前置条件清单 
- `references/naming-and-defaults.md`：`ci-*` 命名与 `ci/cipass` 约定、可覆盖策略 
- `references/utmctl-and-ip-discovery.md`：utmctl 使用与 IP 发现/兜底策略 
- `references/go-pattern.md`：Go 项目的推荐结构（build tags、编排测试/guest 测试分层、命令模板） 
