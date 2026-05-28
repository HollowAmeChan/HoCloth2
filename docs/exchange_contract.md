# 数据交换契约

HoCloth2 的正式协议使用 MessagePack。JSON 只作为 debug mirror 输出，不作为运行时契约。

## 正式编码

```text
payload_encoding: msgpack
file extension: .msgpack
stream frame: uint32 little-endian byte_length + MessagePack body
```

Blender 插件本地携带 `msgpack`：

```text
_Lib/msgpack/
```

插件启动时会扫描 `_Lib/<资源包名>` 并加入 Python 搜索路径。以后新增第三方包也按这个规则放。

## Envelope

```text
schema: hocloth.exchange
schema_version: 1
backend: MagicaCloth2 | VRM | DynamicBone | Physbones
payload_type: hello | host_status | authoring_snapshot | build_request | build_output | frame_inputs | step_request | step_output | error
payload_encoding: msgpack
coordinate_space: blender_world
length_unit: meter
quaternion_order: wxyz
payload: map
```

## 关键规则

- `backend` 决定 payload 由哪个 backend 解释。
- `payload` 内部结构归 backend 自己维护。
- `common` 不定义通用 component schema。
- Unity host 收到消息后按 `backend` 分发给对应 adapter。
- 大数组优先用 MessagePack `bin` 承载二进制 buffer，而不是膨胀成 JSON 风格 float array。
- mesh/bake 仍然优先 Alembic，不进入主通信帧。

## Debug JSON

Blender 侧可以输出 `.debug.json` 方便人工查看，但它只是 MessagePack envelope 的镜像：

```text
HoCloth2_MC2_AuthoringSnapshot.msgpack       # 正式数据
HoCloth2_MC2_AuthoringSnapshot.debug.json    # 调试查看
```

## MC2 payload

第一版只定义 MC2 payload。MC2 authoring snapshot 字段方向：

```text
components[]
bone_chains[]
colliders[]
collider_groups[]
cache_outputs[]
mesh_writeback_targets[]
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

第一版暂时不做 mesh 解算，mesh/bake 后续走 Alembic 中转。

## 其他 backend

VRM SpringBone、DynamicBone、PhysBone 后续各自定义自己的 payload。它们不需要伪装成 MC2，也不需要适配一个通用 component。
