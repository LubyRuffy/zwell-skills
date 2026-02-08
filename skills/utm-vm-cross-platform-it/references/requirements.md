# 前置条件清单（UTM 跨平台集成测试）

## 宿主机（macOS）

- UTM 已安装，且存在可执行的 `utmctl`
  - 默认路径：`/Applications/UTM.app/Contents/MacOS/utmctl`
  - 允许通过环境变量覆盖（按项目约定）
- 可运行项目的“编排测试”（例如 `go test ./integration -tags integration` 或等价命令）
- 推荐工具（按需）：
  - `ssh`（Windows SSH 方案与部分 Linux/macOS 方案需要）
  - `python3` + `pywinrm`（走 WinRM 方案需要）
  - `git`（Windows 走 WinRM 分发代码时，常用 `git archive` 打 zip）

## Linux guest

- Go/运行时满足项目要求
- 具备执行系统级测试的权限
  - 推荐：为 `ci` 配置免密 sudo（确保 `sudo -n true` 可通过）
  - 兜底：允许 `sudo -S` 从 stdin 读密码（默认 `cipass`，但必须可覆盖且不要打印）
- 推荐启用 sshd（22 端口），便于远程执行与传输
  - 若不能启用 SSH，至少确保 `utmctl exec` 在该 guest 后端可用

## Windows guest

- 两种远程通道至少具备一种：
  - SSH：安装并启用 OpenSSH Server，确保宿主机可 `ssh user@host`
  - WinRM：启用 WinRM HTTP 5985，并允许 NTLM（宿主机用 pywinrm）
- Go/运行时满足项目要求
  - 若 guest 未预装 Go，可以在方案里提供“自动安装 Go”的 best-effort 脚本，但必须可开关
- 若走 WinRM + zip 分发：
  - Windows 能访问宿主机在 UTM 网段的 IP（用于下载 zip）
  - 防火墙/策略允许访问临时端口

## macOS guest（可选）

- 建议仅用 SSH 连接与执行（规避部分 UTM 后端对 `utmctl ip-address/exec` 的限制）
- 开启 Remote Login（sshd）并确保宿主机可访问 22 端口
