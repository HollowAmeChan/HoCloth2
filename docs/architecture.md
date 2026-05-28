# 架构

HoCloth2 的架构目标很简单：Blender 插件负责 authoring 和写回，Unity 程序负责实际物理解算。

不要在 Blender 侧设计一个大而全的通用物理组件模型。每个后端自己维护自己的完整实现。

## 进程边界

```text
Blender HoCloth2 插件
  backend-specific authoring
  backend-specific export
  backend-specific pose/cache apply

Unity HoCloth host
  MC2 / VRM SpringBone / DynamicBone / PhysBone adapters
  simulation
  viewport/debug UI
```

## 插件内边界

```text
hocloth2/common/
  小工具，不放业务模型

hocloth2/backends/MagicaCloth2/
  MC2 的完整 Blender 侧实现

hocloth2/backends/VRM/
  未来 VRM SpringBone 的完整 Blender 侧实现

hocloth2/backends/DynamicBone/
  未来 DynamicBone 的完整 Blender 侧实现

hocloth2/backends/Physbones/
  未来 PhysBone 的完整 Blender 侧实现
```

## MC2 第一阶段

```text
1. MagicaCloth2 backend 在 Blender 里维护 MC2 参数和绑定。
2. MagicaCloth2 backend 导出 MC2 authoring snapshot。
3. Unity host 的 MC2 adapter 构建 MagicaCloth。
4. Blender 每帧发送 MC2 frame inputs。
5. Unity 返回 MC2 solved bone transforms。
6. MagicaCloth2 backend 写回 Blender pose。
```

## 扩展其他后端

新增后端时，不改 MC2 的内部模型。

例如 VRM SpringBone：

```text
hocloth2/backends/VRM/
  props.py
  ui.py
  snapshot.py
  inputs.py
  apply.py
```

它可以和 MC2 共享 `common` 里的 JSON、路径、启动 Unity host helper，但不共享 component schema。

## 统一的最小内容

可以统一：

- 插件根目录定位。
- Unity host 路径查找和启动。
- 基础 JSON envelope。
- 版本检查。
- 日志。
- 打包流程。

不统一：

- Component 参数模型。
- Collider 参数模型。
- Solver payload。
- UI 布局。
- 写回策略。
- Bake 策略。

