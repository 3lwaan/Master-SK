import bpy
from .. import config
from ..core import weight_utils

class MASTERSK_OT_unified_finalize(bpy.types.Operator):
    """Step 8: Construct ALS Body Skeleton, bind mesh, and organize collections"""
    bl_idname = "mastersk.unified_finalize"
    bl_label = "Step 8: Finalize Single Rig Setup"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene
        als_arm = scene.mastersk_als_armature
        daz_arm = scene.mastersk_daz_armature
        body_mesh = scene.mastersk_body_mesh or scene.mastersk_mesh_obj

        if not als_arm or als_arm.type != 'ARMATURE':
            for obj in scene.objects:
                if obj.type == 'ARMATURE' and "als" in obj.name.lower():
                    als_arm = obj
                    scene.mastersk_als_armature = obj
                    break

        if not als_arm or als_arm.type != 'ARMATURE':
            self.report({'ERROR'}, "ALS Armature not found. Please run 'Step 5' first.")
            return {'CANCELLED'}

        if context.object and context.object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')

        # 1. Setup Body Armature
        als_arm.name = "root"
        als_arm.data.name = "root"

        if body_mesh and body_mesh.type == 'MESH':
            for mod in list(body_mesh.modifiers):
                if mod.type == 'ARMATURE':
                    body_mesh.modifiers.remove(mod)
            arm_mod = body_mesh.modifiers.new(name="Armature", type='ARMATURE')
            arm_mod.object = als_arm
            body_mesh.parent = als_arm

        # 2. Organize Scene Collections
        self.organize_collections(context, als_arm, body_mesh)

        # 3. Transfer Calf Weights to Twist Bones
        if body_mesh and body_mesh.type == 'MESH':
            weight_utils.rename_vertex_groups(body_mesh, {
                "calf_l": "calf_twist_01_l",
                "calf_r": "calf_twist_01_r"
            })

        # 4. Hide original Daz armature
        data_col = bpy.data.collections.get("MasterSK_Data")
        if not data_col:
            data_col = bpy.data.collections.new("MasterSK_Data")
            scene.collection.children.link(data_col)
            
        data_col.hide_viewport = True
        data_col.hide_render = True
        
        if daz_arm:
            for c in list(daz_arm.users_collection):
                c.objects.unlink(daz_arm)
            data_col.objects.link(daz_arm)
            if daz_arm.type == 'ARMATURE':
                for pb in daz_arm.pose.bones:
                    pb.matrix_basis.identity()

        # Delete any leftover head armatures if they existed from previous attempts
        g9_head_arm = bpy.data.objects.get("G9_Head_Armature")
        if g9_head_arm:
            try:
                bpy.ops.object.select_all(action='DESELECT')
                g9_head_arm.select_set(True)
                context.view_layer.objects.active = g9_head_arm
                bpy.ops.object.delete(use_global=False, confirm=False)
            except Exception:
                pass
                
        # 5. Purge orphan data
        bpy.ops.outliner.orphans_purge(do_local_ids=True, do_linked_ids=True, do_recursive=True)

        self.report({'INFO'}, "Step 8 Complete: Generated clean 'root' single rig ready for Unreal Engine 5.")
        
        bpy.ops.mastersk.spine_warning_popup('INVOKE_DEFAULT')
        
        scene.mastersk_progress_step = 9
        return {'FINISHED'}

    def organize_collections(self, context, body_arm, body_mesh):
        scene = context.scene

        def get_col(name):
            col = bpy.data.collections.get(name)
            if not col:
                col = bpy.data.collections.new(name)
                scene.collection.children.link(col)
            return col

        export_col = get_col("MasterSK_Unified_Export")

        def move_to_col(obj, target_col):
            if not obj:
                return
            for c in list(obj.users_collection):
                c.objects.unlink(obj)
            target_col.objects.link(obj)

        move_to_col(body_arm, export_col)
        move_to_col(body_mesh, export_col)
