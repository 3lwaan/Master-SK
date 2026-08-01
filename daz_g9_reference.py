"""
Master SK Reference File: DAZ Genesis 9 to UE5 / ALS Master Skeleton Hierarchy
Contains:
1. DAZ_TO_MASTER_MAP: Mapping DAZ / Diffeomorphic bone names to UE5 Master SK names.
2. MASTER_SK_HIERARCHY: Target parent-child bone relationships.
3. BONES_TO_DELETE: List of bones and bone patterns to delete.
"""

DAZ_TO_MASTER_MAP = {
    # Core Root / Hips
    "hip": "pelvis",
    "pelvis": "pelvis",
    
    # Spine Chain
    "spine1": "spine_01",
    "spine2": "spine_02",
    "spine3": "spine_03",
    "neck": "neck_01",
    "head": "head",
    
    # Left Arm
    "l_shoulder": "clavicle_l",
    "l_arm": "upperarm_l",
    "l_forearm": "lowerarm_l",
    "l_hand": "hand_l",
    
    # Right Arm
    "r_shoulder": "clavicle_r",
    "r_arm": "upperarm_r",
    "r_forearm": "lowerarm_r",
    "r_hand": "hand_r",
    
    # Left Leg
    "l_thigh": "thigh_l",
    "l_shin": "calf_l",
    "l_foot": "foot_l",
    "l_toes": "ball_l",
    
    # Right Leg
    "r_thigh": "thigh_r",
    "r_shin": "calf_r",
    "r_foot": "foot_r",
    "r_toes": "ball_r",
    
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

    # Twist Bones
    "l_arm_twist": "upperarm_twist_01_l",
    "l_upperarm_twist": "upperarm_twist_01_l",
    "l_forearm_twist": "lowerarm_twist_01_l",
    "r_arm_twist": "upperarm_twist_01_r",
    "r_upperarm_twist": "upperarm_twist_01_r",
    "r_forearm_twist": "lowerarm_twist_01_r",
    "l_thigh_twist": "thigh_twist_01_l",
    "r_thigh_twist": "thigh_twist_01_r",
}

MASTER_SK_HIERARCHY = {
    # Top-Level Deformation Bone
    "pelvis": None,
    
    # Spine
    "spine_01": "pelvis",
    "spine_02": "spine_01",
    "spine_03": "spine_02",
    "neck_01": "spine_03",
    "head": "neck_01",
    
    # Left Arm
    "clavicle_l": "spine_03",
    "upperarm_l": "clavicle_l",
    "lowerarm_l": "upperarm_l",
    "hand_l": "lowerarm_l",
    
    # Left Hand Fingers
    "thumb_01_l": "hand_l",
    "thumb_02_l": "thumb_01_l",
    "thumb_03_l": "thumb_02_l",
    "index_01_l": "hand_l",
    "index_02_l": "index_01_l",
    "index_03_l": "index_02_l",
    "middle_01_l": "hand_l",
    "middle_02_l": "middle_01_l",
    "middle_03_l": "middle_02_l",
    "ring_01_l": "hand_l",
    "ring_02_l": "ring_01_l",
    "ring_03_l": "ring_02_l",
    "pinky_01_l": "hand_l",
    "pinky_02_l": "pinky_01_l",
    "pinky_03_l": "pinky_02_l",
    
    # Right Arm
    "clavicle_r": "spine_03",
    "upperarm_r": "clavicle_r",
    "lowerarm_r": "upperarm_r",
    "hand_r": "lowerarm_r",
    
    # Right Hand Fingers
    "thumb_01_r": "hand_r",
    "thumb_02_r": "thumb_01_r",
    "thumb_03_r": "thumb_02_r",
    "index_01_r": "hand_r",
    "index_02_r": "index_01_r",
    "index_03_r": "index_02_r",
    "middle_01_r": "hand_r",
    "middle_02_r": "middle_01_r",
    "middle_03_r": "middle_02_r",
    "ring_01_r": "hand_r",
    "ring_02_r": "ring_01_r",
    "ring_03_r": "ring_02_r",
    "pinky_01_r": "hand_r",
    "pinky_02_r": "pinky_01_r",
    "pinky_03_r": "pinky_02_r",
    
    # Legs
    "thigh_l": "pelvis",
    "calf_l": "thigh_l",
    "foot_l": "calf_l",
    "ball_l": "foot_l",
    
    "thigh_r": "pelvis",
    "calf_r": "thigh_r",
    "foot_r": "calf_r",
    "ball_r": "foot_r",
    
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
    "l_hand_anchor",
    "r_hand_anchor",
    "l_foot_anchor",
    "r_foot_anchor",
]
