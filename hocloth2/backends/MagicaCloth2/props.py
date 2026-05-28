import uuid

import bpy


COMPONENT_TYPE_ITEMS = (
    ("BONE_CLOTH", "BoneCloth", "Magica Cloth 2 BoneCloth"),
    ("BONE_SPRING", "BoneSpring", "Magica Cloth 2 BoneSpring"),
    ("SPHERE_COLLIDER", "Sphere Collider", "Magica Cloth 2 sphere collider"),
    ("CAPSULE_COLLIDER", "Capsule Collider", "Magica Cloth 2 capsule collider"),
    ("PLANE_COLLIDER", "Plane Collider", "Magica Cloth 2 plane collider"),
)

BONE_COMPONENT_TYPES = {"BONE_CLOTH", "BONE_SPRING"}
COLLIDER_COMPONENT_TYPES = {"SPHERE_COLLIDER", "CAPSULE_COLLIDER", "PLANE_COLLIDER"}

CONNECTION_MODE_ITEMS = (
    ("Automatic", "Automatic", "Use MC2 automatic bone connection"),
    ("Line", "Line", "Use line connection"),
    ("Mesh", "Mesh", "Use mesh connection when this backend supports it"),
)


def _poll_armature_object(_self, obj):
    return obj is not None and obj.type == "ARMATURE"


def generate_component_id() -> str:
    return uuid.uuid4().hex


def ensure_component_id(component) -> str:
    if not component.component_id:
        component.component_id = generate_component_id()
    return component.component_id


class HOCLOTH2_MC2_Component(bpy.types.PropertyGroup):
    component_id: bpy.props.StringProperty(name="Component ID")
    display_name: bpy.props.StringProperty(name="Name", default="MagicaCloth2 Component")
    component_type: bpy.props.EnumProperty(
        name="Type",
        items=COMPONENT_TYPE_ITEMS,
        default="BONE_CLOTH",
    )
    enabled: bpy.props.BoolProperty(name="Enabled", default=True)
    ui_expanded: bpy.props.BoolProperty(name="Expanded", default=True)
    armature_object: bpy.props.PointerProperty(
        name="Armature",
        type=bpy.types.Object,
        poll=_poll_armature_object,
    )
    root_bone_name: bpy.props.StringProperty(name="Root Bone")
    bone_count: bpy.props.IntProperty(name="Bones", default=0, min=0)
    connection_mode: bpy.props.EnumProperty(
        name="Connection",
        items=CONNECTION_MODE_ITEMS,
        default="Automatic",
    )
    radius: bpy.props.FloatProperty(name="Radius", default=0.05, min=0.0, soft_max=1.0)
    gravity_strength: bpy.props.FloatProperty(name="Gravity", default=9.81, min=0.0, soft_max=20.0)
    damping: bpy.props.FloatProperty(name="Damping", default=0.10, min=0.0, max=1.0)
    stiffness: bpy.props.FloatProperty(name="Stiffness", default=0.60, min=0.0, soft_max=2.0)
    drag: bpy.props.FloatProperty(name="Drag", default=0.40, min=0.0, max=1.0)
    source_object: bpy.props.PointerProperty(name="Object", type=bpy.types.Object)
    length: bpy.props.FloatProperty(name="Length", default=0.2, min=0.0, soft_max=2.0)
    collider_friction: bpy.props.FloatProperty(name="Friction", default=0.05, min=0.0, max=1.0)
    status: bpy.props.StringProperty(name="Status", default="Not built")


CLASSES = (
    HOCLOTH2_MC2_Component,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)

    bpy.types.Scene.hocloth2_mc2_components = bpy.props.CollectionProperty(type=HOCLOTH2_MC2_Component)
    bpy.types.Scene.hocloth2_mc2_component_index = bpy.props.IntProperty(
        name="MC2 Component Index",
        default=0,
        min=0,
    )
    bpy.types.Scene.hocloth2_mc2_status = bpy.props.StringProperty(name="MC2 Status", default="Idle")
    bpy.types.Scene.hocloth2_mc2_live_running = bpy.props.BoolProperty(name="MC2 Live", default=False)
    bpy.types.Scene.hocloth2_mc2_runtime_handle = bpy.props.IntProperty(name="MC2 Runtime Handle", default=0, min=0)
    bpy.types.Scene.hocloth2_mc2_step_index = bpy.props.IntProperty(name="MC2 Step Index", default=0, min=0)
    bpy.types.Scene.hocloth2_mc2_last_time_seconds = bpy.props.FloatProperty(name="MC2 Last Time Seconds", default=0.0)
    bpy.types.Scene.hocloth2_mc2_has_last_time_seconds = bpy.props.BoolProperty(name="MC2 Has Last Time Seconds", default=False)
    bpy.types.Scene.hocloth2_mc2_unity_tick_rate = bpy.props.IntProperty(
        name="Unity Ticks / Sec",
        default=120,
        min=1,
        max=240,
    )
    bpy.types.Scene.hocloth2_mc2_simulation_frequency = bpy.props.IntProperty(
        name="MC2 Steps / Sec",
        default=120,
        min=30,
        max=150,
    )
    bpy.types.Scene.hocloth2_mc2_last_snapshot_path = bpy.props.StringProperty(
        name="Last Snapshot Path",
        default="",
    )
    bpy.types.Scene.hocloth2_mc2_last_debug_json_path = bpy.props.StringProperty(
        name="Last Debug JSON Path",
        default="",
    )


def unregister() -> None:
    for attr_name in (
        "hocloth2_mc2_last_debug_json_path",
        "hocloth2_mc2_last_snapshot_path",
        "hocloth2_mc2_simulation_substeps",
        "hocloth2_mc2_simulation_frequency",
        "hocloth2_mc2_unity_tick_rate",
        "hocloth2_mc2_has_last_time_seconds",
        "hocloth2_mc2_last_time_seconds",
        "hocloth2_mc2_step_index",
        "hocloth2_mc2_runtime_handle",
        "hocloth2_mc2_live_running",
        "hocloth2_mc2_status",
        "hocloth2_mc2_component_index",
        "hocloth2_mc2_components",
    ):
        if hasattr(bpy.types.Scene, attr_name):
            delattr(bpy.types.Scene, attr_name)

    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


def create_component(scene, component_type: str, display_name: str) -> HOCLOTH2_MC2_Component:
    component = scene.hocloth2_mc2_components.add()
    component.component_id = generate_component_id()
    component.name = display_name
    component.display_name = display_name
    component.component_type = component_type
    scene.hocloth2_mc2_component_index = len(scene.hocloth2_mc2_components) - 1
    return component


def get_active_component(scene):
    components = scene.hocloth2_mc2_components
    if not components:
        return None
    index = max(0, min(scene.hocloth2_mc2_component_index, len(components) - 1))
    scene.hocloth2_mc2_component_index = index
    return components[index]
