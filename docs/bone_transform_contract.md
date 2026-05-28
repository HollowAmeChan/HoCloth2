# 骨骼变换契约

Blender 的 Armature/PoseBone 变换不能直接等同于 Unity 的 Transform。HoCloth2 和 HoClothUnity 之间必须把“数据空间”和“求解空间”分开，否则 MC2 即使能运行，也会在骨骼轴向、父子局部矩阵、重力方向和写回姿态上产生隐性错误。

本文档定义 MC2 第一版骨骼解算使用的专用契约。

## 基本规则

- MessagePack 是正式传输格式，JSON 只作为 debug mirror。
- 矩阵数组使用 `float[16]` row-major 存储。
- 矩阵数学语义为列向量形式：`world = matrix * local`。
- 四元数顺序为 `wxyz`。
- 长度单位为米。
- Blender 侧字段必须保留 Blender 原始语义，不伪装成 Unity Transform。
- Unity 侧必须显式执行 Blender -> Unity solver 的轴转换，再创建 MC2 Transform 层级。

## 坐标空间

### Blender 原始空间

协议 envelope 的 `coordinate_space: blender_world` 表示 payload 中默认字段来自 Blender 原始世界空间：

```text
Blender X: right
Blender Y: back/front axis
Blender Z: up
Blender bone local +Y: head -> tail
```

Blender `PoseBone.matrix` 是 armature object space 下的最终 pose 矩阵，不是 Unity 的 local Transform。根骨和子骨也不能只靠一个 world matrix 还原出可靠的 Unity 骨架语义。

### Unity solver 空间

Unity 内部 MC2 运行在 solver 空间。第一版固定使用：

```text
axis_conversion: BLENDER_Z_UP_NEG_Y_FORWARD_TO_UNITY_Y_UP_POS_Z_FORWARD
position_u = (x_b, z_b, -y_b)
```

对应 4x4 基变换：

```text
C = [
  1,  0,  0, 0,
  0,  0,  1, 0,
  0, -1,  0, 0,
  0,  0,  0, 1
]
```

矩阵转换：

```text
M_u = C * M_b * inverse(C)
M_b = inverse(C) * M_u * C
```

位置转换只使用 `C * p_b`。方向、旋转和矩阵必须使用完整基变换，不能只交换三个 float。

## Build Snapshot 字段

每个 bone chain 必须声明：

```text
transform_contract: bone_transform_v1
axis_conversion: BLENDER_Z_UP_NEG_Y_FORWARD_TO_UNITY_Y_UP_POS_Z_FORWARD
matrix_convention: row_major_column_vector
bone_primary_axis: blender_local_positive_y
```

每个 bone 至少需要：

```text
name
parent_name
parent_index
length
head_local
tail_local
rest_parent_local_matrix_b
rest_world_matrix_b
rest_local_translation
rest_local_rotation
rest_world_rotation
rest_world_scale
```

兼容字段：

```text
rest_local_to_world_matrix
```

`rest_local_to_world_matrix` 等同于 `rest_world_matrix_b`，只为旧代码和 debug JSON 保留。

## Frame Input 字段

每帧输入必须优先发送 Blender 语义字段：

```text
component_id
armature_name
bone_name
pose_world_matrix_b
pose_parent_local_matrix_b
pose_world_translation_b
pose_world_rotation_b
pose_world_scale_b
```

兼容字段：

```text
world_matrix
world_translation
world_rotation
world_scale
```

这些兼容字段等同于对应的 `*_b` 字段，但 Unity 侧不能把它们直接当 Unity Transform 使用。

## Unity Runtime 行为

Unity MC2 adapter 在 build 时执行：

```text
1. 读取 Blender rest_parent_local_matrix_b。
2. 转换为 Unity solver local matrix。
3. 按 parent_index 创建 mirror Transform hierarchy。
4. 对 rootBones 绑定 MC2 root Transform。
5. 创建 MagicaCloth 并 BuildAndRun。
```

Unity MC2 adapter 在 step 时执行：

```text
1. 读取 pose_parent_local_matrix_b 或 pose_world_matrix_b。
2. 转换到 Unity solver 空间。
3. 写入 mirror Transform hierarchy，作为动画输入。
4. 等 MC2 更新后读取 solver Transform。
5. 转回 Blender 空间作为 step_output。
```

第一版可以先返回当前 solver Transform 的转换结果，但返回字段必须仍然标明它是 Blender 空间输出。

## Step Output 字段

Unity 返回给 Blender 的主输出使用 Blender 空间：

```text
component_id
armature_name
bone_name
parent_index
output_world_matrix_b
output_world_translation_b
output_world_rotation_b
write_mode
```

兼容字段：

```text
world_matrix
world_translation
world_rotation
world_scale
```

`world_matrix` 等同于 `output_world_matrix_b`。Blender 写回当前仍可用它，但后续应按 `write_mode` 选择更窄的写回策略。

## 写回策略

BoneCloth/BoneSpring 的写回不能长期依赖“直接覆盖 pose bone world matrix”。因为 Blender 骨骼有 rest pose、roll、inherit scale、connected bone 等语义，直接写 world matrix 容易断链。

第一版允许：

```text
write_mode: pose_world_matrix_debug
```

后续正式模式应拆成：

```text
mc2_local_rotation
mc2_world_rotation
tail_position_delta
fallback_world_matrix
```

其中优先级建议是：

```text
rotation only > tail delta > full world matrix
```

## 调试要求

build_output diagnostics 至少返回：

```text
transform_contract
axis_conversion
created_unity_bone_count
created_mc2_component_count
```

step_output diagnostics 至少返回：

```text
input_space
solver_space
output_space
write_mode
```
