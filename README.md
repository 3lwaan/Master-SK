# MasterSK: Genesis 9 to ALS Pipeline

![Version](https://img.shields.io/badge/Version-4.0.0-blue.svg)
![Blender](https://img.shields.io/badge/Blender-4.0+-orange.svg)
![Unreal Engine](https://img.shields.io/badge/Unreal_Engine-5.0+-black.svg)

**MasterSK** is an automated, professional-grade rigging pipeline for Blender that seamlessly bridges high-fidelity Daz3D Genesis 9 characters with Unreal Engine 5's Advanced Locomotion System (ALS). 

## Why MasterSK?

Integrating Genesis 9 characters into Unreal Engine's ALS ecosystem has traditionally been a frustrating, multi-day manual process involving tedious vertex weight repainting, destructive bone renaming, and highly error-prone joint alignment. 

MasterSK eliminates this friction by providing a deterministic, 8-step programmatic pipeline. It guarantees 100% mechanical compatibility with the ALS Epic Mannequin while strictly preserving the integrity of the original Genesis 9 anatomical mesh weights and shapes.

---

## How It Works Under The Hood

MasterSK does not use heuristic guessing. It relies on exact mathematical transformations, direct matrix inversions, and rigid hierarchy replacements.

1. **Weight Consolidation:** Merges complex Genesis 9 driver bones, metacarpals, toes, and twists into their singular UE5 target equivalents (e.g., merging 10 independent toes into the single ALS `ball_l` / `ball_r` groups).
2. **Armature Pruning:** Strips the Genesis 9 armature down to the exact hierarchy required by ALS, preserving only the whitelist of essential bones.
3. **Vertex Group Mapping:** Renames the Genesis 9 bones and their corresponding mesh vertex groups simultaneously to perfectly match the ALS naming convention.
4. **Kinematic Pose Matching:** Solves a kinematic vector alignment to rotate the Genesis 9 bones to precisely match the ALS A-Pose limbs, and bakes this deformation (along with all facial Shape Keys) into the character mesh as the new default rest pose.
5. **Base Skeleton Injection:** Imports the true UE5 ALS Base Skeleton, dynamically scaling it to match the physical bounds of the Genesis 9 mesh without distorting proportions.
6. **Joint Snapping (Roll Lock):** Mathematically snaps the head pivots of the ALS joints to the Genesis 9 joint coordinates, while strictly preserving the original ALS local axes (Roll). This ensures the UE5 IK retargeter receives perfect mathematical data.
7. **Mesh Splitting & Morph Pruning:** Non-destructively separates the head/face mesh from the body mesh based on material keyword classification. It automatically merges internal materials (Mouth Cavity to Head), optimizes UVs, and executes a mathematical `numpy` shape key cleaner that instantly purges any morph targets that have zero geometric effect on the newly separated meshes (perfectly isolating ARKit keys to the Head and JCMs to the Body).
8. **Dual Rig Finalization:** Generates two distinct, production-ready output rigs (`root` for the body, `root_head` for the facial rig) tailored for modular UE5 construction. The Head Rig seamlessly integrates the spine, clavicles, upper arms, and the full uncompromised Daz3D facial skeleton, powered by a zero-length bone preservation safeguard.

---

## Installation

1. Download or clone this repository.
2. In Blender, navigate to **Edit** > **Preferences** > **Add-ons**.
3. Click **Install...** and select the `MasterSK.zip` file.
4. Enable the checkbox next to **Rigging: MasterSK Pipeline**.
5. Ensure the `als_base_skeleton.blend` asset file remains within the addon's `assets/` directory.

## Usage Guide

MasterSK is designed to be executed sequentially.

1. Open the **Sidebar (N)** in the 3D Viewport and locate the **MasterSK** tab.
2. Select your imported Genesis 9 Mesh. The addon will attempt to auto-detect its corresponding Armature.
3. Execute **Steps 1 through 4** in exact order. 
4. Execute **Step 5** to append the ALS Reference Skeleton.
5. Execute **Step 6** to mathematically snap the joints.
6. Execute **Step 7** to split the head and body meshes.
7. Execute **Step 8** to finalize the dual rigs.
   > **Note:** A prompt will appear reminding you to manually verify the Z-axis placement of the `spine_01`, `spine_02`, and `spine_03` bones in Edit Mode to ensure they visually match your preferred mesh weight envelopes before exporting.

## License
Proprietary. Developed for internal production pipelines.
