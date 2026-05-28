# Unity Backend

Unity 后端是一个外部物理宿主程序。它可以同时包含多个 adapter，但每个 adapter 自己维护自己的实现。

## 当前 Unity 工程

```text
D:\Unity_Project\HoClothUnity
```

## Unity Host 职责

- 启动本地服务。
- 提供简易 viewport/debug UI。
- 接收 Blender 消息。
- 按 `backend` 字段分发给对应 adapter。
- 返回 build/step 结果。

## Adapter 职责

```text
MC2 adapter
  构建 MagicaCloth / colliders
  映射 MC2 serialize_data
  Step 后返回 MC2 solved transforms

VRM SpringBone adapter
  未来自己实现

DynamicBone adapter
  未来自己实现

PhysBone adapter
  未来自己实现
```

Unity 侧也不要做一个过度抽象的通用物理组件。Host 管进程、消息、viewport、session；adapter 管具体包。

## 第一版

第一版只做 MC2 adapter：

- BoneCloth。
- BoneSpring。
- MC2 colliders。
- Bone transform 输出。

MeshCloth 和 Alembic 先不做。

