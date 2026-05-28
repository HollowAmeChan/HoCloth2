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


def _poll_armature_object(_self, obj):
    return obj is not None and obj.type == "ARMATURE"


def generate_component_id() -> str:
    return uuid.uuid4().hex


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
    source_object: bpy.props.PointerProperty(name="Object", type=bpy.types.Object)
    radius: bpy.props.FloatProperty(name="Radius", default=0.05, min=0.0, soft_max=1.0)
    length: bpy.props.FloatProperty(name="Length", default=0.2, min=0.0, soft_max=2.0)
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


def unregister() -> None:
    for attr_name in (
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
