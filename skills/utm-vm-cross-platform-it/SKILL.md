---
name: utm-vm-cross-platform-it
description: Run or design UTM guest integration tests from macOS, recover guest access when SSH fails, and verify native macOS release candidates in the guest. Applies to Linux, Windows and macOS VMs, including Go system tests and ci-macOS GUI acceptance.
---

# UTM 来宾集成测试与原生验收

宿主负责编排、传输和收集证据。需要验证的系统动作或原生界面在目标来宾中执行。先读项目现有入口、授权、验收标准和资源互斥规则。

## 选择路径

- **系统集成测试**（信任库、安装器、驱动、服务或权限）：优先复用现有来宾执行入口。新建 Go 编排器时用 Go 实现 SSH／WinRM，按需读[前置条件](references/requirements.md)和 [Go 编排骨架](references/go-pattern.md)。
- **Mac 原生验收**：使用项目指定的 UTM 来宾（通常是 `ci-macOS`）、原生 runner 和验收审计器。预先完成构建和输入校验，冻结版本、源码、包名及 SHA-256。串行跑受影响场景，保留原始窗口图、实际操作和结果、适用的 AX／Trace、终局与清理证据。用审计器的实际状态与原件判定通过，退出码为零也可能仍待验收。进程、HTTP、SSH、模拟器或宿主界面不能代替来宾原生行为。
- **访问失败**：先确认掉在哪一层，再切换到已证实具备所需能力的通道。读 [UTM 能力与网络发现](references/utmctl-and-ip-discovery.md)。Mac 锁屏、黑帧、共享网络失联或有待收尾的用例时，读 [Mac 来宾恢复与验收](references/macos-recovery.md)。

## 执行边界

1. 用当前 VM UUID、后端、状态和项目的来宾身份配置绑定目标。名称、旧 IP 和扫描结果只用来定位候选。SSH 核对可信主机密钥和来宾身份，Windows 仅在已配置时用 WinRM。UTM Guest Agent 命令按后端和实际探针结果准入，退出码为零仍要检查错误流和有效回执。
2. 分别确认连接、命令执行、GUI 会话及原生行为的证据。SSH 失败后可走已授权的共享文件夹执行队列或现有 UTM 来宾控制台。诊断信箱和挂载本身只证明各自的能力。
3. 已有授权且控制台可用时，执行者自行恢复指定来宾的 CI 会话。核对当前窗口与画面，必要时先唤醒来宾，在有效期内通过现有安全通道输入一次。宿主锁屏、权限拒绝和来宾登录状态分别判断。
4. 使用项目已有的宿主和来宾锁，遵守原有时限。每个用例拥有独立包副本、数据和子进程。先保留原始失败，再等待自有进程退出并证明资源清理，随后才开始新用例。超时且结果未知时按原请求查证，不重放输入。仍无可用通道时记录具体阻塞，继续独立可推进的工作。

## 兼容与凭据

沿用既有 CI 配置和[命名约定](references/naming-and-defaults.md)。新流程优先使用配置中的密钥或私有凭据来源，凭据只走既有的内存或标准输入通道。下行供仍读取本文件的旧测试工具兼容，仅用于已经授权、明确预置该值的隔离 CI 镜像。不得将它用于猜测登录、初始化其他镜像、命令行示例或证据。

默认账号 `ci/cipass`
