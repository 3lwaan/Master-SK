# MasterSK Configuration & Mapping Tables
# Pipeline v3: ALS hierarchy — "root" is the armature object, pelvis is
# the top-level bone (no root bone exists in ALS).
import os

ADDON_NAME = "MasterSK"
ASSET_BLEND_FILE = "als_base_skeleton.blend"

def get_asset_path(filename=ASSET_BLEND_FILE):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, "assets", filename)

# ---------------------------------------------------------------------------
# Sentinel used in WEIGHT_CONSOLIDATION_MAP to reference the dynamic root bone.
# The root bone in Genesis 9 is named after the character (e.g. "Anice", "Sara").
# Operators must detect it at runtime as the only bone with no parent.
# In Step 2, this bone is DELETED and its weight merges into pelvis.
# ---------------------------------------------------------------------------
ROOT_BONE_SENTINEL = "__ROOT__"

# ---------------------------------------------------------------------------
# Step 1: Weight Consolidation Map
# Source vertex groups are merged INTO the target (key) vertex group.
# The target group is created if it does not exist.
# After merging, source groups are deleted from the mesh.
# ---------------------------------------------------------------------------
WEIGHT_CONSOLIDATION_MAP = {
    # Root & Hip -- hip weight merges into the character-named root bone.
    # In Step 2, the root bone itself is deleted and its weight merges
    # into pelvis (since ALS has no root bone).
    ROOT_BONE_SENTINEL: ["hip"],

    # Spines & Pectorals
    "spine3": [
        "spine4", "l_pectoral", "r_pectoral",
        "l_pectoral(drv)", "r_pectoral(drv)"
    ],

    # Neck
    "neck1": ["neck2"],

    # Hands, Metacarpals & Anchors
    "l_hand": [
        "l_hand_anchor", "l_indexmetacarpal", "l_midmetacarpal",
        "l_ringmetacarpal", "l_pinkymetacarpal"
    ],
    "r_hand": [
        "r_hand_anchor", "r_indexmetacarpal", "r_midmetacarpal",
        "r_ringmetacarpal", "r_pinkymetacarpal"
    ],

    # Left Foot (metatarsal merges into foot, not toes)
    "l_foot": ["l_metatarsal"],

    # Left Toes (merge all 10 individual toe bones into l_toes)
    "l_toes": [
        "l_bigtoe1", "l_bigtoe2",
        "l_indextoe1", "l_indextoe2", "l_midtoe1", "l_midtoe2",
        "l_ringtoe1", "l_ringtoe2", "l_pinkytoe1", "l_pinkytoe2"
    ],

    # Right Foot
    "r_foot": ["r_metatarsal"],

    # Right Toes
    "r_toes": [
        "r_bigtoe1", "r_bigtoe2",
        "r_indextoe1", "r_indextoe2", "r_midtoe1", "r_midtoe2",
        "r_ringtoe1", "r_ringtoe2", "r_pinkytoe1", "r_pinkytoe2"
    ],

    # Arm Twists & Drivers (twist2 + both drv merge into twist1)
    "l_upperarmtwist1": [
        "l_upperarmtwist2", "l_upperarmtwist1(drv)", "l_upperarmtwist2(drv)"
    ],
    "r_upperarmtwist1": [
        "r_upperarmtwist2", "r_upperarmtwist1(drv)", "r_upperarmtwist2(drv)"
    ],
    "l_forearmtwist1": [
        "l_forearmtwist2", "l_forearmtwist1(drv)", "l_forearmtwist2(drv)"
    ],
    "r_forearmtwist1": [
        "r_forearmtwist2", "r_forearmtwist1(drv)", "r_forearmtwist2(drv)"
    ],

    # Leg Twists & Drivers
    "l_thightwist1": [
        "l_thightwist2", "l_thightwist1(drv)", "l_thightwist2(drv)"
    ],
    "r_thightwist1": [
        "r_thightwist2", "r_thightwist1(drv)", "r_thightwist2(drv)"
    ],
}

# ---------------------------------------------------------------------------
# Step 2: Bones to Keep (Whitelist)
# After weight merging, every bone NOT in this set (and NOT a facial bone
# child of 'head') is deleted from the armature in Edit Mode.
# The character-named root bone is NOT in this set — it gets deleted.
# "hip" is NOT in this set — it was merged in Step 1.
# Pelvis becomes the top-level bone (matching ALS).
# ---------------------------------------------------------------------------
BONES_TO_KEEP = {
    # Pelvis is the top-level bone in ALS (no root bone)
    "pelvis",
    "spine1", "spine2", "spine3",
    "neck1", "head",

    # Left Arm
    "l_shoulder", "l_upperarm", "l_upperarmtwist1",
    "l_forearm", "l_forearmtwist1", "l_hand",

    # Left Fingers
    "l_thumb1", "l_thumb2", "l_thumb3",
    "l_index1", "l_index2", "l_index3",
    "l_mid1", "l_mid2", "l_mid3",
    "l_ring1", "l_ring2", "l_ring3",
    "l_pinky1", "l_pinky2", "l_pinky3",

    # Right Arm
    "r_shoulder", "r_upperarm", "r_upperarmtwist1",
    "r_forearm", "r_forearmtwist1", "r_hand",

    # Right Fingers
    "r_thumb1", "r_thumb2", "r_thumb3",
    "r_index1", "r_index2", "r_index3",
    "r_mid1", "r_mid2", "r_mid3",
    "r_ring1", "r_ring2", "r_ring3",
    "r_pinky1", "r_pinky2", "r_pinky3",

    # Left Leg
    "l_thigh", "l_thightwist1", "l_shin", "l_foot", "l_toes",

    # Right Leg
    "r_thigh", "r_thightwist1", "r_shin", "r_foot", "r_toes",
}

# ---------------------------------------------------------------------------
# Step 3: Bone Rename Mapping (G9 -> ALS)
# Applied to both armature bones AND mesh vertex groups simultaneously.
# Note: There is NO "root" bone in ALS. "root" is the armature object name.
# Pelvis is the top-level bone and keeps its name.
# ---------------------------------------------------------------------------
BONE_NAME_MAPPING = {
    # Core / Pelvis (top-level bone in ALS)
    "pelvis": "pelvis",
    "spine1": "spine_01",
    "spine2": "spine_02",
    "spine3": "spine_03",

    # Neck & Head
    "neck1": "neck_01",
    "head": "head",

    # Left Arm Chain
    "l_shoulder": "clavicle_l",
    "l_upperarm": "upperarm_l",
    "l_upperarmtwist1": "upperarm_twist_01_l",
    "l_forearm": "lowerarm_l",
    "l_forearmtwist1": "lowerarm_twist_01_l",
    "l_hand": "hand_l",

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

    # Right Arm Chain
    "r_shoulder": "clavicle_r",
    "r_upperarm": "upperarm_r",
    "r_upperarmtwist1": "upperarm_twist_01_r",
    "r_forearm": "lowerarm_r",
    "r_forearmtwist1": "lowerarm_twist_01_r",
    "r_hand": "hand_r",

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

    # Left Leg Chain
    "l_thigh": "thigh_l",
    "l_thightwist1": "thigh_twist_01_l",
    "l_shin": "calf_l",
    "l_foot": "foot_l",
    "l_toes": "ball_l",

    # Right Leg Chain
    "r_thigh": "thigh_r",
    "r_thightwist1": "thigh_twist_01_r",
    "r_shin": "calf_r",
    "r_foot": "foot_r",
    "r_toes": "ball_r",
}

# ---------------------------------------------------------------------------
# Keywords to classify material slots for mesh separation (Step 5)
# ---------------------------------------------------------------------------
HEAD_MATERIAL_KEYWORDS = [
    "head", "face", "eye", "cornea", "teeth", "mouth",
    "tongue", "eyelash", "brow", "tear", "moisture", "pupil", "sclera"
]

BODY_MATERIAL_KEYWORDS = [
    "body", "torso", "arm", "arms", "leg", "legs",
    "skin", "nails", "limbs", "finger", "fingers"
]

# ---------------------------------------------------------------------------
# ALS Epic Mannequin Base IK Bones (appended from asset, Step 6)
# ---------------------------------------------------------------------------
ALS_IK_BONES = [
    "ik_foot_root", "ik_foot_l", "ik_foot_r",
    "ik_hand_root", "ik_hand_gun", "ik_hand_l", "ik_hand_r"
]

# ---------------------------------------------------------------------------
# Torso bones kept in the Head/Face rig for UE modular alignment (Step 8)
# Note: No "root" bone — pelvis is the top-level bone in ALS.
# ---------------------------------------------------------------------------
BASE_TORSO_BONES = [
    "pelvis", "spine_01", "spine_02", "spine_03",
    "clavicle_l", "clavicle_r", "neck_01", "head"
]
