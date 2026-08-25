import bpy
from .. import config
from ..core import weight_utils

class MASTERSK_OT_finalize_rigs(bpy.types.Operator):
    """Step 8: Construct ALS Body Skeleton and ALS Head/Face Skeleton, bind meshes, and organize collections"""
    bl_idname = "mastersk.finalize_rigs"
    bl_label = "Step 8: Finalize & Dual Rig Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        als_arm = scene.mastersk_als_armature
        daz_arm = scene.mastersk_daz_armature
        body_mesh = scene.mastersk_body_mesh or scene.mastersk_mesh_obj
        head_mesh = scene.mastersk_head_mesh

        # Auto-find ALS Armature in scene if not explicitly set
        if not als_arm or als_arm.type != 'ARMATURE':
            for obj in scene.objects:
                if obj.type == 'ARMATURE' and "als" in obj.name.lower():
                    als_arm = obj
                    scene.mastersk_als_armature = obj
                    break

        if not als_arm or als_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "ALS Armature not found. Please run 'Step 5: Append Base Skeleton' and 'Step 7' first.")
            return {'CANCELLED'}

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 1. Setup Head / Face Armature (from ALS Base)
        head_arm = None
        if daz_arm and daz_arm.type == 'ARMATURE':
            bpy.ops.object.select_all(action='DESELECT')
            als_arm.select_set(True)
            context.view_layer.objects.active = als_arm
            bpy.ops.object.duplicate(linked=False)
            head_arm = context.active_object
            
            # Name object and data exactly "root_head" to avoid .001 clutter
            head_arm.name = "root_head"
            head_arm.data.name = "root_head"

            g9_head_arm = bpy.data.objects.get("G9_Head_Armature")
            if g9_head_arm:
                self.transfer_face_bones(g9_head_arm, head_arm)

            if head_mesh and head_mesh.type == 'MESH':
                for mod in list(head_mesh.modifiers):
                    if mod.type == 'ARMATURE':
                        head_mesh.modifiers.remove(mod)
                arm_mod_h = head_mesh.modifiers.new(name="Armature", type='ARMATURE')
                arm_mod_h.object = head_arm
                head_mesh.parent = head_arm

        # 2. Setup Body Armature
        # Name object and data exactly "root" as expected by UE
        als_arm.name = "root"
        als_arm.data.name = "root"

        if body_mesh and body_mesh.type == 'MESH':
            for mod in list(body_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    body_mesh.modifiers.remove(mod)
            arm_mod = body_mesh.modifiers.new(name="Armature", type='ARMATURE')
            arm_mod.object = als_arm
            body_mesh.parent = als_arm

        # 3. Organize Scene Collections
        self.organize_collections(context, als_arm, body_mesh, head_arm, head_mesh)

        # 4. Transfer Calf Weights to Twist Bones
        if body_mesh and body_mesh.type == 'MESH':
            weight_utils.rename_vertex_groups(body_mesh, {
                "calf_l": "calf_twist_01_l",
                "calf_r": "calf_twist_01_r"
            })

        # 5. COMPLETELY Delete original Daz armatures (prevents clutter)
        g9_head_arm = bpy.data.objects.get("G9_Head_Armature")
        for arm_to_delete in [daz_arm, g9_head_arm]:
            if arm_to_delete:
                try:
                    bpy.ops.object.select_all(action='DESELECT')
                    arm_to_delete.select_set(True)
                    context.view_layer.objects.active = arm_to_delete
                    bpy.ops.object.delete(use_global=False, confirm=False)
                except Exception:
                    pass
                
        # 6. Purge orphan data
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        self.report({'INFO'}, "Step 8 Complete: Generated clean 'root' and 'root_head' dual rigs ready for Unreal Engine 5.")
        
        # Trigger the popup warning for manual spine alignment
        bpy.ops.mastersk.spine_warning_popup('INVOKE_DEFAULT')
        
        scene.mastersk_progress_step = 9
        return {'FINISHED'}

    def transfer_face_bones(self, daz_arm, head_arm):
        """Copies facial rig bones from Daz Armature onto ALS Head Armature under the 'head' bone."""
        bpy.context.view_layer.objects.active = daz_arm
        bpy.ops.object.mode_set(mode='EDIT')
        daz_ebs = daz_arm.data.edit_bones

        face_bone_names = []
        als_core_names = set(config.BONE_NAME_MAPPING.values())
        for b in daz_ebs:
            if b.name not in als_core_names and b.name not in config.BASE_TORSO_BONES:
                face_bone_names.append(b.name)

        face_bones_data = {}
        for bname in face_bone_names:
            if bname in daz_ebs:
                eb = daz_ebs[bname]
                parent_name = eb.parent.name if eb.parent else "head"
                face_bones_data[bname] = {
                    "head": eb.head.copy(),
                    "tail": eb.tail.copy(),
                    "roll": eb.roll,
                    "parent": parent_name,
                    "use_deform": eb.use_deform
                }
        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.context.view_layer.objects.active = head_arm
        bpy.ops.object.mode_set(mode='EDIT')
        head_ebs = head_arm.data.edit_bones

        bones_to_remove = [
            b.name for b in head_ebs
            if b.name not in config.BASE_TORSO_BONES
        ]
        for bname in bones_to_remove:
            eb = head_ebs.get(bname)
            if eb:
                head_ebs.remove(eb)

        created_bones = {}
        import mathutils
        for bname, data in face_bones_data.items():
            new_eb = head_ebs.new(bname)
            new_eb.head = data["head"]
            
            # Safeguard: Blender auto-deletes 0-length bones. Push tail out by 1cm if identical.
            if (data["tail"] - data["head"]).length < 0.0001:
                new_eb.tail = data["head"] + mathutils.Vector((0, 0.01, 0))
            else:
                new_eb.tail = data["tail"]
                
            new_eb.roll = data["roll"]
            new_eb.use_deform = data["use_deform"]
            created_bones[bname] = new_eb

        for bname, data in face_bones_data.items():
            eb = created_bones.get(bname)
            pname = data["parent"]
            if eb and pname in head_ebs:
                eb.parent = head_ebs[pname]

        bpy.ops.object.mode_set(mode='OBJECT')

    def organize_collections(self, context, body_arm, body_mesh, head_arm, head_mesh):
        """Creates clean collections for Body and Head export."""
        scene = context.scene

        def get_col(name):
            col = bpy.data.collections.get(name)
            if not col:
                col = bpy.data.collections.new(name)
                scene.collection.children.link(col)
            return col

        body_col = get_col("MasterSK_Body_Export")
        head_col = get_col("MasterSK_Head_Export")

        def move_to_col(obj, target_col):
            if not obj:
                return
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            target_col.objects.link(obj)

        move_to_col(body_arm, body_col)
        move_to_col(body_mesh, body_col)
        move_to_col(head_arm, head_col)
        move_to_col(head_mesh, head_col)

class MASTERSK_OT_spine_warning_popup(bpy.types.Operator):
    """Notification to manually align spine bones"""
    bl_idname = "mastersk.spine_warning_popup"
    bl_label = "Action Required: Manual Spine Alignment"
    bl_options = {'REGISTER', 'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=450)

    def draw(self, context):
        layout = self.layout
        layout.label(text="WARNING: Spine Bones Require Manual Alignment!", icon='ERROR')
        layout.label(text="To perfectly match your mesh's proportions while maintaining exact UE5")
        layout.label(text="local axes (roll), the spine bones were left at their original offsets.")
        layout.separator()
        layout.label(text="Please manually adjust the Z-location of:")
        layout.label(text="  • spine_01")
        layout.label(text="  • spine_02")
        layout.label(text="  • spine_03")
        layout.separator()
        layout.label(text="Ensure they align perfectly with their weight paint while facing backward.")
