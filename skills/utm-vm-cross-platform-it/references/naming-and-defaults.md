# 命名与默认值约定（强推荐）

## VM 命名

默认命名（推荐）：

- `ci-Windows`
- `ci-Linux`
- `ci-macOS`

可选命名（同样支持）：

- `ci-os-windows`
- `ci-os-linux`
- `ci-os-macos`

自动选择时的优先级建议：

1. `ci-os*` 前缀
2. `ci-*` 前缀
3. 同前缀下按 OS 关键字倾向选择（Windows/Linux/macOS）

## hostname

建议 guest 内 hostname 与 VM 名称一致或可匹配（例如 `ci-Windows`），便于 DHCP leases/日志定位。

## 默认账号

- 默认用户名：`ci`
- 默认密码：`cipass`

约束：

- 只能作为“CI 兜底默认”，必须允许用户显式覆盖
- 任何日志都不得输出明文密码

覆盖策略建议（实现层面）：

- `*_SSH_USER` / `*_SSH_PASSWORD`
- `*_WINRM_USER` / `*_WINRM_PASSWORD`
- `*_SUDO_PASSWORD`（Linux）

## 为什么要保留这些强约定

- 降低无登录/无交互环境下的配置成本
- 让自动发现（utmctl list/disk guess/scan）具备稳定的候选集
- 便于统一 CI 的 VM 池与复用脚本
