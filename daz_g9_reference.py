"""
Master SK Reference File: DAZ Genesis 9 to UE5 / ALS Master Skeleton Hierarchy
Contains:
1. DAZ_TO_MASTER_MAP: Mapping DAZ / Diffeomorphic bone names to UE5 Master SK names.
2. MASTER_SK_HIERARCHY: Target parent-child bone relationships.
3. BONES_TO_DELETE: List of bones and bone patterns to delete.
"""

DAZ_TO_MASTER_MAP = {
    # Core Pelvis
    "pelvis": "pelvis",
    
    # Spine Chain
    "spine1": "spine_01",
    "spine2": "spine_02",
    "spine3": "spine_03",
    "spine4": "spine_04",
    "spine_01": "spine_01",
    "spine_02": "spine_02",
    "spine_03": "spine_03",
    "spine_04": "spine_04",
    
    # Neck & Head
    "neck": "neck01",
    "neck1": "neck01",
    "neck_01": "neck01",
    "neck2": "neck02",
    "neck_02": "neck02",
    "head": "head",
    
    # Pectorals
    "l_pectoral": "pectoral_l",
    "r_pectoral": "pectoral_r",
    
    # Clavicles & Arms
    "l_shoulder": "clavicle_l",
    "r_shoulder": "clavicle_r",
    "l_arm": "upperarm_l",
    "l_upperarm": "upperarm_l",
    "r_arm": "upperarm_r",
    "r_upperarm": "upperarm_r",
    "l_forearm": "lowerarm_l",
    "l_lowerarm": "lowerarm_l",
    "r_forearm": "lowerarm_r",
    "r_lowerarm": "lowerarm_r",
    "l_hand": "hand_l",
    "r_hand": "hand_r",
    
    # Arm Twist Bones
    "l_arm_twist": "upperarm_twist_01_l",
    "l_upperarm_twist": "upperarm_twist_01_l",
    "l_upperarmtwist1": "upperarm_twist_01_l",
    "l_upperarmtwist2": "upperarm_twist_02_l",
    "r_arm_twist": "upperarm_twist_01_r",
    "r_upperarm_twist": "upperarm_twist_01_r",
    "r_upperarmtwist1": "upperarm_twist_01_r",
    "r_upperarmtwist2": "upperarm_twist_02_r",
    "l_forearm_twist": "lowerarm_twist_01_l",
    "l_forearmtwist1": "lowerarm_twist_01_l",
    "l_forearmtwist2": "lowerarm_twist_02_l",
    "r_forearm_twist": "lowerarm_twist_01_r",
    "r_forearmtwist1": "lowerarm_twist_01_r",
    "r_forearmtwist2": "lowerarm_twist_02_r",

    # Metacarpals
    "l_indexmetacarpal": "indexmetacarpal_l",
    "r_indexmetacarpal": "indexmetacarpal_r",
    "l_midmetacarpal": "midmetacarpal_l",
    "r_midmetacarpal": "midmetacarpal_r",
    "l_ringmetacarpal": "ringmetacarpal_l",
    "r_ringmetacarpal": "ringmetacarpal_r",
    "l_pinkymetacarpal": "pinkymetacarpal_l",
    "r_pinkymetacarpal": "pinkymetacarpal_r",

    # Left Hand Fingers
    "l_thumb1": "thumb_01_l",
    "l_thumb2": "thumb_02_l",
    "l_thumb3": "thumb_03_l",
    "l_index1": "index_01_l",
    "l_index2": "index_02_l",
    "l_index3": "index_03_l",
    "l_mid1": "middle_01_l",
    "l_mid2": "middle_02_l",
    "l_mid3": "middle_03_l",
    "l_ring1": "ring_01_l",
    "l_ring2": "ring_02_l",
    "l_ring3": "ring_03_l",
    "l_pinky1": "pinky_01_l",
    "l_pinky2": "pinky_02_l",
    "l_pinky3": "pinky_03_l",

    # Right Hand Fingers
    "r_thumb1": "thumb_01_r",
    "r_thumb2": "thumb_02_r",
    "r_thumb3": "thumb_03_r",
    "r_index1": "index_01_r",
    "r_index2": "index_02_r",
    "r_index3": "index_03_r",
    "r_mid1": "middle_01_r",
    "r_mid2": "middle_02_r",
    "r_mid3": "middle_03_r",
    "r_ring1": "ring_01_r",
    "r_ring2": "ring_02_r",
    "r_ring3": "ring_03_r",
    "r_pinky1": "pinky_01_r",
    "r_pinky2": "pinky_02_r",
    "r_pinky3": "pinky_03_r",

    # Legs, Feet & Toes
    "l_thigh": "thigh_l",
    "r_thigh": "thigh_r",
    "l_shin": "calf_l",
    "r_shin": "calf_r",
    "l_foot": "foot_l",
    "r_foot": "foot_r",
    "l_toes": "toes_l",
    "r_toes": "toes_r",
    "ltoe": "toes_l",
    "rtoe": "toes_r",
    "ball_l": "toes_l",
    "ball_r": "toes_r",
    "l_thigh_twist": "thigh_twist_01_l",
    "r_thigh_twist": "thigh_twist_01_r",
    "l_tightwist1": "thigh_twist_01_l",
    "l_thightwist1": "thigh_twist_01_l",
    "l_tightwist2": "thigh_twist_02_l",
    "l_thightwist2": "thigh_twist_02_l",
    "r_tightwist1": "thigh_twist_01_r",
    "r_thightwist1": "thigh_twist_01_r",
    "r_tightwist2": "thigh_twist_02_r",
    "r_thightwist2": "thigh_twist_02_r",
}

MASTER_SK_HIERARCHY = {
    # Top-Level Deformation Bone
    "pelvis": None,
    
    # Spine Chain (under pelvis)
    "spine_01": "pelvis",
    "spine_02": "spine_01",
    "spine_03": "spine_02",
    "spine_04": "spine_03",
    
    # Legs (under pelvis)
    "thigh_l": "pelvis",
    "thigh_twist_01_l": "thigh_l",
    "thigh_twist_02_l": "thigh_twist_01_l",
    "calf_l": "thigh_l",
    "foot_l": "calf_l",
    "toes_l": "foot_l",
    
    "thigh_r": "pelvis",
    "thigh_twist_01_r": "thigh_r",
    "thigh_twist_02_r": "thigh_twist_01_r",
    "calf_r": "thigh_r",
    "foot_r": "calf_r",
    "toes_r": "foot_r",
    
    # Pectorals (parented to spine_03)
    "pectoral_l": "spine_03",
    "pectoral_r": "spine_03",

    # Neck & Head (parented to spine_04)
    "neck01": "spine_04",
    "neck02": "neck01",
    "head": "neck02",

    # Clavicles & Arms (parented to spine_04)
    "clavicle_l": "spine_04",
    "upperarm_l": "clavicle_l",
    "upperarm_twist_01_l": "upperarm_l",
    "upperarm_twist_02_l": "upperarm_twist_01_l",
    "lowerarm_l": "upperarm_l",
    "lowerarm_twist_01_l": "lowerarm_l",
    "lowerarm_twist_02_l": "lowerarm_twist_01_l",
    "hand_l": "lowerarm_l",
    
    "clavicle_r": "spine_04",
    "upperarm_r": "clavicle_r",
    "upperarm_twist_01_r": "upperarm_r",
    "upperarm_twist_02_r": "upperarm_twist_01_r",
    "lowerarm_r": "upperarm_r",
    "lowerarm_twist_01_r": "lowerarm_r",
    "lowerarm_twist_02_r": "lowerarm_twist_01_r",
    "hand_r": "lowerarm_r",
    
    # Metacarpals (children of hand_l / hand_r)
    "indexmetacarpal_l": "hand_l",
    "midmetacarpal_l": "hand_l",
    "ringmetacarpal_l": "hand_l",
    "pinkymetacarpal_l": "hand_l",

    "indexmetacarpal_r": "hand_r",
    "midmetacarpal_r": "hand_r",
    "ringmetacarpal_r": "hand_r",
    "pinkymetacarpal_r": "hand_r",

    # Left Hand Fingers
    "thumb_01_l": "hand_l",
    "thumb_02_l": "thumb_01_l",
    "thumb_03_l": "thumb_02_l",
    "index_01_l": "indexmetacarpal_l",
    "index_02_l": "index_01_l",
    "index_03_l": "index_02_l",
    "middle_01_l": "midmetacarpal_l",
    "middle_02_l": "middle_01_l",
    "middle_03_l": "middle_02_l",
    "ring_01_l": "ringmetacarpal_l",
    "ring_02_l": "ring_01_l",
    "ring_03_l": "ring_02_l",
    "pinky_01_l": "pinkymetacarpal_l",
    "pinky_02_l": "pinky_01_l",
    "pinky_03_l": "pinky_02_l",
    
    # Right Hand Fingers
    "thumb_01_r": "hand_r",
    "thumb_02_r": "thumb_01_r",
    "thumb_03_r": "thumb_02_r",
    "index_01_r": "indexmetacarpal_r",
    "index_02_r": "index_01_r",
    "index_03_r": "index_02_r",
    "middle_01_r": "midmetacarpal_r",
    "middle_02_r": "middle_01_r",
    "middle_03_r": "middle_02_r",
    "ring_01_r": "ringmetacarpal_r",
    "ring_02_r": "ring_01_r",
    "ring_03_r": "ring_02_r",
    "pinky_01_r": "pinkymetacarpal_r",
    "pinky_02_r": "pinky_01_r",
    "pinky_03_r": "pinky_02_r",

    # Top-Level IK Roots
    "ik_foot_root": None,
    "ik_foot_l": "ik_foot_root",
    "ik_foot_r": "ik_foot_root",
    "ik_hand_root": None,
    "ik_hand_l": "ik_hand_root",
    "ik_hand_r": "ik_hand_root",
}

BONES_TO_DELETE = [
    "root",
    "Root",
    "hip",
    "l_hand_anchor",
    "r_hand_anchor",
    "l_foot_anchor",
    "r_foot_anchor",
    # 20 Individual DAZ & Master SK Child Toe Bones (Left Foot)
    "l_bigtoe1", "l_bigtoe2", "l_indextoe1", "l_indextoe2",
    "l_midtoe1", "l_midtoe2", "l_ringtoe1", "l_ringtoe2",
    "l_pinkytoe1", "l_pinkytoe2", "l_pinkeytoe2",
    "bigtoe01_l", "bigtoe02_l", "indextoe01_l", "indextoe02_l",
    "midtoe01_l", "midtoe02_l", "ringtoe01_l", "ringtoe02_l",
    "pinkytoe01_l", "pinkytoe02_l", "pinkeytoe02_l",
    "bigtoe_01_l", "bigtoe_02_l", "indextoe_01_l", "indextoe_02_l",
    "midtoe_01_l", "midtoe_02_l", "ringtoe_01_l", "ringtoe_02_l",
    "pinkytoe_01_l", "pinkytoe_02_l", "pinkeytoe_02_l",
    # 20 Individual DAZ & Master SK Child Toe Bones (Right Foot)
    "r_bigtoe1", "r_bigtoe2", "r_indextoe1", "r_indextoe2",
    "r_midtoe1", "r_midtoe2", "r_ringtoe1", "r_ringtoe2",
    "r_pinkytoe1", "r_pinkytoe2", "r_pinkeytoe2",
    "bigtoe01_r", "bigtoe02_r", "indextoe01_r", "indextoe02_r",
    "midtoe01_r", "midtoe02_r", "ringtoe01_r", "ringtoe02_r",
    "pinkytoe01_r", "pinkytoe02_r", "pinkeytoe02_r",
    "bigtoe_01_r", "bigtoe_02_r", "indextoe_01_r", "indextoe_02_r",
    "midtoe_01_r", "midtoe_02_r", "ringtoe_01_r", "ringtoe_02_r",
    "pinkytoe_01_r", "pinkytoe_02_r", "pinkeytoe_02_r",
]
