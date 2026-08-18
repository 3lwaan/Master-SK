# Changelog

All notable changes to the **Master SK** Blender addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.1.0] - 2026-08-18

### Added
- **Automated Nails UV Transformation (UDIM 1004 / Arms Layout)**:
  - Injected hardcoded UV coordinate mapping (`g9_nails_uv_reference.json`) covering all 1,592 Genesis 9 fingernail and toenail polygons.
  - Repositions nail UV islands into the open central negative space between the upper and lower arm islands in UDIM Tile 1004.
- **Nails UV Extraction Diagnostic**:
  - Added internal utilities to inspect and extract per-loop UV coordinates from reference Genesis 9 meshes.
- **Changelog Tracking**:
  - Initialized `CHANGELOG.md` to document feature updates, fixes, and workflow improvements.

### Changed
- **Step 4 (Mesh Separation & Material Consolidation)**:
  - Updated `consolidate_pre_split_materials` to execute `apply_hardcoded_nails_uv_layout` prior to reassigning polygon material indices.
  - Automatically moves fingernails and toenails into the Arms UV space and merges `Fingernails` / `Toenails` material slots into the `Arms` slot, eliminating empty slots and texture collisions.
  - Added dedicated audit log feedback in the 3D Viewport sidebar panel for UV repositioning.
- **Build System (`build_addon.bat`)**:
  - Added packaging support for `g9_nails_uv_reference.json` and `CHANGELOG.md` into `master_sk_tools.zip`.

---

## [2.0.0] - 2026-08-01

### Added
- **Full Blender 4.4+ Compatibility**:
  - Support for Blender 4.4 un-grouped bone collection architecture (`purge_all_bone_collections`).
- **Anatomical Gender Variant System**:
  - *Male Setup*: Removes pectoral & glute deformers, normalizes remaining torso weights.
  - *Female Setup*: Injects scale-proportional `glute_l` / `glute_r` bones (-15° pitch, posterior cosine falloff, Laplacian edge smoothing) and preserves `pectoral_l` / `pectoral_r`.
- **UE5 / ALS IK Bones Injection**:
  - Injects `ik_foot_root`, `ik_foot_l/r`, `ik_hand_root`, `ik_hand_gun`, `ik_hand_l/r`.
- **Modular Head & Body Rig Separation**:
  - Separates mesh into `SKM_Head_Mesh` and `SKM_Body_Mesh`.
  - Creates independent, single-user datablocks for `SKM_Face_Rig` and `SKM_Body_Rig`.
  - Purges 100% of body shape keys (~90% FBX file size reduction) while retaining ARKit, Viseme, and expression morphs on the head.
- **Weight Transfer & Sync**:
  - Merges 20 individual child toe weights into `toes_l/r`.
  - Merges 8 metacarpal weights into `hand_l/r`.
  - Merges metatarsal weights into `foot_l/r`.
  - Merges `hip` weights into `pelvis`.
- **Driver & Constraint Remapping**:
  - Automatically updates driver variable subtargets and expressions when bones are renamed.
- **Material Slot Optimization**:
  - Merges `Teeth` -> `Mouth`, `EyeMoisture` -> `Eyes`, `Mouth Cavity` -> `Head`.
- **Pipeline Audit Checklist**:
  - Real-time timestamped event log inside the View3D sidebar panel.

---

## [1.0.0] - Initial Release

- Basic bone mapping from DAZ Genesis 9 to standard UE5 mannequin naming.
- Single armature hierarchy restructuring.
