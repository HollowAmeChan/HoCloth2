# 路径大纲

这版路径只保留必要结构。不要为了未来扩展提前拆太多层。

## 顶层

```text
HoCloth2/
  __init__.py
  README.md
  hocloth2/
  bundled/
  docs/
  tools/
  tests/
```

## `hocloth2/`

```text
hocloth2/
  common/
  backends/
    MagicaCloth2/
    VRM/
    DynamicBone/
    Physbones/
```

## `common/`

只放明确复用的小东西：

- addon 路径定位。
- 简单日志。
- MessagePack/envelope 小工具。
- Unity host 启动/连接的基础 helper。
- 坐标/矩阵的最小通用函数。

不要在这里做通用 component、通用 collider、通用 solver schema。

## `backends/<name>/`

每个 backend 自己是一套完整插件子系统。

一个 backend 可以自己放这些文件：

```text
backends/MagicaCloth2/
  __init__.py
  props.py
  ui.py
  operators.py
  snapshot.py
  inputs.py
  bridge.py
  apply.py
  colliders.py
  bake.py
  presets.py
```

这些文件不是一开始都要建。需要哪个建哪个。

backend 自己拥有：

- Blender PropertyGroup。
- UI 面板。
- Operators。
- Authoring snapshot。
- Frame inputs。
- Runtime bridge。
- Pose 写回。
- Collider 映射。
- Bake/export。

## 为什么不做通用 component

MC2、VRM SpringBone、DynamicBone、PhysBone 的参数模型和运行时语义不同。提前抽象一个通用 component 会导致两种问题：

- 抽象过薄，最后各 backend 还是绕过去。
- 抽象过厚，后续每个 backend 都被迫适配一个不自然的模型。

所以 HoCloth2 只统一外围：插件目录、Unity host 查找、打包、最小消息 envelope。业务模型由 backend 自己维护。

## `bundled/`

```text
bundled/
  unity_host/
    windows-x64/
```

这里放 Unity Player build 后的可运行文件。它让裸插件目录和发布 zip 都能用相同相对路径找到 Unity 后端。

不要把 Unity 工程源码放进这里。

## `tools/`

未来脚本：

```text
tools/
  sync_unity_host.ps1
  package_addon.ps1
```

`sync_unity_host.ps1` 从 Unity build 输出复制文件到 `bundled/unity_host/windows-x64`。

`package_addon.ps1` 生成 Blender 可安装的 zip。

## `docs/`

只保留能指导实现的文档，不堆过度设计。

