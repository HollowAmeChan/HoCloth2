from mathutils import Vector

from ...common.exchange import wrap_authoring_snapshot
from . import props


BACKEND_ID = "MagicaCloth2"
TRANSFORM_CONTRACT = "bone_transform_v1"
AXIS_CONVERSION = "BLENDER_Z_UP_NEG_Y_FORWARD_TO_UNITY_Y_UP_POS_Z_FORWARD"
MATRIX_CONVENTION = "row_major_column_vector"
BONE_PRIMARY_AXIS = "blender_local_positive_y"
MC2_BONE_ATTRIBUTE_PROPERTY_ALIASES = (
    "hocloth_mc2_attribute",
    "mc2_attribute",
)
MC2_BONE_ATTRIBUTE_ENUMS = {
    "DEFAULT",
    "MOVE",
    "FIXED",
    "DISABLE_COLLISION",
    "INVALID",
}
MC2_BONE_ATTRIBUTE_INT_MAP = {
    0: "DEFAULT",
    1: "MOVE",
    2: "FIXED",
    3: "DISABLE_COLLISION",
    4: "INVALID",
}


def _vec3(value) -> tuple[float, float, float]:
    return (float(value[0]), float(value[1]), float(value[2]))


def _quat(value) -> tuple[float, float, float, float]:
    return (float(value.w), float(value.x), float(value.y), float(value.z))


def _matrix(value) -> tuple[float, ...]:
    return tuple(float(value[row][column]) for row in range(4) for column in range(4))


def _curve(value: float, use_curve: bool = False) -> dict:
    sample = float(value)
    return {
        "value": sample,
        "useCurve": bool(use_curve),
        "samples": [sample] * 16,
    }


def _normalize_bone_attribute(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return MC2_BONE_ATTRIBUTE_INT_MAP.get(value)

    token = str(value).strip()
    if not token:
        return None
    token = token.upper().replace("-", "_").replace(" ", "_")
    collapsed = token.replace("_", "")
    alias_map = {
        "DEFAULT": "DEFAULT",
        "MOVE": "MOVE",
        "FIXED": "FIXED",
        "DISABLECOLLISION": "DISABLE_COLLISION",
        "INVALID": "INVALID",
    }
    normalized = alias_map.get(collapsed, token)
    return normalized if normalized in MC2_BONE_ATTRIBUTE_ENUMS else None


def _read_bone_attribute_property(pose_bone, bone) -> str | None:
    for owner in (pose_bone, bone):
        if owner is None or not hasattr(owner, "get"):
            continue
        for key in MC2_BONE_ATTRIBUTE_PROPERTY_ALIASES:
            value = owner.get(key)
            normalized = _normalize_bone_attribute(value)
            if normalized is not None:
                return normalized
    return None


def _collect_bone_subtree_names(armature_object, root_bone_name: str) -> list[str]:
    if armature_object is None or armature_object.type != "ARMATURE" or not root_bone_name:
        return []
    root_bone = armature_object.data.bones.get(root_bone_name)
    if root_bone is None:
        return []

    names: list[str] = []
    stack = [root_bone]
    while stack:
        current = stack.pop()
        names.append(current.name)
        children = sorted(current.children, key=lambda child: child.name)
        stack.extend(reversed(children))
    return names


def _bone_parent_local_matrix(armature_object, bone, world_matrix):
    if bone.parent is not None:
        parent_pose_bone = armature_object.pose.bones.get(bone.parent.name) if armature_object.pose else None
        parent_pose_matrix = parent_pose_bone.matrix.copy() if parent_pose_bone is not None else bone.parent.matrix_local.copy()
        return (armature_object.matrix_world @ parent_pose_matrix).inverted_safe() @ world_matrix
    return armature_object.matrix_world.inverted_safe() @ world_matrix


def _sample_chain_bones(component) -> list[dict]:
    armature_object = component.armature_object
    bone_names = _collect_bone_subtree_names(armature_object, component.root_bone_name)
    if not bone_names:
        return []

    armature_matrix = armature_object.matrix_world.copy()
    name_to_index = {name: index for index, name in enumerate(bone_names)}
    sampled: list[dict] = []
    for bone_name in bone_names:
        bone = armature_object.data.bones.get(bone_name)
        if bone is None:
            continue

        pose_bone = armature_object.pose.bones.get(bone_name) if armature_object.pose else None
        pose_matrix = pose_bone.matrix.copy() if pose_bone is not None else bone.matrix_local.copy()
        world_matrix = armature_matrix @ pose_matrix
        parent_name = bone.parent.name if bone.parent and bone.parent.name in name_to_index else ""
        parent_index = name_to_index[parent_name] if parent_name else -1
        depth = sampled[parent_index]["depth"] + 1 if 0 <= parent_index < len(sampled) else 0
        head_world = world_matrix.to_translation()
        length = max(float(bone.length), 1.0e-6)
        tail_world = head_world + (world_matrix.to_quaternion() @ Vector((0.0, length, 0.0)))
        local_matrix = _bone_parent_local_matrix(armature_object, bone, world_matrix)

        sampled.append(
            {
                "name": bone_name,
                "parent_name": parent_name,
                "parent_index": int(parent_index),
                "depth": int(depth),
                "length": float((tail_world - head_world).length),
                "radius": float(component.radius),
                "stiffness": float(component.stiffness),
                "damping": float(component.damping),
                "drag": float(component.drag),
                "gravity_scale": 1.0,
                "head_local": _vec3(bone.head_local),
                "tail_local": _vec3(bone.tail_local),
                "rest_head_local": _vec3(head_world),
                "rest_tail_local": _vec3(tail_world),
                "rest_parent_local_matrix_b": _matrix(local_matrix),
                "rest_world_matrix_b": _matrix(world_matrix),
                "rest_local_translation": _vec3(local_matrix.to_translation()),
                "rest_local_rotation": _quat(local_matrix.to_quaternion()),
                "rest_world_rotation": _quat(world_matrix.to_quaternion()),
                "rest_world_scale": _vec3(world_matrix.to_scale()),
                "rest_local_to_world_matrix": _matrix(world_matrix),
            }
        )
    return sampled


def _bone_attribute_overrides(component, bones: list[dict]) -> list[dict]:
    armature_object = component.armature_object
    if armature_object is None:
        return []

    overrides = []
    for bone_data in bones:
        bone_name = bone_data.get("name", "")
        bone = armature_object.data.bones.get(bone_name) if armature_object.data else None
        pose_bone = armature_object.pose.bones.get(bone_name) if armature_object.pose else None
        attribute = _read_bone_attribute_property(pose_bone, bone)
        if attribute in {None, "DEFAULT"}:
            continue
        overrides.append({"bone_name": bone_name, "attribute": attribute})
    return overrides


def _bone_chain_snapshot(component):
    armature_object = component.armature_object
    if armature_object is None or armature_object.type != "ARMATURE":
        return None

    component_id = props.ensure_component_id(component)
    bones = _sample_chain_bones(component)
    armature_matrix = armature_object.matrix_world.copy()
    cloth_type = "BoneCloth" if component.component_type == "BONE_CLOTH" else "BoneSpring"
    root_bone_names = [component.root_bone_name] if component.root_bone_name else []
    serialize_data = {
        "clothType": cloth_type,
        "rootBones": root_bone_names,
        "connectionMode": component.connection_mode,
        "gravity": float(component.gravity_strength),
        "gravityDirection": (0.0, 0.0, -1.0),
        "damping": _curve(component.damping),
        "radius": _curve(component.radius),
        "distanceConstraint": {
            "stiffness": _curve(component.stiffness),
        },
        "angleRestorationConstraint": {
            "useAngleRestoration": True,
            "stiffness": _curve(component.stiffness),
            "velocityAttenuation": max(0.0, min(1.0, 1.0 - float(component.drag))),
            "gravityFalloff": 0.0,
        },
        "springConstraint": {
            "useSpring": component.component_type == "BONE_SPRING",
            "springPower": float(component.stiffness),
            "limitDistance": 0.1,
            "normalLimitRatio": 1.0,
            "springNoise": 0.0,
        },
        "colliderCollisionConstraint": {
            "mode": "Point",
            "friction": 0.05,
            "colliderList": [],
            "collisionBones": [],
            "limitDistance": _curve(component.radius),
        },
    }

    return {
        "component_id": component_id,
        "transform_contract": TRANSFORM_CONTRACT,
        "axis_conversion": AXIS_CONVERSION,
        "matrix_convention": MATRIX_CONVENTION,
        "bone_primary_axis": BONE_PRIMARY_AXIS,
        "component_type": component.component_type,
        "mc2_component_type": "MagicaCloth",
        "mc2_authoring_mode": cloth_type,
        "cloth_type": cloth_type,
        "display_name": component.display_name,
        "serialize_data": serialize_data,
        "armature_name": armature_object.name,
        "armature_data_name": armature_object.data.name if armature_object.data else "",
        "root_bone_name": component.root_bone_name,
        "root_bone_names": root_bone_names,
        "bone_connection_mode": component.connection_mode,
        "pose_space": "WORLD",
        "joint_radius": float(component.radius),
        "collider_ids": [],
        "collider_group_ids": [],
        "stiffness": float(component.stiffness),
        "damping": float(component.damping),
        "drag": float(component.drag),
        "gravity_strength": float(component.gravity_strength),
        "gravity_direction": (0.0, 0.0, -1.0),
        "armature_position": _vec3(armature_matrix.to_translation()),
        "armature_rotation": _quat(armature_matrix.to_quaternion()),
        "armature_scale": _vec3(armature_matrix.to_scale()),
        "bones": bones,
        "bone_attribute_overrides": _bone_attribute_overrides(component, bones),
    }


def _collider_snapshot(component):
    source_object = component.source_object
    if source_object is None:
        return None

    component_id = props.ensure_component_id(component)
    world_matrix = source_object.matrix_world.copy()
    shape_type = {
        "SPHERE_COLLIDER": "SPHERE",
        "CAPSULE_COLLIDER": "CAPSULE",
        "PLANE_COLLIDER": "PLANE",
    }.get(component.component_type, "SPHERE")
    mc2_component_type = {
        "SPHERE": "MagicaSphereCollider",
        "CAPSULE": "MagicaCapsuleCollider",
        "PLANE": "MagicaPlaneCollider",
    }[shape_type]
    size = (float(component.radius), 0.0, 0.0)
    if shape_type == "CAPSULE":
        size = (float(component.radius), float(component.radius), float(component.length))
    elif shape_type == "PLANE":
        size = (0.0, 0.0, 0.0)

    return {
        "component_id": component_id,
        "component_type": component.component_type,
        "mc2_component_type": mc2_component_type,
        "display_name": component.display_name,
        "object_name": source_object.name,
        "center": (0.0, 0.0, 0.0),
        "size": size,
        "shape_type": shape_type,
        "radius": float(component.radius),
        "height": float(component.length),
        "friction": float(component.collider_friction),
        "capsule_direction": "Y",
        "capsule_aligned_on_center": True,
        "capsule_reverse_direction": False,
        "capsule_end_radius": float(component.radius),
        "world_translation": _vec3(world_matrix.to_translation()),
        "world_rotation": _quat(world_matrix.to_quaternion()),
        "world_scale": _vec3(world_matrix.to_scale()),
    }


def build_authoring_snapshot(scene) -> dict:
    payload = {
        "schema_note": "MC2-style Unity component snapshot generated by HoCloth2.",
        "transform_contract": TRANSFORM_CONTRACT,
        "axis_conversion": AXIS_CONVERSION,
        "matrix_convention": MATRIX_CONVENTION,
        "bone_primary_axis": BONE_PRIMARY_AXIS,
        "components": [],
        "bone_chains": [],
        "colliders": [],
        "collider_groups": [],
        "cache_outputs": [],
        "mesh_writeback_targets": [],
    }

    for component in scene.hocloth2_mc2_components:
        component_id = props.ensure_component_id(component)
        payload["components"].append(
            {
                "component_id": component_id,
                "component_type": component.component_type,
                "mc2_component_type": "MagicaCloth" if component.component_type in props.BONE_COMPONENT_TYPES else component.component_type,
                "mc2_authoring_mode": component.component_type,
                "display_name": component.display_name,
                "enabled": bool(component.enabled),
            }
        )
        if not component.enabled:
            continue

        if component.component_type in props.BONE_COMPONENT_TYPES:
            chain = _bone_chain_snapshot(component)
            if chain is not None:
                payload["bone_chains"].append(chain)
        elif component.component_type in props.COLLIDER_COMPONENT_TYPES:
            collider = _collider_snapshot(component)
            if collider is not None:
                payload["colliders"].append(collider)

    return wrap_authoring_snapshot(BACKEND_ID, payload)
