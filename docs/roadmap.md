# 路线图

## Stage 0: 仓库形态

- 创建干净 HoCloth2 仓库。
- 简化为 `common/ + backends/ + bundled/`。
- 明确不做通用 component。
- 旧 HoCloth 只作为参考。

## Stage 1: 最小插件壳

- 添加 `__init__.py`。
- 添加基础注册/注销。
- 添加一个 HoCloth2 面板入口。
- 添加 common 路径和日志工具。

## Stage 2: MagicaCloth2 backend 原型

- 在 `backends/MagicaCloth2/` 里添加 props/ui/operators。
- 导出 MC2 authoring snapshot。
- 导出 MC2 frame inputs。
- 写 MC2 pose apply。

## Stage 3: Unity Host MC2 原型

- Unity host 启动服务。
- 接收 backend=`MagicaCloth2` 的消息。
- 构建 MC2 BoneCloth/BoneSpring。
- Step 后返回 solved bone transforms。

## Stage 4: Live Loop

- Blender 播放时每帧发送 inputs。
- 接收 transforms。
- 写回 pose bones。

## Stage 5: 本地打包

- 写 `tools/sync_unity_host.ps1`。
- 写 `tools/package_addon.ps1`。
- 生成 Blender 可安装 zip。

## Stage 6: 第二后端

- 原型稳定后再选 VRM SpringBone / DynamicBone / PhysBone 之一。
- 新后端完整放到自己的 `backends/<name>/` 目录。
- 不改 MC2 内部结构。

## Stage 7: GitHub Release

- 第一版原型跑通后再做自动 release。

