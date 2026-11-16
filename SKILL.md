---
name: ke-game-character-action
description: Design, generate, validate, and deliver consistent game-character animations from an approved character reference or rig. Use for idle, walk, run, hop, fly, attack, hit reactions, knockback, knockdown, recovery, death, sprite sheets, 2D skeletal motion, 3D animation, action timing, combat events, and engine-ready previews. Requires character-specific movement and body-part/direction-aware impact design; never treat a generic GIF as a finished game asset.
license: MIT
metadata:
  author: kelicblan
  version: "1.0.0"
---

# Game Character Action — independent animation skill

You turn a character reference (image, layered file, rig, description, or existing game asset) into **credible, character-specific, testable game animation**. This skill is self-contained. Do not assume any other skill, repository, art style, monster type, engine, or model.

## Operating contract

1. **Inspect the actual supplied source** before designing poses. If no source is accessible, mark identity constraints as unverified; do not invent unseen details.
2. **Character first, animation second.** Establish anatomy, apparent mass, flexibility, locomotion/support, equipment, view, and emotional/behavioral traits before choosing motion.
3. **Physics-informed, game-readable reactions.** Impact motion must follow the hit part, force vector, strength, grounded/airborne/hovering state, collision constraints, and the character's characteristic stiffness. Avoid a universal bend/back-lean animation.
4. **Separate intent, visual pose, and gameplay.** Animation poses do not themselves prove collision, displacement, stagger, invulnerability, or engine integration.
5. **Respect the user's current reference as authority.** Preserve identity, proportions, features, costume, attachments, limb count, palette, and handedness. Do not silently add facial hair, change eyes, duplicate accessories, or alter the pose's intended facing.
6. **Do not equate frames with timing.** Set timings in milliseconds, author distinct pose holds, hitstop, hitstun, recovery locks, cancel windows, and root motion. Eight equal frames are not a default.
7. **Preview honestly.** Label outputs as concept, motion draft, asset draft, or engine-verified. A montage, GIF, fake loop, or single image is not an engine-ready sprite sheet or skeleton.
8. **Keep source skill clean.** All user art, generated frames, sprite sheets, GIFs, videos, models, build outputs, and private assets belong in the target game workspace, **never in this skill repository**.

## When triggered

Use on requests to animate characters, design movement personality, create action frames, study hit reactions, build a motion library, export game animation, or fix unnatural idle/walk/attack/hit feedback. Support 2D frame animation, 2D cutout/skeletal animation, hybrid 2D, and 3D rigs. Choose an approach justified by required silhouette change and available tools.

## Workflow

### 1. Establish input and deliverable
- Determine available image/rig/source, requested actions and directions, 2D or 3D representation, approximate scale, game camera, engine, performance target, and whether deliverable is **design**, **preview**, **animation assets**, or **running game integration**.
- Proceed with safe defaults when details are missing; explicitly list assumptions. Do not ask unnecessary questions once a task is clear.
- Record source provenance and limitations. If tooling is missing, produce implementable specs; do not claim assets or engine verification.

### 2. Analyze character biomechanics and identity
Read [references/character-and-motion.md](references/character-and-motion.md).
- Character motion profile: silhouette/proportion, joint degrees of freedom, mass distribution, center of mass/support, gait class (ground step, heavy shuffle, dual-foot hop, crawl, flight/hover), garment inertia, carried props.
- Write **motion personality** distinct from visual style: e.g. quick/light/hopping vs heavy/stiff/anchored. Avoid anthropomorphic gait for creatures whose structure rules it out.
- Identify what must remain unchanged between frames and what may deform.

### 3. Design actions with explicit timing
Read [references/timing-and-states.md](references/timing-and-states.md).
- Author one action card per animation: use `templates/action-card.json` as a starting point.
- Idle: small motion, low amplitude, loop seam. Do not add steps, large breathing, or exaggerated swaying unless the character supports them.
- Locomotion: foot contacts, airborne arcs, propulsion, landing, or hover; maintain coherent root travel and floor/shadow.
- Attack: anticipation → acceleration → active contact → follow-through → optional pose hold → recovery/transition. Whiff, hit, block, and combo are separate branches.
- Reactions: choose from the context matrix before authoring poses, rather than generating six near-identical backbends.
- Do not demand exactly eight key poses. Sample at the timestamps necessary to communicate force; visual frame count and gameplay timing are independent.

### 4. Select realistic hit-response behavior
Read [references/hit-reaction-system.md](references/hit-reaction-system.md) **for every hit animation request**.
- Input: hit location, incoming/impulse direction, intensity, locomotion phase, grounded/airborne/hovering state, mass/stagger resistance, existing velocity, walls/platforms.
- Head front strike: head reacts first, upper body and support follow; a compensating step is conditional on imbalance, not universal.
- Abdomen front strike: torso contracts/flexes with knees/support response; avoid reflexive head-recoil pose.
- Top-down strike: compression through head/neck/shoulders/knees; avoid translating the whole image down without joint deformation.
- Airborne hit: preserve or modify current trajectory under impulse and resolve into valid landing/hover recovery; do **not** teleport to idle or impose a second jump.
- Direction and severity change pose **and** game position when authorized. Separate cosmetic flinch from stagger/knockback.
- `templates/hit-reaction.json` is an illustrative decision entry, not a universal physical law.

### 5. Build coherent source assets and animation
Read [references/production-and-consistency.md](references/production-and-consistency.md).
- Choose frame-by-frame, cutout/skeletal, hybrid, or 3D according to motion requirements.
- Create character identity sheet, key poses, intermediate motion, transparent/correctly anchored sprites or rig, contacts/offsets, and secondary motion. Reveal/paint occluded body parts before deforming a static drawing.
- Keep ground registration and roots consistent. No hidden spatial changes from frame resizing or inconsistent cropping.
- Verify identity **frame-by-frame**; generated images are candidates, not automatically approved frames. Discard incorrect frames, do not stitch inconsistent characters into an animation.
- If using image generation, generate a small pose set and compare with source before creating dozens of variants.

### 6. Package, preview, and integrate
Read [references/integration-and-qa.md](references/integration-and-qa.md).
- Keep the logical actor root (game position/collision) distinct from the visual pivot and skeletal/sprite pose. Define one owner for actual displacement.
- Map attack windows to real combat hit results; prevent duplicate hit events and race conditions on interrupt/death.
- For sprite sheets, document frame dimensions, layout, per-frame durations, pivot, trim/offset, direction, loop policy, and events.
- For skeletal rigs, document runtime version, bones/slots/skins, track blending requirements, and events.
- Prefer an **inline live preview** when tools support it; otherwise produce a self-contained local preview and state its limitation. Never invent a hosted link.
- Use `python scripts/validate_motion.py <action-card.json> [--check-assets]` to check metadata and optional media existence.
- If a sprite sheet exists, use `python scripts/preview.py <action-card.json> -o preview.html` for an adjustable offline browser preview.
- Do not claim engine testing unless the target project actually imported and ran the asset.

### 7. QA gates and reporting
Check the [references/integration-and-qa.md](references/integration-and-qa.md) gate list.
- **G0 input**: source/view/identity/rig limits grounded.
- **G1 design**: body mechanics, intended direction, gait, support, hit contexts, key poses, timing verified in storyboard.
- **G2 visual**: source identity and anatomy consistent in every frame; alpha/background, anchors, accessories, seams checked.
- **G3 motion**: normal-speed playback; movement/impact/hold/recovery readable; loops seamless; root motion matches trajectory.
- **G4 gameplay**: hit/whiff/block, hitstop, hitstun, displacements, interruptions, repeated hits and death behave correctly.
- **G5 engine**: real import, target framerate, memory, batching, collisions, platform testing recorded.
- Stop at the highest **actually verified** gate and state what failed. Provide actionable revision notes, not an unqualified “done.”

## Delivery format

Return a concise summary with: character profile, action list and movement rationale; action cards/time ranges; hit-reaction matrix if relevant; actual exported files and preview links **only when they exist**; verification gate, measured limitations, and next validation step. Preserve editable sources where possible.

## References, tools, and templates

| Resource | Load when |
| --- | --- |
| `references/character-and-motion.md` | Designing any animation |
| `references/timing-and-states.md` | Actions, loops, combos, timing |
| `references/hit-reaction-system.md` | Any impact or stagger task |
| `references/production-and-consistency.md` | Image/rig production, AI-generated frames |
| `references/integration-and-qa.md` | Export, preview, engine, QA |
| `templates/character-profile.json` | New character |
| `templates/action-card.json` | New action/timeline |
| `templates/hit-reaction.json` | New contextual hit response |
| `scripts/validate_motion.py` | Validate action-card format |
| `scripts/preview.py` | Preview real sprite sheets |
