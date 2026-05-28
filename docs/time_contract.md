# 时间契约

HoCloth2 的 MC2 后端使用固定模拟步长。Blender 负责声明项目显示时间，Unity 负责把这个声明映射到 MC2 的固定频率和 Unity 的游戏时间推进。

## MC2 时间模型

MagicaCloth2 不直接使用每帧可变步长做一次模拟。它的 `TimeManager` 使用：

```text
SimulationDeltaTime = 1.0 / simulationFrequency
MaxDeltaTime = SimulationDeltaTime * maxSimulationCountPerFrame
```

每个 Unity PlayerLoop 中，MC2 根据 Unity `Time.deltaTime` 累积时间，计算本帧应执行的固定步数，并限制在 `maxSimulationCountPerFrame` 内。MC2 公开 API：

```text
MagicaManager.SetSimulationFrequency(30..150)
MagicaManager.SetMaxSimulationCountPerFrame(1..5)
MagicaManager.SetUpdateLocation(AfterLateUpdate | BeforeLateUpdate)
```

## Blender 显示时间

Blender 每秒显示帧率来自项目设置：

```text
display_fps = scene.render.fps / scene.render.fps_base
display_frame_delta_time = 1.0 / display_fps
```

这个显示帧率必须在 UI 中显式展示。用户看到的“每帧”就是这个 Blender display frame，不是 Unity 实时渲染帧。

## MC2 第一版映射

Blender 侧提供 `MC2 Substeps / Frame`，默认 4。契约解析为：

```text
requested_simulation_frequency = display_fps * requested_substeps_per_frame
mc2_simulation_frequency = clamp(round(requested_simulation_frequency), 30, 150)
mc2_fixed_delta_time = 1.0 / mc2_simulation_frequency
effective_substeps_per_frame = mc2_simulation_frequency / display_fps
mc2_max_simulation_count_per_frame = clamp(ceil(effective_substeps_per_frame), 1, 5)
```

Unity 侧应用：

```text
QualitySettings.vSyncCount = 0
Application.targetFrameRate = round(display_fps)
Time.captureDeltaTime = display_frame_delta_time
Time.fixedDeltaTime = mc2_fixed_delta_time
Time.maximumDeltaTime = max(display_frame_delta_time, mc2_fixed_delta_time * maxSimulationCountPerFrame)
MagicaManager.SetSimulationFrequency(mc2_simulation_frequency)
MagicaManager.SetMaxSimulationCountPerFrame(mc2_max_simulation_count_per_frame)
MagicaManager.SetUpdateLocation(AfterLateUpdate)
```

`Time.captureDeltaTime` 让 Unity 游戏时间每个 PlayerLoop 固定推进一个 Blender 显示帧。这样连续 step 时，`step_request(N)` 提交第 N 帧输入，`step_request(N+1)` 读取到的是第 N 帧输入经过后续 Unity/MC2 tick 推进后的状态。

## Payload 字段

`authoring_snapshot.payload.time_contract` 和 `step_request.payload.frame_inputs.time_contract` 使用同一结构：

```text
contract: mc2_time_v1
time_source: blender_scene_fps
blender_fps: int
blender_fps_base: float
display_fps: float
display_frame_delta_time: float
requested_substeps_per_frame: int
requested_simulation_frequency: float
mc2_simulation_frequency: int
mc2_fixed_delta_time: float
mc2_max_simulation_count_per_frame: int
effective_substeps_per_frame: float
unity_time_mode: capture_delta_time
unity_capture_delta_time: float
unity_target_frame_rate: int
```

Unity 的 `build_output` 和 `step_output` 会回传解析后的 `time_contract`，用于确认实际生效值。

## 当前边界

第一版是稳定步长的实时预览契约，不是严格离线确定性 bake。MC2 仍由 Unity PlayerLoop 驱动，时间推进来自 Unity game time。后续如果要做完全离线确定性，需要进一步研究是否能绕过 MC2 PlayerLoop 或建立独立的手动 tick 驱动。