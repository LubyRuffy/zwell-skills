# Terminal 所有权与清理

## 为什么不能只靠 runner 的 finally

runner 的 app／子进程 cleanup 不包含启动它的外层 Terminal 标签页。`.command` 已显示“进程已完成”仍可能留下 Terminal 持有的 PTY。成功、失败、超时、取消和控制端断线都必须收尾，不能以 exit 0 代替。

## 统一入口

`scripts/terminal_session.py` 是**来宾端**的独立守护包装器。先把脚本放到已核验身份的来宾私有路径，所有测试控制者使用同一个私有 state 目录。第一次使用必须在目标来宾验证 Terminal AppleEvents 权限和 `lsof` 可用，分别执行成功／失败／取消／超时，验收每次自有标签页消失，并对比 Terminal 进程持有的 PTY master 数与开始前基线。标签页消失、TTY 从端无持有者是包装器的检查，不等于已核验 macOS 的 PTY master 回收。

1. 在既有无 PTY 通道，使用 **与 `.command` 完全相同的来宾 Python 绝对路径**运行：

```sh
/private/verified/guardian-python3 /private/verified/terminal_session.py status \
  --state "$HOME/.local/state/utm-terminal"
```

   只有退出码为 0 且输出 `ready` 才允许打开一个新的专用测试 Terminal 标签页；不得在用户手工终端中调用 `run`。包装器以能力探测为准：守护进程必须能用 `os.waitid` 和 `WNOWAIT` 保留子进程身份（macOS 上 CPython 3.13 起提供）；探测不启动子进程。若缺失，不开标签页、不启动测试，不自动安装解释器；改用现有且经验证的兼容解释器，或留在无 PTY 路径。`status` 不预约下一次启动：控制端必须串行遵守此前置检查；包装器的原子门禁拒绝并发执行，但不能拦截绕过它打开的 Terminal 标签页。
2. 原 `.command` 不再直接启动 runner，而只调用下面的包装并立即结束。不要附加 `read`、交互 shell 或新 Terminal：

```sh
/private/verified/guardian-python3 /private/verified/terminal_session.py run \
  --state "$HOME/.local/state/utm-terminal" \
  --evidence /private/new-round/terminal --timeout 60 \
  -- /private/verified/python3 /private/frozen/tools/native_macos_case.py ...
exit $?
```

路径替换为实际已核验的解释器、冻结源码和独立证据目录。既有项目的 runner 资源租约和子进程／数据清理仍需保留。命令不得将秘密放在 argv。

3. 包装器绑定当前 stdin TTY，并给这个**专用**标签页设置唯一所有权标题。独立 guardian 将工作输出保存至证据文件，超时或 `cancel` 请求终止本轮新建进程组。它不会按标题前缀／窗口索引批量关闭，也不改变全局 Terminal 或锁屏设置。逃离本轮进程组的服务仍由项目 runner 的既有所有权清理负责。
4. 通过已有无 PTY 通道执行 `python3 terminal_session.py cancel --state ...` 取消。控制端断线不杀 guardian；即使客户端不再等待，guardian 仍有有限时限。
5. 读取 `result.json`：业务退出状态与 `process_cleanup_complete`、`terminal_cleanup_complete` 分别判定。只在唯一令牌和 TTY 绑定匹配、tab 不 busy、标签页已关闭且该 TTY 无持有者时解锁下一轮。权限不足、身份歧义、进程清理异常或 guardian 消失均保留 active 门禁，禁止反复补开终端。不要为恢复任务直接删除 active；先检查 owner.json、原请求、原进程和 PTY。

## 已有残留

先只读核对窗口／标签页的 TTY、测试命令路径、完成状态和进程占用。只关闭已确证是本次测试遗留且已结束的标签页。不能按 `start.command` 等常见标题猜归属、全关 Terminal 或杀用户交互 shell。每批关闭后记录数量和 PTY 回收，仍有运行任务时保留。

## 回归范围

`python3 -m unittest discover -s scripts -p 'test_terminal_session.py'` 覆盖成功、非零退出、超时、取消、启动失败、遗留子进程组、控制端退出后的 guardian、busy／身份歧义拒绝、关窗而 PTY 未释放、下轮 fail-stop，以及等待 API 不兼容时不开标签页、不启动测试。这些是带 Terminal 边界替身的控制逻辑测试，不替代真实来宾 AppleEvents／PTY 验收。
