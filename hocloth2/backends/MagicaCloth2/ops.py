import json

import bpy

from . import props, snapshot
from .extract import extract_active_bone_chain


_COMPONENT_LABELS = {
    "BONE_CLOTH": "MagicaCloth2 BoneCloth",
    "BONE_SPRING": "MagicaCloth2 BoneSpring",
    "SPHERE_COLLIDER": "MagicaCloth2 Sphere Collider",
    "CAPSULE_COLLIDER": "MagicaCloth2 Capsule Collider",
    "PLANE_COLLIDER": "MagicaCloth2 Plane Collider",
}

SNAPSHOT_TEXT_NAME = "HoCloth2_MC2_AuthoringSnapshot.json"


def _active_component(scene):
    return props.get_active_component(scene)


def _write_snapshot_text(scene, envelope: dict) -> str:
    text = bpy.data.texts.get(SNAPSHOT_TEXT_NAME)
    if text is None:
        text = bpy.data.texts.new(SNAPSHOT_TEXT_NAME)
    text.clear()
    text.write(json.dumps(envelope, ensure_ascii=False, indent=2))
    scene.hocloth2_mc2_last_snapshot_text_name = text.name
    return text.name


class HOCLOTH2_MC2_OT_add_component(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_add_component"
    bl_label = "Add MC2 Component"
    bl_description = "Create a Magica Cloth 2 authoring component from the current Blender selection"

    component_type: bpy.props.EnumProperty(
        name="Type",
        items=props.COMPONENT_TYPE_ITEMS,
        default="BONE_CLOTH",
    )

    def execute(self, context):
        scene = context.scene
        component_type = self.component_type
        label = _COMPONENT_LABELS.get(component_type, "MagicaCloth2 Component")

        if component_type in props.BONE_COMPONENT_TYPES:
            try:
                extracted = extract_active_bone_chain(context)
            except RuntimeError as exc:
                self.report({"ERROR"}, str(exc))
                return {"CANCELLED"}

            display_name = f"{label}: {extracted.root_bone_name}"
            component = props.create_component(scene, component_type, display_name)
            component.armature_object = context.object
            component.root_bone_name = extracted.root_bone_name
            component.bone_count = len(extracted.bone_names)
            component.status = f"Authoring chain ready: {component.bone_count} bones"
            scene.hocloth2_mc2_status = f"Added {display_name}"
            return {"FINISHED"}

        active_object = context.object
        if active_object is None:
            self.report({"ERROR"}, "Select an object to bind as a collider.")
            return {"CANCELLED"}

        display_name = f"{label}: {active_object.name}"
        component = props.create_component(scene, component_type, display_name)
        component.source_object = active_object
        component.status = "Collider authoring ready"
        scene.hocloth2_mc2_status = f"Added {display_name}"
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_remove_component(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_remove_component"
    bl_label = "Remove MC2 Component"
    bl_description = "Remove the active Magica Cloth 2 authoring component"

    def execute(self, context):
        scene = context.scene
        components = scene.hocloth2_mc2_components
        if not components:
            return {"CANCELLED"}

        index = max(0, min(scene.hocloth2_mc2_component_index, len(components) - 1))
        removed_name = components[index].display_name or components[index].name
        components.remove(index)
        scene.hocloth2_mc2_component_index = max(0, min(index, len(components) - 1))
        scene.hocloth2_mc2_status = f"Removed {removed_name}"
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_refresh_component(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_refresh_component"
    bl_label = "Refresh MC2 Component"
    bl_description = "Refresh the active component from the current armature selection"

    def execute(self, context):
        scene = context.scene
        component = _active_component(scene)
        if component is None:
            return {"CANCELLED"}
        if component.component_type not in props.BONE_COMPONENT_TYPES:
            component.status = "Collider does not need a bone-chain refresh"
            scene.hocloth2_mc2_status = component.status
            return {"FINISHED"}

        try:
            extracted = extract_active_bone_chain(context)
        except RuntimeError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}

        component.armature_object = context.object
        component.root_bone_name = extracted.root_bone_name
        component.bone_count = len(extracted.bone_names)
        component.status = f"Refreshed chain: {component.bone_count} bones"
        scene.hocloth2_mc2_status = component.status
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_export_snapshot(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_export_snapshot"
    bl_label = "Export MC2 Snapshot"
    bl_description = "Write the current Magica Cloth 2 authoring snapshot to a Blender text datablock"

    def execute(self, context):
        envelope = snapshot.build_authoring_snapshot(context.scene)
        payload = envelope.get("payload", {})
        text_name = _write_snapshot_text(context.scene, envelope)
        context.scene.hocloth2_mc2_status = (
            f"Snapshot exported: {len(payload.get('bone_chains', []))} chains, "
            f"{len(payload.get('colliders', []))} colliders"
        )
        self.report({"INFO"}, f"Wrote {text_name}")
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_build(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_build"
    bl_label = "Build MC2 Runtime"
    bl_description = "Build a Magica Cloth 2 runtime scene in the Unity host"

    def execute(self, context):
        scene = context.scene
        envelope = snapshot.build_authoring_snapshot(scene)
        payload = envelope.get("payload", {})
        bone_chains = payload.get("bone_chains", [])
        collider_count = len(payload.get("colliders", []))
        bone_count = sum(len(chain.get("bones", [])) for chain in bone_chains)
        _write_snapshot_text(scene, envelope)

        if not bone_chains:
            scene.hocloth2_mc2_status = "Build blocked: no enabled BoneCloth/BoneSpring component"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}
        if bone_count <= 0:
            scene.hocloth2_mc2_status = "Build blocked: enabled MC2 chains resolved 0 bones"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        scene.hocloth2_mc2_status = (
            "Build placeholder snapshot ready: "
            f"{len(bone_chains)} chains, {collider_count} colliders, {bone_count} bones"
        )
        self.report({"INFO"}, "MC2 Unity bridge is not implemented yet.")
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_step(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_step"
    bl_label = "Step MC2 Runtime"
    bl_description = "Step the Magica Cloth 2 runtime once"

    def execute(self, context):
        context.scene.hocloth2_mc2_status = "Step placeholder: Unity bridge is not implemented yet"
        self.report({"INFO"}, context.scene.hocloth2_mc2_status)
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_toggle_live(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_toggle_live"
    bl_label = "Toggle MC2 Live"
    bl_description = "Start or stop live stepping for the Magica Cloth 2 runtime"

    def execute(self, context):
        scene = context.scene
        scene.hocloth2_mc2_live_running = not scene.hocloth2_mc2_live_running
        scene.hocloth2_mc2_status = (
            "Live placeholder: waiting for Unity bridge"
            if scene.hocloth2_mc2_live_running
            else "Live stopped"
        )
        return {"FINISHED"}


CLASSES = (
    HOCLOTH2_MC2_OT_add_component,
    HOCLOTH2_MC2_OT_remove_component,
    HOCLOTH2_MC2_OT_refresh_component,
    HOCLOTH2_MC2_OT_export_snapshot,
    HOCLOTH2_MC2_OT_build,
    HOCLOTH2_MC2_OT_step,
    HOCLOTH2_MC2_OT_toggle_live,
)


def register() -> None:
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister() -> None:
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
