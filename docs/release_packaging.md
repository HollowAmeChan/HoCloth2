# 发布与打包流程

HoCloth2 当前目录本身就是 Blender 可读取的裸插件目录。

## 开发期

Blender 直接读取：

```text
C:\Users\hhh12\AppData\Roaming\Blender Foundation\Blender\4.5\scripts\addons\HoCloth2
```

Unity 工程在：

```text
D:\Unity_Project\HoClothUnity
```

## Unity build 同步

Unity 打包后，复制到：

```text
HoCloth2\engine
```

未来脚本：

```text
tools/sync_engine.ps1
```

职责：

- 检查 Unity build 输出。
- 清空 `engine/` 目标目录。
- 复制 exe、Data 目录、UnityPlayer.dll、依赖 dll、version.json。
- 不复制 Unity 工程源码。
- 不复制 PDB/MDB、DoNotShip、D3D12 等调试或冗余发布内容。

## Blender 插件 zip

未来脚本：

```text
tools/package_addon.ps1
```

输出：

```text
_dist/HoCloth2-<version>.zip
```

zip 内部：

```text
HoCloth2/
  __init__.py
  _Lib/
  engine/
  hocloth2/
```

## GitHub Release

先搁置。等第一版原型跑通后，再做：

```text
tag v* -> build/package -> upload HoCloth2-<version>.zip
```

Unity/MC2 授权和 CI 环境可能麻烦，后面再决定是否用自托管 runner。
