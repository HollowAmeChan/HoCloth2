import json
from pathlib import Path

import bpy
from mathutils import Matrix

from ...common import host
from ...common.exchange import make_envelope, write_messagepack_file
from . import props, snapshot
from .extract import extract_active_bone_chain


_COMPONENT_LABELS = {
    "BONE_CLOTH": "MagicaCloth2 BoneCloth",
    "BONE_SPRING": "MagicaCloth2 BoneSpring",
    "SPHERE_COLLIDER": "MagicaCloth2 Sphere Collider",
    "CAPSULE_COLLIDER": "MagicaCloth2 Capsule Collider",
    "PLANE_COLLIDER": "MagicaCloth2 Plane Collider",
}

SNAPSHOT_FILE_NAME = "HoCloth2_MC2_AuthoringSnapshot.msgpack"
DEBUG_JSON_FILE_NAME = "HoCloth2_MC2_AuthoringSnapshot.debug.json"
BUILD_REQUEST_FILE_NAME = "HoCloth2_MC2_BuildRequest.msgpack"
BUILD_REQUEST_DEBUG_JSON_FILE_NAME = "HoCloth2_MC2_BuildRequest.debug.json"


def _active_component(scene):
    return props.get_active_component(scene)


def _snapshot_dir() -> Path:
    blend_path = Path(bpy.data.filepath) if bpy.data.filepath else None
    if blend_path is not None and blend_path.parent.exists():
        path = blend_path.parent / ".hocloth2"
    else:
        path = Path(bpy.app.tempdir) / "HoCloth2"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_debug_pair(scene, message: dict, msgpack_name: str, debug_json_name: str) -> tuple[Path, Path]:
    path = _snapshot_dir()
    msgpack_path = path / msgpack_name
    debug_json_path = path / debug_json_name
    write_messagepack_file(msgpack_path, message)
    debug_json_path.write_text(json.dumps(message, ensure_ascii=False, indent=2), encoding="utf-8")
    scene.hocloth2_mc2_last_snapshot_path = str(msgpack_path)
    scene.hocloth2_mc2_last_debug_json_path = str(debug_json_path)
    return msgpack_path, debug_json_path


def _write_snapshot_files(scene, envelope: dict) -> tuple[Path, Path]:
    return _write_debug_pair(scene, envelope, SNAPSHOT_FILE_NAME, DEBUG_JSON_FILE_NAME)


def _build_request_from_snapshot(authoring_snapshot: dict) -> dict:
    return make_envelope(
        "MagicaCloth2",
        "build_request",
        {
            "authoring_snapshot": authoring_snapshot,
        },
    )


def _write_build_request_files(scene, authoring_snapshot: dict) -> tuple[Path, Path]:
    return _write_debug_pair(
        scene,
        _build_request_from_snapshot(authoring_snapshot),
        BUILD_REQUEST_FILE_NAME,
        BUILD_REQUEST_DEBUG_JSON_FILE_NAME,
    )


def _as_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _vec3(value) -> tuple[float, float, float]:
    return (float(value[0]), float(value[1]), float(value[2]))


def _quat(value) -> tuple[float, float, float, float]:
    return (float(value.w), float(value.x), float(value.y), float(value.z))


def _matrix(value) -> tuple[float, ...]:
    return tuple(float(value[row][column]) for row in range(4) for column in range(4))


def _matrix_from_row_major(values) -> Matrix | None:
    if not isinstance(values, (list, tuple)) or len(values) != 16:
        return None
    try:
        numbers = [float(value) for value in values]
    except (TypeError, ValueError):
        return None
    return Matrix(
        (
            numbers[0:4],
            numbers[4:8],
            numbers[8:12],
            numbers[12:16],
        )
    )


def _scene_delta_time(scene) -> float:
    fps_base = float(scene.render.fps_base) if scene.render.fps_base else 1.0
    fps = float(scene.render.fps) / fps_base if scene.render.fps else 24.0
    return 1.0 / fps if fps > 0.0 else 1.0 / 24.0


def _store_build_response(scene, response: dict) -> tuple[int, str]:
    payload = response.get("payload", {}) if isinstance(response, dict) else {}
    handle = _as_int(payload.get("handle"), 0)
    summary = str(payload.get("summary", ""))
    if handle > 0:
        scene.hocloth2_mc2_runtime_handle = handle
        scene.hocloth2_mc2_step_index = 0
    return handle, summary


def _frame_inputs_from_snapshot(scene, authoring_snapshot: dict) -> dict:
    snapshot_payload = authoring_snapshot.get("payload", {})
    transforms: list[dict] = []
    for chain in snapshot_payload.get("bone_chains", []):
        armature_name = chain.get("armature_name", "")
        armature_object = bpy.data.objects.get(armature_name)
        if armature_object is None or armature_object.type != "ARMATURE" or armature_object.pose is None:
            continue
        component_id = chain.get("component_id", "")
        for bone_data in chain.get("bones", []):
            bone_name = bone_data.get("name", "")
            pose_bone = armature_object.pose.bones.get(bone_name)
            if pose_bone is None:
                continue
            world_matrix = armature_object.matrix_world @ pose_bone.matrix
            parent_name = bone_data.get("parent_name", "")
            parent_pose_bone = armature_object.pose.bones.get(parent_name) if parent_name else None
            if parent_pose_bone is not None:
                parent_world_matrix = armature_object.matrix_world @ parent_pose_bone.matrix
                parent_local_matrix = parent_world_matrix.inverted_safe() @ world_matrix
            else:
                parent_local_matrix = armature_object.matrix_world.inverted_safe() @ world_matrix
            transforms.append(
                {
                    "component_id": component_id,
                    "armature_name": armature_name,
                    "bone_name": bone_name,
                    "pose_world_matrix_b": _matrix(world_matrix),
                    "pose_parent_local_matrix_b": _matrix(parent_local_matrix),
                    "pose_world_translation_b": _vec3(world_matrix.to_translation()),
                    "pose_world_rotation_b": _quat(world_matrix.to_quaternion()),
                    "pose_world_scale_b": _vec3(world_matrix.to_scale()),
                    "world_matrix": _matrix(world_matrix),
                    "world_translation": _vec3(world_matrix.to_translation()),
                    "world_rotation": _quat(world_matrix.to_quaternion()),
                    "world_scale": _vec3(world_matrix.to_scale()),
                }
            )

    delta_time = _scene_delta_time(scene)
    return {
        "frame": int(scene.frame_current),
        "time": float(scene.frame_current) * delta_time,
        "delta_time": delta_time,
        "bone_transforms": transforms,
    }


def _step_request_from_snapshot(scene, authoring_snapshot: dict) -> dict:
    return make_envelope(
        "MagicaCloth2",
        "step_request",
        {
            "handle": int(scene.hocloth2_mc2_runtime_handle),
            "frame_inputs": _frame_inputs_from_snapshot(scene, authoring_snapshot),
        },
    )


def _apply_step_output(scene, response: dict) -> int:
    payload = response.get("payload", {}) if isinstance(response, dict) else {}
    applied = 0
    for transform in payload.get("bone_transforms", []):
        armature_name = transform.get("armature_name", "")
        bone_name = transform.get("bone_name", "")
        armature_object = bpy.data.objects.get(armature_name)
        if armature_object is None or armature_object.type != "ARMATURE" or armature_object.pose is None:
            continue
        pose_bone = armature_object.pose.bones.get(bone_name)
        if pose_bone is None:
            continue
        world_matrix = _matrix_from_row_major(transform.get("output_world_matrix_b") or transform.get("world_matrix"))
        if world_matrix is None:
            continue
        pose_bone.matrix = armature_object.matrix_world.inverted_safe() @ world_matrix
        applied += 1

    if applied:
        bpy.context.view_layer.update()
    return applied


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
            scene.hocloth2_mc2_runtime_handle = 0
            scene.hocloth2_mc2_step_index = 0
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
        scene.hocloth2_mc2_runtime_handle = 0
        scene.hocloth2_mc2_step_index = 0
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
        scene.hocloth2_mc2_runtime_handle = 0
        scene.hocloth2_mc2_step_index = 0
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
        scene.hocloth2_mc2_runtime_handle = 0
        scene.hocloth2_mc2_step_index = 0
        scene.hocloth2_mc2_status = component.status
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_export_snapshot(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_export_snapshot"
    bl_label = "Export MC2 Snapshot"
    bl_description = "Write the current Magica Cloth 2 authoring snapshot as MessagePack plus debug JSON"

    def execute(self, context):
        envelope = snapshot.build_authoring_snapshot(context.scene)
        payload = envelope.get("payload", {})
        msgpack_path, _debug_json_path = _write_snapshot_files(context.scene, envelope)
        context.scene.hocloth2_mc2_status = (
            f"Snapshot exported: {len(payload.get('bone_chains', []))} chains, "
            f"{len(payload.get('colliders', []))} colliders"
        )
        self.report({"INFO"}, f"Wrote {msgpack_path}")
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
        request_path, _debug_json_path = _write_build_request_files(scene, envelope)

        if not bone_chains:
            scene.hocloth2_mc2_status = "Build blocked: no enabled BoneCloth/BoneSpring component"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}
        if bone_count <= 0:
            scene.hocloth2_mc2_status = "Build blocked: enabled MC2 chains resolved 0 bones"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        request_message = _build_request_from_snapshot(envelope)
        if host.can_connect():
            try:
                response = host.request(request_message)
            except Exception as exc:
                scene.hocloth2_mc2_status = f"Build send failed: {exc}"
                self.report({"ERROR"}, scene.hocloth2_mc2_status)
                return {"CANCELLED"}
            if response.get("payload_type") != "build_output" or not response.get("payload", {}).get("ok", False):
                scene.hocloth2_mc2_status = f"Build failed: {response.get('payload_type', 'unknown')}"
                self.report({"ERROR"}, scene.hocloth2_mc2_status)
                return {"CANCELLED"}
            handle, summary = _store_build_response(scene, response)
            scene.hocloth2_mc2_status = f"Build #{handle}: {summary or response.get('payload_type', 'ok')}"
            return {"FINISHED"}

        scene.hocloth2_mc2_runtime_handle = 0
        scene.hocloth2_mc2_status = (
            "Build request ready: "
            f"{len(bone_chains)} chains, {collider_count} colliders, {bone_count} bones"
        )
        self.report({"INFO"}, f"Wrote {request_path}; Unity bridge is not running yet.")
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_step(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_step"
    bl_label = "Step MC2 Runtime"
    bl_description = "Step the Magica Cloth 2 runtime once"

    def execute(self, context):
        scene = context.scene
        if not host.can_connect():
            scene.hocloth2_mc2_status = "Step blocked: Unity engine is not running"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}
        if scene.hocloth2_mc2_runtime_handle <= 0:
            scene.hocloth2_mc2_status = "Step blocked: build runtime first"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        authoring_snapshot = snapshot.build_authoring_snapshot(scene)
        request_message = _step_request_from_snapshot(scene, authoring_snapshot)
        bone_count = len(request_message["payload"]["frame_inputs"].get("bone_transforms", []))
        if bone_count <= 0:
            scene.hocloth2_mc2_status = "Step blocked: no bone transforms to send"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        try:
            response = host.request(request_message)
        except Exception as exc:
            scene.hocloth2_mc2_status = f"Step send failed: {exc}"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        payload = response.get("payload", {})
        if response.get("payload_type") != "step_output" or not payload.get("ok", False):
            scene.hocloth2_mc2_status = f"Step failed: {payload.get('message', response.get('payload_type', 'unknown'))}"
            self.report({"ERROR"}, scene.hocloth2_mc2_status)
            return {"CANCELLED"}

        applied = _apply_step_output(scene, response)
        scene.hocloth2_mc2_step_index = _as_int(payload.get("step_index"), scene.hocloth2_mc2_step_index + 1)
        scene.hocloth2_mc2_status = (
            f"Step #{scene.hocloth2_mc2_step_index}: sent {bone_count} bones, "
            f"applied {applied} transforms"
        )
        return {"FINISHED"}


class HOCLOTH2_MC2_OT_toggle_live(bpy.types.Operator):
    bl_idname = "hocloth2.mc2_toggle_live"
    bl_label = "Toggle MC2 Live"
    bl_description = "Start or stop live stepping for the Magica Cloth 2 runtime"

    def execute(self, context):
        scene = context.scene
        scene.hocloth2_mc2_live_running = not scene.hocloth2_mc2_live_running
        scene.hocloth2_mc2_status = (
            "Live placeholder: manual Step is wired"
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