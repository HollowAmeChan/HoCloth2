# 时间契约

HoCloth2 的传输时间单位是现实秒。Blender 的帧率不是模拟采样率，也不能假设 bake 一定按固定帧率稳定推进。Blender 只需要说明当前时间轴如何解释帧号：一秒对应多少 Blender timeline frame、当前是第几帧、这一帧对应多少秒。

## 核心原则

`frame_inputs.time_seconds` 是每次传输的主时间坐标。`frame` / `frame_index` 是 Blender 时间轴上的帧号标签。`blender_timeline_fps` 只用于解释这个帧号标签，例如：

```text
time_seconds = (timeline_frame - frame_origin) / blender_timeline_fps
```

如果 bake、预览或后续调度出现非连续帧、跳帧、倒放、子帧，发送端仍然应该显式发送 `time_seconds`。接收端不应该只靠固定 FPS 自己推断当前时间。

## 分层

Blender 时间轴解释：
```text
blender_timeline_fps = scene.render.fps / scene.render.fps_base
blender_frame_duration_seconds = 1.0 / blender_timeline_fps
frame_index = scene.frame_current
timeline_frame = frame_index + scene.frame_subframe
time_seconds = (timeline_frame - frame_origin) / blender_timeline_fps
```

Unity 主机运行：
```text
unity_tick_rate = 用户设置的 Unity 每秒 PlayerLoop tick 数
unity_tick_delta_time = 1.0 / unity_tick_rate
Application.targetFrameRate = unity_tick_rate
Time.captureDeltaTime = unity_tick_delta_time
```

MC2 内部解算：
```text
mc2_simulation_frequency = 用户设置的 MC2 每秒模拟步数，范围 30..150
mc2_fixed_delta_time = 1.0 / mc2_simulation_frequency
mc2_max_simulation_count_per_frame = ceil(mc2_simulation_frequency / unity_tick_rate)，范围 1..5
```

Unity tick rate 和 MC2 simulation frequency 是后端运行设置，不由 Blender 帧率反推。提高 Unity tick rate 可以让骨骼/碰撞体输入在 Unity 侧更密；提高 MC2 simulation frequency 可以让 MC2 内部每步更短。

## time_contract 字段

`authoring_snapshot.payload.time_contract` 和 `step_request.payload.frame_inputs.time_contract` 使用同一结构：

```text
contract: mc2_time_v3
time_unit: seconds
time_basis: real_time_seconds
time_source: frame_inputs.time_seconds
timeline_source: blender_scene
blender_fps: int
blender_fps_base: float
blender_timeline_fps: float
blender_frame_duration_seconds: float
unity_tick_rate: int
unity_tick_delta_time: float
unity_time_mode: capture_delta_time
unity_capture_delta_time: float
unity_target_frame_rate: int
mc2_simulation_frequency: int
mc2_fixed_delta_time: float
mc2_max_simulation_count_per_frame: int
unity_ticks_per_timeline_frame: float
mc2_steps_per_timeline_frame: float
mc2_steps_per_unity_tick: float
```

`blender_sample_rate`、`blender_frame_delta_time`、`display_fps`、`display_frame_delta_time`、`unity_ticks_per_blender_frame`、`mc2_steps_per_blender_frame`、`effective_substeps_per_frame` 暂时保留为兼容字段，新代码优先读取 timeline 命名字段。

## frame_inputs 时间字段

每次 step request 必须发送：

```text
frame: int                    # 兼容字段，等同 frame_index
frame_index: int              # Blender 当前帧号标签
frame_subframe: float         # Blender 子帧
timeline_frame: float         # frame_index + frame_subframe
frame_origin: int             # 当前时间段的 0 秒原点，默认 scene.frame_start
time_seconds: float           # 主时间坐标，单位秒
delta_time_seconds: float     # 与上一次发送的 time_seconds 差值；不连续时可为 0
time_discontinuity: bool      # 第一帧、倒放、跳转等不连续时间标记
```

`time` 和 `delta_time` 暂时保留为兼容别名，但语义等同 `time_seconds` 和 `delta_time_seconds`。

## 当前边界

当前 MC2 仍由 Unity PlayerLoop 驱动。契约已经把“传输时间坐标”和“后端运行频率”拆开；后续要做更完整的 bake 调度时，Unity host 应按 `time_seconds` 消费输入、按自身 tick rate 推进，并在目标时间点回传采样。