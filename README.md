#  Master SK - Automated DAZ Genesis 9 to UE5 / ALS Pipeline for Blender

<div align="center">

![Master SK Banner](https://img.shields.io/badge/Blender-4.4%2B-orange?style=for-the-badge&logo=blender&logoColor=white)
![Unreal Engine](https://img.shields.io/badge/Unreal_Engine-UE5.0%2B-blue?style=for-the-badge&logo=unrealengine&logoColor=white)
![DAZ Genesis 9](https://img.shields.io/badge/Character-DAZ_Genesis_9-purple?style=for-the-badge)
![License](https://img.shields.io/badge/License-GPL_v3-green?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-v2.1.0-brightgreen?style=for-the-badge)

### *Streamline your DAZ G9 character workflow inside Blender and prepare game-ready modular rigs for Unreal Engine 5 & Advanced Locomotion System (ALS) in seconds.*

---

</div>

##  Why Master SK?

Importing **DAZ Genesis 9** characters into **Unreal Engine 5** or **Advanced Locomotion System (ALS)** manually is notoriously frustrating and time-consuming:

- ❌ **Bloated FBX Files**: Unused morph targets and body shape keys inflate FBX file sizes from ~25MB to over **250MB**, causing massive memory overhead.
- ❌ **Missing IK Bones**: UE5 and ALS require specific IK bones (`ik_foot_root`, `ik_hand_gun`, etc.) that DAZ rigs lack out of the box.
- ❌ **Deformation & Weight Issues**: Secondary gender deformations (Pectoral & Glute dynamics) are missing or result in terrible weight paint bleeding.
- ❌ **Shared Datablock Conflicts**: Splitting head and body armatures manually in Blender often leaves shared edit-bone data blocks, corrupting skeletal transforms upon export.
- ❌ **Fragmented Material Slots & UV Islands**: Separate material slots for fingernails, toenails, mouth cavity, and teeth waste draw calls and require tedious manual UV repacking.

**Master SK** solves all of these issues with a clean, 5-step automated panel inside Blender!

---

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **UE5 & ALS Hierarchy Sync** | Automates bone renaming (`hip` -> `pelvis`), hierarchy restructuring, driver target updates, and clears pelvic constraints for full ALS translation. |
| **Anatomical Gender Variants** | Injects scale-proportional `glute_l` / `glute_r` and `pectoral_l` / `pectoral_r` secondary deformers with topology-aware Laplacian weight paint. |
| **Automated IK Bone Injection** | Injects 6 essential UE5 IK bones (`ik_foot_root`, `ik_foot_l`, `ik_foot_r`, `ik_hand_root`, `ik_hand_gun`, `ik_hand_l`, `ik_hand_r`). |
| **Modular Head & Body Split** | Splits meshes into `SKM_Head_Mesh` and `SKM_Body_Mesh`, generates decoupled armatures (`SKM_Face_Rig` & `SKM_Body_Rig`), and purges unused body morphs (~90% file size reduction). |
| **Nails UV Repositioning & Slot Merge** | Automatically repositions all 1,592 fingernail & toenail UV loops into the central channel of the **Arms** UV map (UDIM Tile 1004) without texture overlap, merging slots cleanly. |
| **Material Slot Consolidation** | Merges duplicate materials (Teeth -> Mouth, Nails -> Arms, EyeMoisture -> Eyes, Mouth Cavity -> Head) to optimize draw calls for game engine export. |

---

## 📦 Installation & Building

### 🛠️ Building from Source (GitHub)
If you cloned this repository from GitHub:
1. Double-click **`build_addon.bat`** (or run `.\build_addon.bat` in Terminal).
2. The script automatically packages all necessary source files into **`master_sk_tools.zip`**.

### 🔌 Installing in Blender
1. Open Blender 4.4+.
2. Navigate to **`Edit > Preferences > Add-ons`**.
3. Click the top-right **`Install...`** button and select `master_sk_tools.zip`.
4. Enable **`Master SK`** in the addon list.
5. Open the 3D Viewport sidebar (`N` key) and find the **`Master SK`** tab.

---

## 🛠️ Step-by-Step Workflow Guide

```
 [1. Prepare Character] ──> [Gender Setup (Male/Female)] ──> [2. Rig & Weight Sync]
                                                                     │
 [5. Join Facial Meshes] <── [4. Modular Head/Body Split] <── [3. Inject IK Bones]
```

###  Step 1️⃣: Prepare Character
- Select your imported DAZ Genesis 9 character armature and mesh.
- Click **`1. Prepare Active Character`**.
- *What it does*: Validates selection, applies location/rotation/scale transforms to 1.0, and initializes object references.

### ♀️ Gender Variant Setup (Male / Female)
- **Set Up Male Variant**: Deletes pectoral and glute bones & vertex groups, rebalancing remaining weights to the torso.
- **Set Up Female Variant**:
  - Injects `glute_l` and `glute_r` bones parented to `pelvis`.
  - Positions bone heads over buttock cheeks with scale-invariant sizing (`hip_width * 0.42`).
  - Sets exact -15° downward pitch and symmetrical left/right mirror alignment.
  - Applies Laplacian topology-aware weight painting for smooth, natural deformation.

###  Step 2️⃣: Rig & Weight Sync
- Click **`2. Process Rig & Vertex Groups`**.
- *What it does*: Renames armature object and datablock to `root`, clears pelvic constraints, maps DAZ bones to `MASTER_SK_HIERARCHY`, merges toe/metacarpal/metatarsal weights, and updates driver subtarget references.

###  Step 3️⃣: Inject IK Bones
- Click **`3. Inject IK Bones`**.
- *What it does*: Injects all 6 UE5/ALS IK bones (`ik_foot_root`, `ik_foot_l/r`, `ik_hand_root`, `ik_hand_gun`, `ik_hand_l/r`) with accurate bone tail lengths and parent relationships.

###  Step 4️⃣: Modular Head & Body Split (with Nails UV Transform)
- Click **`4. Separate Head & Modularize`**.
- *What it does*:
  - **Nails UV Transform**: Automatically moves all 1,592 fingernail & toenail UV coordinates into the central channel of **UDIM Tile 1004 (Arms map)**.
  - **Material Consolidation**: Merges `Fingernails` & `Toenails` -> `Arms`, `Mouth Cavity` -> `Head`, and deletes empty slots.
  - **Mesh & Rig Decoupling**: Splits `SKM_Head_Mesh` and `SKM_Body_Mesh` and creates single-user datablocks for `SKM_Body_Rig` and `SKM_Face_Rig`.
  - **Shape Key & Driver Optimization**: Purges unused body shape keys (~90% file size reduction) and drivers while preserving ARKit/Viseme facial morphs on the head.

###  Step 5️⃣: Join Facial Meshes & Materials
- Click **`5. Join Facial Meshes & Materials`**.
- *What it does*: Standardizes UV map names (`UVMap`), joins eyes/eyelashes/mouth to the head mesh, consolidates material slots (Teeth -> Mouth, EyeMoisture -> Eyes), and performs a final audit.

---

## 📜 Changelog
See [CHANGELOG.md](CHANGELOG.md) for detailed version history and updates.
