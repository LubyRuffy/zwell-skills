# UTM 能力与网络发现

## 先绑定 VM，再探测通道

- 使用项目配置或 `utmctl list` 找到唯一目标，再用 `utmctl status <UUID>` 读取精确状态。名称与 OS 只用于筛选。找不到唯一目标时，不靠磁盘名称或开放端口猜测。确认需要且有权启动时才启动准确 UUID。启动返回未知时读当前状态，避免重复启动。
- `utmctl` 默认位于 `/Applications/UTM.app/Contents/MacOS/utmctl`。核对当前 UTM 后端和已安装版本的子命令能力。QEMU Guest Agent 的 `exec`、`file` 等需要已启用且响应的代理。不要把这些命令当成 Apple Virtualization 的兜底。对 `ip-address` 独立核实能力。只在配置了串口且证实有目标控制服务时才考虑 `attach`。
- 探针使用无副作用的身份读取，保存命令、退出状态和两路输出。曾出现 `utmctl exec` 退出为 0、stderr 却报告 `Operation not supported by the backend`／OSStatus −2700。此时该通道不可用。区分后端不支持、权限拒绝、未就绪和未知超时，避免用重复命令处理确定性拒绝。

## 地址是候选，身份由来宾证明

1. 先使用当前配置的 SSH／WinRM 地址。核对宿主路由、接口和真实 VM 网段。旧地址可能落到代理、VPN 或其他来宾。
2. 按实际能力使用 Guest Agent、来宾内网卡读数、限定接口的 DHCP／ARP、mDNS 等发现候选。冷启动 DHCP 可以在一次有界等待中查询。仅在获准且已确认的 VM 子网内做限定探测，避免整网扫描。
3. SSH 使用已固定的主机密钥，再核对来宾的 hostname、UID 和项目要求的网卡身份。WinRM 使用已配置并验证身份的端点。出现主机密钥或来宾身份不匹配时拒绝该候选，不覆盖信任记录或发送凭据。TCP 端口可达、旧 DHCP 表和 `sshd` 已监听分别只证明局部状态。

参考 [UTM 命令行与脚本说明](https://docs.getutm.app/scripting/scripting/)、[脚本字典](https://docs.getutm.app/scripting/reference/)和[串口说明](https://docs.getutm.app/advanced/serial/)。
