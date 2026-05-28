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
- 骨骼 Transform 不能按普通 Unity Transform 理解，必须遵守 `bone_transform_contract.md`。
- 时间推进必须遵守 `time_contract.md`：传输时间以 `time_seconds` 的现实秒为准，Blender 帧率只解释帧号，Unity tick rate 和 MC2 simulation frequency 是独立后端设置。

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


## MC2 runtime step

`build_request` 成功后，Unity 返回：

```text
payload.handle: int
payload.received_chain_count: int
payload.received_bone_count: int
payload.received_collider_count: int
```

Blender 后续用 `handle` 发送 `step_request`：

```text
payload.handle: int
payload.frame_inputs.frame: int
payload.frame_inputs.time: float
payload.frame_inputs.delta_time: float
payload.frame_inputs.bone_transforms[]:
  component_id: string
  armature_name: string
  bone_name: string
  pose_world_matrix_b: float[16] row-major
  pose_parent_local_matrix_b: float[16] row-major
  pose_world_translation_b: float[3]
  pose_world_rotation_b: float[4] wxyz
  pose_world_scale_b: float[3]
```

兼容字段 `world_matrix/world_translation/world_rotation/world_scale` 暂时仍会输出，它们等同于对应的 Blender 空间 `*_b` 字段，只用于旧代码和 debug。Unity 侧不能把这些字段直接当作 Unity Transform。

Unity 返回 `step_output`：

```text
payload.ok: bool
payload.handle: int
payload.step_index: int
payload.received_bone_count: int
payload.solved_bone_count: int
payload.sample_phase: before_input_apply
payload.started_mc2_build_count: int
payload.completed_mc2_build_count: int
payload.failed_mc2_build_count: int
payload.pending_mc2_build_count: int
payload.bone_transforms[]:
  component_id: string
  armature_name: string
  bone_name: string
  parent_index: int
  output_world_matrix_b: float[16] row-major
  output_world_translation_b: float[3]
  output_world_rotation_b: float[4] wxyz
  write_mode: string
```

兼容字段 `world_matrix/world_translation/world_rotation/world_scale` 暂时仍会返回，它们等同于对应的 Blender 空间输出。

当前第一版 `step_output` 采用连续读取语义：每次 step 先返回当前可读输出，再提交本次输入给后续 Unity/MC2 tick 使用。返回 payload 会带 `sample_phase: before_input_apply`。真正接入 MC2 时必须遵守 `bone_transform_contract.md` 中的 solver 空间转换和写回策略。

## 其他 backend

VRM SpringBone、DynamicBone、PhysBone 后续各自定义自己的 payload。它们不需要伪装成 MC2，也不需要适配一个通用 component。

