# HoCloth2

HoCloth2 是一个 Blender 插件目录，用来和外部 Unity 物理宿主交互。

第一版先做 MC2。以后如果要支持 VRM SpringBone、DynamicBone、PhysBone，就各自作为一个独立 backend 加进来。不要先设计一个抽象通用 component，再逼每个 backend 适配它。

## 基本原则

- HoCloth2 当前目录本身就是 Blender 可读取的裸插件目录。
- 每个 backend 自己维护完整实现：属性、UI、导出、运行时、写回、collider、bake。
- `common/` 只放真正会被多个 backend 复用的小工具。
- Unity host 是一个外部程序，插件通过 bridge 调用它。
- GitHub 自动发布先搁置，等第一版原型跑通后再做。

## 当前目录

```text
HoCloth2/
  __init__.py
  README.md
  hocloth2/
    common/
    backends/
      MagicaCloth2/
      VRM/
      DynamicBone/
      Physbones/
  bundled/
    unity_host/
      windows-x64/
  docs/
  tools/
  tests/
```

## 第一阶段

第一阶段只做：

```text
Blender MagicaCloth2 backend
  -> export MC2 authoring snapshot
  -> Unity host MC2 adapter build
  -> send frame inputs
  -> receive solved bone transforms
  -> Blender pose apply
```

MeshCloth、Alembic、VRM SpringBone、DynamicBone、PhysBone 都后置。

## 发布形态

开发期：Blender 直接读取当前 `HoCloth2` 目录。

发布期：打包成 zip：

```text
HoCloth2-<version>.zip
  HoCloth2/
    __init__.py
    hocloth2/
    bundled/unity_host/windows-x64/
```

Unity 后端由 `D:\Unity_Project\HoClothUnity` build 后复制到 `bundled/unity_host/windows-x64`。

