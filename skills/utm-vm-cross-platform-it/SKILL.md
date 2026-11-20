---
name: utm-vm-cross-platform-it
description: Run or design UTM integration tests for Linux, Windows and macOS guests. Recover guest access or a locked GUI session and verify macOS native behavior using the project's guest runner, including checkout launches and release candidates.
---

# UTM 来宾集成测试与原生验收

宿主负责编排、传输和收集证据。需要验证的系统动作或原生界面在目标来宾中执行。先读项目现有入口、授权、验收标准和资源互斥规则。

## 选择路径

- **系统集成测试**（信任库、安装器、驱动、服务或权限）：优先复用现有来宾执行入口。新建 Go 编排器时用 Go 实现 SSH／WinRM，按需读[前置条件](references/requirements.md)和 [Go 编排骨架](references/go-pattern.md)。
- **Mac 原生验收**先读项目的原生测试快路径和场景合同，例如 `eino-swarm` 的 `docs/NATIVE_TESTING_FAST_PATH.md`。按范围完成非 GUI 检查，冻结候选和 helper，按[前置条件](references/requirements.md)检查来宾容量，再在项目指定来宾中串行运行。按[验收与收尾](references/macos-recovery.md#验收范围与收尾)核对本轮原件和实际状态。
- **访问失败**先定位命令通道、来宾登录或当前执行主体的权限。网络和后端能力参见 [UTM 能力与网络发现](references/utmctl-and-ip-discovery.md)。Mac 锁屏、黑帧、Screen Sharing 或 Terminal 交接参见 [Mac 来宾恢复与验收](references/macos-recovery.md)。

## 执行边界

1. 用当前 VM UUID、后端、状态和项目的来宾身份配置绑定目标。名称、旧 IP 和扫描结果只用来定位候选。SSH 核对可信主机密钥和来宾身份，Windows 仅在已配置时用 WinRM。UTM Guest Agent 命令按后端和实际探针结果准入，退出码为零仍要检查错误流和有效回执。
2. 分别取得命令通道、当前桌面、实际执行主体的权限和原生行为证据。宿主锁屏时按已有授权查找独立通道。有可用通道时，把新鲜画面核验、必要登录、会话保持与 runner 启动放在同一次受控交接内。只有来宾原生窗口和本轮业务断言能验收原生行为。
3. 使用项目已有的宿主和来宾锁与场景时限。每个用例拥有独立包副本、数据和子进程。先保留首错，再等待自有进程退出并确认清理，随后才开始新用例。超时且结果未知时查证原请求。准入受阻时保留具体原因和待验收状态，继续独立可推进的工作。

## 兼容与凭据

沿用既有 CI 配置和[命名约定](references/naming-and-defaults.md)。新流程从项目批准的私有来源取凭据，经已授权的内存或标准输入通道传递。下行是仍直接解析本文件的旧测试工具的兼容接口，仅供明确预置该值且已授权的隔离 CI 镜像使用。迁移旧工具到私有来源后再移除此接口。

默认账号 `ci/cipass`
