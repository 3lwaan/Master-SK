# MasterSK - Vertex Group & Weight Utilities
import bpy

def get_or_create_vertex_group(mesh_obj, group_name):
    """Returns an existing vertex group or creates a new one."""
    vg = mesh_obj.vertex_groups.get(group_name)
    if vg is None:
        vg = mesh_obj.vertex_groups.new(name=group_name)
    return vg

def merge_vertex_groups(mesh_obj, consolidation_map, remove_sources=True):
    """
    Consolidates weights from source vertex groups into target vertex groups.
    consolidation_map: { 'target_group_name': ['src_group1', 'src_group2', ...] }
    """
    if mesh_obj.type != 'MESH':
        raise ValueError(f"Object {mesh_obj.name} is not a mesh.")
    
    mesh = mesh_obj.data
    vgroups = mesh_obj.vertex_groups
    
    total_merged = 0
    groups_to_remove = set()
    
    for target_name, source_names in consolidation_map.items():
        existing_sources = []
        for src in source_names:
            vg = vgroups.get(src)
            if vg is not None:
                existing_sources.append(vg)
                
        if not existing_sources:
            continue
            
        target_vg = get_or_create_vertex_group(mesh_obj, target_name)
        target_idx = target_vg.index
        src_indices = [vg.index for vg in existing_sources]
        
        for v in mesh.vertices:
            target_weight = 0.0
            for g in v.groups:
                if g.group == target_idx:
                    target_weight = g.weight
                    break
            
            additional_weight = 0.0
            for g in v.groups:
                if g.group in src_indices:
                    additional_weight += g.weight
                    
            if additional_weight > 0.0:
                new_weight = min(1.0, target_weight + additional_weight)
                target_vg.add([v.index], new_weight, 'REPLACE')
                total_merged += 1
                
        if remove_sources:
            for vg in existing_sources:
                groups_to_remove.add(vg.name)
                
    if remove_sources:
        for grp_name in groups_to_remove:
            vg = vgroups.get(grp_name)
            if vg:
                vgroups.remove(vg)
                
    return total_merged, len(groups_to_remove)

def rename_vertex_groups(mesh_obj, mapping):
    """
    Renames vertex groups according to the mapping dictionary.
    mapping: { 'old_name': 'new_name' }
    """
    if mesh_obj.type != 'MESH':
        raise ValueError(f"Object {mesh_obj.name} is not a mesh.")
        
    vgroups = mesh_obj.vertex_groups
    renamed_count = 0
    
    for old_name, new_name in mapping.items():
        if old_name == new_name:
            continue
        vg = vgroups.get(old_name)
        if vg:
            existing_target = vgroups.get(new_name)
            if existing_target and existing_target != vg:
                for v in mesh_obj.data.vertices:
                    for g in v.groups:
                        if g.group == vg.index:
                            existing_target.add([v.index], g.weight, 'ADD')
                vgroups.remove(vg)
            else:
                vg.name = new_name
            renamed_count += 1
            
    return renamed_count

def rename_dynamic_vertex_groups(mesh_obj):
    """
    Catches any remaining vertex groups with 'l_' or 'r_' prefixes (like facial groups)
    and converts them to Unreal Engine '_l' / '_r' suffixes.
    """
    if not mesh_obj or mesh_obj.type != 'MESH':
        return 0

    renamed_count = 0
    vgroups = mesh_obj.vertex_groups

    for vg in vgroups:
        if vg.name.startswith("l_"):
            new_name = vg.name[2:] + "_l"
            if not vgroups.get(new_name):
                vg.name = new_name
                renamed_count += 1
        elif vg.name.startswith("r_"):
            new_name = vg.name[2:] + "_r"
            if not vgroups.get(new_name):
                vg.name = new_name
                renamed_count += 1

    return renamed_count

def prune_unweighted_groups(mesh_obj, threshold=0.0001):
    """Removes vertex groups that have no influence."""
    if mesh_obj.type != 'MESH':
        return 0
        
    mesh = mesh_obj.data
    vgroups = mesh_obj.vertex_groups
    
    used_indices = set()
    for v in mesh.vertices:
        for g in v.groups:
            if g.weight > threshold:
                used_indices.add(g.group)
                
    removed_count = 0
    for vg in list(vgroups):
        if vg.index not in used_indices:
            vgroups.remove(vg)
            removed_count += 1
            
    return removed_count

def normalize_all_weights(mesh_obj):
    """Normalizes vertex group weights for each vertex to sum up to 1.0."""
    if mesh_obj.type != 'MESH':
        return
        
    mesh = mesh_obj.data
    for v in mesh.vertices:
        total_w = sum(g.weight for g in v.groups)
        if total_w > 0.00001 and abs(total_w - 1.0) > 0.0001:
            for g in v.groups:
                g.weight = g.weight / total_w
