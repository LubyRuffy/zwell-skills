# systemd + nginx Blue/Green Reference

这个参考文件给出一套项目无关的 Linux 单机零停机发布模板。把占住稳定入口的职责从业务进程剥离出去，改成：

- 一个稳定代理服务，固定监听业务入口端口
- 两个互斥运行的应用 slot，分别监听不同的 localhost 端口
- 一个发布脚本，负责拉起候选 slot、校验健康、切流、回滚、停旧实例

## 推荐拓扑

```text
client
  -> stable entry (:80 / :443 / 127.0.0.1:<stable-port>)
  -> local reverse proxy
  -> active slot (blue or green)

slot blue  -> 127.0.0.1:<blue-port>
slot green -> 127.0.0.1:<green-port>
```

关键点：

- 稳定入口永远不直接绑定到真实应用实例。
- 两个 slot 都只监听 `127.0.0.1`。
- 稳定代理通过 `reload` 切换 upstream，不做 stop/start。

## 文件约定

建议准备以下文件：

- `/etc/systemd/system/<app>.service`
  作用：运行稳定代理，而不是运行业务二进制
- `/etc/systemd/system/<app>-slot@.service`
  作用：运行业务实例，支持 `%i=blue|green`
- `/etc/<app>/nginx.conf`
  作用：稳定代理配置
- `<runtime-dir>/upstream.conf`
  作用：当前代理指向哪个 slot
- `<runtime-dir>/active-slot`
  作用：记录当前活跃 slot
- `<runtime-dir>/slots/blue.env`、`green.env`
  作用：为每个 slot 提供端口、二进制路径、配置路径

## systemd 模板

稳定代理 unit：

```ini
[Unit]
Description=<App> Hot Proxy
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=<base-dir>
ExecStart=/usr/sbin/nginx -p <nginx-work-dir> -c /etc/<app>/nginx.conf -g 'daemon off;'
ExecReload=/bin/kill -s HUP $MAINPID
ExecStop=/bin/kill -s QUIT $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

业务 slot unit：

```ini
[Unit]
Description=<App> Slot %i
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=<base-dir>
EnvironmentFile=-<runtime-dir>/slots/%i.env
ExecStart=/bin/sh -lc 'exec "$BINARY_PATH" --config "$CONFIG_PATH" --port "$PORT"'
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## nginx 模板

```nginx
worker_processes auto;
pid <nginx-work-dir>/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    include <runtime-dir>/upstream.conf;

    server {
        listen 127.0.0.1:<stable-port>;

        location / {
            proxy_pass http://<app>_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;

            # 这个头不是必须，但强烈建议保留，便于验证切流已生效
            add_header X-Backend-Slot $<app>_backend_slot always;
        }
    }
}
```

配套的 `upstream.conf` 可由发布脚本动态生成：

```nginx
upstream <app>_backend {
    server 127.0.0.1:<slot-port> max_fails=3 fail_timeout=5s;
    keepalive 64;
}

map $request_uri $<app>_backend_slot {
    default "<slot-name>";
}
```

## 运行时状态文件

`active-slot`：

```env
ACTIVE_SLOT=blue
```

`blue.env` / `green.env`：

```env
BINARY_PATH=<release-dir>/<app>
CONFIG_PATH=/etc/<app>/config.yaml
PORT=<slot-port>
```

## 发布算法

推荐按这个顺序实现：

1. 检测当前模式：
   - `proxy`：稳定代理已经在跑，且真实进程就是代理
   - `legacy`：当前还在跑旧的单进程直绑模式
   - `inactive`：服务未运行
2. 识别当前活跃 slot，推导空闲 slot。
3. 把新版本安装到版本化目录，例如 `<base-dir>/releases/<release-id>/`。
4. 为空闲 slot 写入新的 env 文件。
5. 启动候选 slot。
6. 对候选 slot 执行 readiness 检查，直到成功或超时。
7. 生成新的 `upstream.conf` 和 `active-slot`。
8. 先做 `nginx -t` 校验。
9. 如果当前已是 `proxy` 模式，执行 `systemctl reload <app>`。
10. 如果当前仍是 `legacy` 模式，执行一次性迁移：
    - 先停 legacy 进程
    - 再启动代理 unit
    - 若失败，恢复 legacy unit 并重启旧服务
11. 通过稳定入口再次做验证：
    - 健康接口成功
    - 可选：响应头返回新的 slot 标识
12. 只有稳定入口验证成功后，才停止旧 slot。

## 回滚规则

需要保存这两类备份：

- 切流前的 `upstream.conf`
- 切流前的 `active-slot`

失败时按类型回滚：

- 候选 slot 未 ready：
  - 不改 upstream
  - 停止候选 slot
- 代理配置校验失败：
  - 恢复旧 upstream 与旧 active-slot
  - 停止候选 slot
- 代理 reload 失败：
  - 恢复旧 upstream 与旧 active-slot
  - 重新加载旧配置
  - 停止候选 slot
- 稳定入口验证失败：
  - `proxy` 模式下恢复旧 upstream/active-slot 并 reload
  - `legacy` 首迁模式下恢复 legacy unit 并重启旧服务
  - 停止候选 slot

## 首次迁移注意事项

第一次从“业务进程直绑稳定端口”迁到“稳定代理 + 双 slot”时，风险最高。必须额外做这几件事：

- 备份旧 unit，保留 `legacy` 回滚路径
- 检测当前正在运行的真实进程命令行，不要只看 unit 文件内容
- 把这次迁移视为一次特殊 cutover，而不是普通的 proxy reload

如果首迁失败，目标不是“继续折腾新方案”，而是优先恢复旧服务对外可用。

## 健康检查要求

健康检查至少满足：

- 命中真正的 readiness endpoint，而不是只验证 TCP 端口打开
- 对 slot 直连检查一次
- 对稳定入口再检查一次
- 等待窗口按真实启动耗时设置，通常用分钟级重试

不推荐：

- 只用 `systemctl start` 成功作为 ready 信号
- 只看进程存在
- 切流后不做稳定入口验证

## Docker 变体

如果应用已经运行在 Docker/Compose 中，不必强制改回裸进程。可保持同一思想：

- 稳定入口仍由 nginx / caddy / traefik / HAProxy 承担
- `blue`、`green` 改成两个容器或两个 compose service
- 候选容器健康后再切换代理 upstream
- 旧容器在稳定入口验证成功后再停止

不要把“docker restart 容器”误认为热重启。只要稳定入口和旧实例同时被拿掉，仍然会中断。

## 最低验收清单

- 发布过程中，稳定入口端口始终持续监听
- 新实例未 ready 时不会切流
- 切流后稳定入口能证明自己已命中新实例
- 失败时旧流量路径可恢复
- 旧实例只在新路径验证成功后才下线
