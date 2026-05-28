# Alembic Bake Plan

Alembic 是后续 bake/export 功能，不进入第一版实时闭环。

## 原则

Bake 也归 backend 自己维护。

MC2 的 Alembic bake 放在：

```text
hocloth2/backends/MagicaCloth2/bake.py
```

未来 VRM SpringBone、DynamicBone、PhysBone 如果也需要 bake，各自放在自己的 backend 目录。

## MC2 未来流程

```text
1. Blender 指定 frame range 和目标 mesh。
2. MagicaCloth2 backend 发送 bake 请求给 Unity host。
3. Unity 使用 MC2 解算骨骼。
4. Unity 烘焙 skinned mesh 到 Alembic。
5. Blender 把 Alembic 作为 cache/modifier 挂回对象。
```

## 为什么后置

Alembic 需要 mesh topology、bind pose、skin weights、输出路径、帧范围等额外数据。第一版先验证 MC2 骨骼解算和写回。

