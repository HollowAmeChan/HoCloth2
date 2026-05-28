# 后端模型

HoCloth2 的扩展单位是 backend，不是通用 component。

每个 backend 是一个完整的 Blender 侧实现目录：

```text
hocloth2/backends/<backend_name>/
```

## 当前规划

```text
backends/
  MagicaCloth2/
  VRM/
  DynamicBone/
  Physbones/
```

## Backend 自己负责什么

每个 backend 自己负责：

- Blender properties。
- UI。
- Operators。
- Authoring snapshot。
- Frame inputs。
- Unity bridge 命令细节。
- 结果写回。
- Colliders。
- Bake/export。
- Presets。

## 为什么这样做

这些物理包的模型不同：

- MC2 有 BoneCloth、BoneSpring、MeshCloth、SelectionData、ColliderConstraint。
- VRM SpringBone 有 spring bone chain、collider groups、VRM 生态约定。
- DynamicBone 有自己的 damping/elasticity/stiffness/radius 语义。
- PhysBone 有 VRC 风格参数和限制。

强行抽象成一个通用 component，反而会让每个后端都不好写。

## Common 的边界

`hocloth2/common/` 只能放小工具，例如：

```text
paths.py
exchange.py
logging.py
host.py
version.py
```

不能放：

```text
generic_component.py
generic_collider.py
generic_solver_schema.py
```

## 第一版只实现 MC2

第一版只需要：

```text
backends/MagicaCloth2/
```

其他 backend 目录可以先空着，作为未来位置提醒。

