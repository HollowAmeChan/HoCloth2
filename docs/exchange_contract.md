# 数据交换契约

HoCloth2 只统一最小 envelope，不统一每个后端的业务 payload。

## Envelope

```text
schema: hocloth.exchange
schema_version: 1
backend: MagicaCloth2 | VRM | DynamicBone | Physbones
payload_type: authoring_snapshot | frame_inputs | build_output | step_output
coordinate_space: blender_world
length_unit: meter
quaternion_order: wxyz
payload: object
```

## 关键规则

- `backend` 决定 payload 由哪个 backend 解释。
- `payload` 内部结构归 backend 自己维护。
- `common` 不定义通用 component schema。
- Unity host 收到消息后按 `backend` 分发给对应 adapter。

## MC2 payload

第一版只定义 MC2 payload。

MC2 authoring snapshot 可以沿用旧 HoCloth 中已经验证过的字段方向：

```text
components[]
bone_chains[]
colliders[]
cache_outputs[]
```

MC2 的 `serialize_data` 尽量贴近 MC2 命名：

```text
clothType
rootBones
connectionMode
gravity
gravityDirection
damping
radius
inertiaConstraint
tetherConstraint
distanceConstraint
triangleBendingConstraint
angleRestorationConstraint
angleLimitConstraint
springConstraint
colliderCollisionConstraint
```

## 其他 backend

VRM SpringBone、DynamicBone、PhysBone 后续各自定义自己的 payload。它们不需要伪装成 MC2，也不需要适配一个通用 component。

## 输出

step output 至少要能让对应 backend 写回 Blender。

MC2 第一版输出：

```text
runtime_state
transforms[]
mesh_outputs[]  # 暂时可为空
```

Transform 字段由 MagicaCloth2 backend 自己定义和消费。可以保留 `write_mode`，因为 MC2 写回语义比较敏感。

