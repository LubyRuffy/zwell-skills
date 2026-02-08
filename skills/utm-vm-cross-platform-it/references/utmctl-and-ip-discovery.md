# utmctl 与 IP 发现（实现要点）

## utmctl 路径

- 默认：`/Applications/UTM.app/Contents/MacOS/utmctl`
- 必须允许覆盖：例如 `*_UTMCTL`（具体前缀按项目约定）

## VM 标识

建议支持两类标识：

- VM 名称（更好读）
- VM UUID（更稳定）

建议的选择优先级：

1. 显式配置（例如 `*_UTM_WINDOWS_VM` / `*_UTM_LINUX_VM` / `*_UTM_DARWIN_VM` / `*_UTM_VM`）
2. `utmctl list` 自动挑选：
   - 优先 `ci-os*`，其次 `ci-*`
   - 再按 OS 关键字（windows/linux/macos/darwin）选择
3. 若 `utmctl list` 不可用：
   - “磁盘猜测”常见 bundle 是否存在：
     - `~/Library/Containers/com.utmapp.UTM/Data/Documents/<name>.utm`
4. 仍失败：
   - 端口/网段扫描兜底（见下）

## 启动 VM

- best-effort：尝试 `utmctl start --hide <vm>`，再尝试 `utmctl start <vm>`
- 失败不要立即终止：很多场景下 VM 已经在运行或后端行为不一致

## 获取 IP

- 优先 `utmctl ip-address --hide <vm>`
- 必须重试（VM 冷启动 DHCP 需要时间）
- 解析输出时，兼容：
  - 每行一个 IP
  - 文本里夹杂 `192.168.64.10/24` 这种 CIDR token

## 明确不可恢复错误，直接让上层 fallback

常见不可恢复：

- `Operation not supported by the backend.`
- AppleEvent/OSStatus 类错误（例如权限/TCC/后端限制）

这类错误重试没有意义，应直接回退到：

- 用户显式提供 `*_SSH_HOST` / `*_WINRM_ENDPOINT`
- 或走扫描兜底

## 扫描兜底（只作为最后手段）

- Windows WinRM：优先扫 5985
- Windows SSH：扫 22
- Linux/macOS SSH：扫 22

扫描 CIDR 建议可配置（例如默认 `192.168.64.0/24`），并限制超时与并发，避免 CI 长时间 hang。
