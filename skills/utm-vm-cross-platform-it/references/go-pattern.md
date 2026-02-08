# Go 项目推荐落地骨架（可按需裁剪）

目标：让“宿主机编排”与“guest 内系统测试”解耦，且默认不在开发机误触发。

## 分层

- guest 侧系统测试：用 build tags 绑定到目标 OS/场景
  - Linux：`//go:build linux && linux_integration`
  - Windows：`//go:build windows && windows_integration`
- 宿主机编排测试：
  - `//go:build integration`（仅编排，不做系统级断言）
- 三平台编排（可选）：
  - `//go:build all_platform`（宿主机里开子测试，分别触发不同 guest）

## 典型文件布局（示例）

- `integration/utmctl.go`：utmctl 封装、VM 选择、IP 发现、错误分类
- `integration/ssh_go.go`：纯 Go SSH 客户端（可选），支持 stream 输出、PTY、stdin 注入
- `integration/winrm_go.go`：WinRM 客户端（可选），封装执行 PowerShell 与超时
- `linux_integration_test.go`：guest 内 Linux 系统级验证（必须 root/sudo）
- `windows_integration_test.go`：guest 内 Windows 系统级验证（需要管理员权限）

## 环境变量命名建议（通用）

建议用“项目级前缀”避免冲突。

- 从 module/repo 名推导：例如 `FOO_`、`BAR_`
- 下面以 `${P}` 代表前缀（大写 + 下划线）

基础开关：

- `${P}LINUX_INTEGRATION=1`
- `${P}WINDOWS_SSH_INTEGRATION=1`
- `${P}WINDOWS_WINRM_INTEGRATION=1`

UTM/VM：

- `${P}UTMCTL`（覆盖 utmctl 路径）
- `${P}UTM_LINUX_VM` / `${P}UTM_WINDOWS_VM` / `${P}UTM_DARWIN_VM`
- `${P}UTM_VM`（通用兜底）

SSH：

- `${P}LINUX_SSH_HOST` / `${P}LINUX_SSH_PORT` / `${P}LINUX_SSH_USER` / `${P}LINUX_SSH_PASSWORD` / `${P}LINUX_SSH_KEY`
- `${P}WINDOWS_SSH_HOST` / `${P}WINDOWS_SSH_PORT` / `${P}WINDOWS_SSH_USER` / `${P}WINDOWS_SSH_KEY`
- `${P}DARWIN_SSH_HOST` / `${P}DARWIN_SSH_PORT` / `${P}DARWIN_SSH_USER`

Repo 路径：

- `${P}LINUX_REPO_DIR`
- `${P}WINDOWS_REPO_DIR`
- `${P}DARWIN_REPO_DIR`

权限：

- `${P}LINUX_SUDO_PASSWORD`（默认不需要；仅当 `sudo -n` 不可用时）

WinRM：

- `${P}WINDOWS_WINRM_ENDPOINT`（默认 `http://<ip>:5985/wsman`）
- `${P}WINDOWS_WINRM_USER` / `${P}WINDOWS_WINRM_PASSWORD`
- `${P}WINDOWS_HOST_IP`（宿主机在 UTM 网段的 IP，自动识别失败时手动指定）

默认值建议：

- user 默认 `ci`
- password 默认 `cipass`（只作为 CI 兜底，必须可覆盖，且不要打印）

## 命令模板（示例）

- Linux 编排：

```bash
${P}LINUX_INTEGRATION=1 \
${P}LINUX_REPO_DIR=/home/ci/src/yourrepo \
go test ./integration -tags integration -run TestUTMLinuxIntegration -count=1 -v
```

- Windows 编排（SSH）：

```bash
${P}WINDOWS_SSH_INTEGRATION=1 \
${P}WINDOWS_SSH_USER=ci \
${P}WINDOWS_REPO_DIR='C:\\src\\yourrepo' \
go test ./integration -tags integration -run TestUTMWindowsSSHIntegration -count=1 -v
```

- Windows 编排（WinRM）：

```bash
${P}WINDOWS_WINRM_INTEGRATION=1 \
${P}WINDOWS_WINRM_USER=ci \
${P}WINDOWS_WINRM_PASSWORD=cipass \
go test ./integration -tags integration -run TestUTMWindowsWinRMIntegration -count=1 -v
```
