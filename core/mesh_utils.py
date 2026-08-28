# MasterSK - Mesh Slicing & Separation Utilities
import bpy
import bmesh

def classify_material_slots(mesh_obj, head_keywords, body_keywords):
    """Returns (head_slot_indices, body_slot_indices) based on material name keyword matching."""
    head_indices = set()
    body_indices = set()
    
    for idx, slot in enumerate(mesh_obj.material_slots):
        if not slot.material:
            body_indices.add(idx)
            continue
            
        mat_name = slot.material.name.lower()
        
        is_head = any(kw.lower() in mat_name for kw in head_keywords)
        is_body = any(kw.lower() in mat_name for kw in body_keywords)
        
        if is_head:
            head_indices.add(idx)
        elif is_body:
            body_indices.add(idx)
        else:
            if "head" in mat_name or "face" in mat_name:
                head_indices.add(idx)
            else:
                body_indices.add(idx)
                
    return head_indices, body_indices

def split_mesh_by_materials(mesh_obj, head_keywords, body_keywords):
    """
    Splits the Genesis 9 character mesh into two separate objects:
    - G9_Head_Mesh
    - G9_Body_Mesh
    """
    if mesh_obj.type != 'MESH':
        raise ValueError(f"Object {mesh_obj.name} is not a mesh.")
        
    head_slots, body_slots = classify_material_slots(mesh_obj, head_keywords, body_keywords)
    
    if not head_slots:
        raise ValueError("Could not find any Head material slots on the mesh.")
    if not body_slots:
        raise ValueError("Could not find any Body material slots on the mesh.")
        
    bpy.context.view_layer.objects.active = mesh_obj
    if bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
        
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)
    bpy.ops.object.duplicate(linked=False)
    head_obj = bpy.context.active_object
    head_obj.name = "G9_Head_Mesh"
    
    mesh_obj.name = "G9_Body_Mesh"
    body_obj = mesh_obj
    
    # 1. On Body Object: Delete polygons that belong to head slots
    bpy.context.view_layer.objects.active = body_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm_body = bmesh.from_edit_mesh(body_obj.data)
    bm_body.faces.ensure_lookup_table()
    faces_to_delete = [f for f in bm_body.faces if f.material_index in head_slots]
    bmesh.ops.delete(bm_body, geom=faces_to_delete, context='FACES')
    bm_body.verts.ensure_lookup_table()
    loose_verts = [v for v in bm_body.verts if not v.link_faces]
    bmesh.ops.delete(bm_body, geom=loose_verts, context='VERTS')
    bmesh.update_edit_mesh(body_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 2. On Head Object: Delete polygons that belong to body slots
    bpy.context.view_layer.objects.active = head_obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm_head = bmesh.from_edit_mesh(head_obj.data)
    bm_head.faces.ensure_lookup_table()
    faces_to_delete = [f for f in bm_head.faces if f.material_index in body_slots]
    bmesh.ops.delete(bm_head, geom=faces_to_delete, context='FACES')
    bm_head.verts.ensure_lookup_table()
    loose_verts = [v for v in bm_head.verts if not v.link_faces]
    bmesh.ops.delete(bm_head, geom=loose_verts, context='VERTS')
    bmesh.update_edit_mesh(head_obj.data)
    bpy.ops.object.mode_set(mode='OBJECT')
    
    clean_unused_material_slots(body_obj)
    clean_unused_material_slots(head_obj)
    
    return body_obj, head_obj

def clean_unused_material_slots(mesh_obj):
    """Removes material slots that are not assigned to any faces on the mesh."""
    if mesh_obj.type != 'MESH':
        return
    used_mat_indices = {f.material_index for f in mesh_obj.data.polygons}
    
    bpy.context.view_layer.objects.active = mesh_obj
    slots_to_remove = [i for i in range(len(mesh_obj.material_slots)) if i not in used_mat_indices]
    
    for idx in reversed(slots_to_remove):
        mesh_obj.active_material_index = idx
        bpy.ops.object.material_slot_remove()

def optimize_materials_and_uvs(mesh_obj):
    """
    Optimizes draw calls by merging:
    - 'Mouth Cavity' -> 'Head'
    - 'Fingernails' & 'Toenails' -> 'Arms' (and re-maps their UVs to the custom layout)
    """
    import os
    import json
    from .. import config
    
    if mesh_obj.type != 'MESH':
        return
        
    mesh = mesh_obj.data
    
    # 1. Identify material indices
    head_idx = -1
    arms_idx = -1
    mouth_indices = set()
    nail_indices = set()
    
    for i, slot in enumerate(mesh_obj.material_slots):
        if not slot.material:
            continue
        name = slot.material.name.lower()
        
        if "head" in name or "face" in name:
            head_idx = i
        elif "arm" in name:
            arms_idx = i
        elif "mouth" in name or "cavity" in name:
            mouth_indices.add(i)
        elif "nail" in name:
            nail_indices.add(i)
            
    # 2. Load custom nail UV data
    uv_data = {}
    json_path = os.path.join(os.path.dirname(__file__), "nail_uv_data.json")
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            try:
                # Convert string keys back to int loop indices
                uv_data = {int(k): v for k, v in json.load(f).items()}
            except Exception as e:
                print(f"Failed to load nail UVs: {e}")
    else:
        print(f"Warning: {json_path} not found. Nails will not be UV remapped.")
        
    # 3. Process Polygons
    uv_layer = mesh.uv_layers.active
    
    for poly in mesh.polygons:
        # Merge Mouth Cavity to Head
        if poly.material_index in mouth_indices and head_idx != -1:
            poly.material_index = head_idx
            
        # Merge Nails to Arms and remap UVs
        elif poly.material_index in nail_indices and arms_idx != -1:
            poly.material_index = arms_idx
            if uv_layer and uv_data:
                for loop_idx in poly.loop_indices:
                    if loop_idx in uv_data:
                        uv_layer.data[loop_idx].uv = uv_data[loop_idx]
                        
    # 4. Clean up the now-empty material slots (Mouth Cavity, Nails)
    clean_unused_material_slots(mesh_obj)

    # 5. UDIM Sequencing for Body Mesh (Body: 0, Legs: +1, Arms: +2)
    if uv_layer:
        for poly in mesh.polygons:
            mat_idx = poly.material_index
            if mat_idx >= len(mesh_obj.material_slots) or not mesh_obj.material_slots[mat_idx].material:
                continue
                
            mat_name = mesh_obj.material_slots[mat_idx].material.name.lower()
            shift_x = 0.0
            
            if "leg" in mat_name:
                shift_x = 1.0
            elif "arm" in mat_name or "nail" in mat_name:
                shift_x = 2.0
                
            for loop_idx in poly.loop_indices:
                current_u = uv_layer.data[loop_idx].uv[0]
                uv_layer.data[loop_idx].uv[0] = (current_u % 1.0) + shift_x

    # 5. UDIM Sequencing for Body Mesh (Body: 0, Legs: +1, Arms: +2)
    if uv_layer:
        for poly in mesh.polygons:
            mat_idx = poly.material_index
            if mat_idx >= len(mesh_obj.material_slots) or not mesh_obj.material_slots[mat_idx].material:
                continue
                
            mat_name = mesh_obj.material_slots[mat_idx].material.name.lower()
            shift_x = 0.0
            
            if "leg" in mat_name:
                shift_x = 1.0
            elif "arm" in mat_name or "nail" in mat_name:
                shift_x = 2.0
                
            for loop_idx in poly.loop_indices:
                current_u = uv_layer.data[loop_idx].uv[0]
                uv_layer.data[loop_idx].uv[0] = (current_u % 1.0) + shift_x
