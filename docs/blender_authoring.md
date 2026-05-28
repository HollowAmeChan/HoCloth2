# Blender Authoring

HoCloth2 不做统一 authoring 模型。每个 backend 自己维护自己的 Blender authoring。

## MC2

MC2 authoring 放在：

```text
hocloth2/backends/MagicaCloth2/
```

MC2 自己决定：

- PropertyGroup 怎么存。
- UI 怎么画。
- Bone attributes 怎么读。
- Collider 怎么绑定。
- Snapshot 怎么导出。
- Pose 怎么写回。

## 未来后端

未来新增后端时，也各自完整维护：

```text
hocloth2/backends/VRM/
hocloth2/backends/DynamicBone/
hocloth2/backends/Physbones/
```

它们可以复用 `common` 的小工具，但不复用 MC2 的参数模型。

## Build 前规则

每个 backend 在 build 前都要保证：

```text
1. UI 修改已经写回 Blender datablock。
2. 从 Blender 当前状态采样 authoring。
3. 导出自己的 snapshot payload。
4. 发给 Unity host。
5. Unity build 成功后才能进入 step/live。
```

这个流程可以统一，payload 不统一。

