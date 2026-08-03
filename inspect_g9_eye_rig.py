import bpy

def inspect_genesis9_eye_setup():
    print("=" * 80)
    print("GENESIS 9 EYE & EYELID RIG DIAGNOSTIC REPORT")
    print("=" * 80)

    # 1. Find active armature and mesh
    armature_obj = None
    mesh_obj = None

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE' and not armature_obj:
            armature_obj = obj
        elif obj.type == 'MESH' and not mesh_obj:
            mesh_obj = obj

    if not armature_obj:
        print("ERROR: No Armature object found in scene.")
        return

    print(f"Armature Object: {armature_obj.name}")
    if mesh_obj:
        print(f"Mesh Object: {mesh_obj.name}")

    # 2. Inspect Bone Hierarchy under 'head'
    print("\n--- BONE HIERARCHY UNDER HEAD ---")
    head_bone = armature_obj.data.bones.get("head") or armature_obj.data.bones.get("Head")
    if head_bone:
        def print_children(bone, depth=0):
            indent = "  " * depth
            print(f"{indent}- {bone.name} (parent: {bone.parent.name if bone.parent else 'None'})")
            for child in bone.children:
                print_children(child, depth + 1)
        print_children(head_bone)
    else:
        print("WARNING: 'head' bone not found!")

    # 3. Inspect Drivers on Armature Object & Data
    print("\n--- DRIVERS ON ARMATURE OBJECT & DATA ---")
    driver_count = 0
    for holder_name, holder in [("Object", armature_obj), ("Data", armature_obj.data)]:
        anim_data = getattr(holder, "animation_data", None)
        if anim_data and anim_data.drivers:
            for fcurve in anim_data.drivers:
                d = fcurve.driver
                dp = fcurve.data_path
                if any(k in dp.lower() for k in ["eye", "lid", "brow", "head", "face"]):
                    driver_count += 1
                    print(f"[{holder_name}] DataPath: {dp}")
                    print(f"  Expression: {d.expression}")
                    for var in d.variables:
                        print(f"  Var: {var.name} (type: {var.type})")
                        for tgt in var.targets:
                            id_name = tgt.id.name if tgt.id else "None"
                            subt = getattr(tgt, "subtarget", "N/A")
                            tchan = getattr(tgt, "transform_type", "N/A")
                            print(f"    Target ID: {id_name}, Subtarget: {subt}, TransformChannel: {tchan}")
    if driver_count == 0:
        print("No eye/eyelid drivers found on armature.")

    # 4. Inspect Constraints on Pose Bones
    print("\n--- CONSTRAINTS ON EYE & EYELID POSE BONES ---")
    constraint_count = 0
    for pb in armature_obj.pose.bones:
        b_name_lower = pb.name.lower()
        if any(k in b_name_lower for k in ["eye", "lid", "brow"]):
            if pb.constraints:
                print(f"PoseBone '{pb.name}':")
                for c in pb.constraints:
                    constraint_count += 1
                    subt = getattr(c, "subtarget", "N/A")
                    print(f"  - Constraint '{c.name}' (type: {c.type}, target bone: '{subt}', mute: {c.mute})")
    if constraint_count == 0:
        print("No constraints found on eye/eyelid pose bones.")

    # 5. Inspect Mesh Vertex Groups
    if mesh_obj:
        print("\n--- MESH VERTEX GROUPS (EYE / EYELID RELATED) ---")
        eye_vgs = []
        for vg in mesh_obj.vertex_groups:
            vgn_lower = vg.name.lower()
            if any(k in vgn_lower for k in ["eye", "lid", "brow"]):
                eye_vgs.append(vg.name)
        print(f"Found {len(eye_vgs)} eye/eyelid vertex groups: {eye_vgs}")

    print("=" * 80)

if __name__ == "__main__":
    inspect_genesis9_eye_setup()
