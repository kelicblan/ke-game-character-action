# Host-native automatic image generation (mandatory)

## Intent

A user supplies a character design image and asks for idle, walk/hop/fly, attack, hit, or other multi-frame animations. **The invoking Agent must generate the assets, rather than stopping after advice, whenever image generation is actually accessible in the calling environment.** This Skill contains the orchestration instructions; the host must expose an image tool or a model with image-output capability.

The image-rendering model does not have to be the same as the language model interpreting this SKILL. **Use whichever image generation capability the current host actually exposes.** Do not guess a tool's name, hard-code a provider/API key, attempt unauthorized network access, or demand that the user install a separate model as the normal path.

## Capability discovery and dispatch

Before planning a "text-only" deliverable, determine at runtime:

1. **Native image output** — does the current model/runtime directly support making or editing images and saving or returning them? If yes, invoke that supported method.
2. **Available image-generation/edit tool** — can the calling Agent invoke an image tool exposed in its tool list? If yes, call it (for edits, pass the original reference or images as supported by the tool's actual interface).
3. **Alternative user-configured tool that is already enabled** — if native image generation is absent, use any available compatible image tool with permission and known input contract.
4. **No image capability** — do **not** pretend to have generated files. Produce action cards / prompts / task manifest, explain that rendering requires a tool-enabled host, and state what actually remains uncompleted.

Do not assume a text-only LLM can render image bytes simply because it is reading SKILL.md. The system's image tool belongs to the host, not to the SKILL Markdown file.

When the model or tool is accessible, **call it without asking the user to approve each frame** unless approval or additional inputs are actually required by that tool. Respect provider permissions, quotas, usage policies, and billing confirmations when mandatory. Never expose model API keys.

## Full automatic execution loop

Input: user-provided approved character reference(s), desired actions (explicit or reasonable defaults), target camera, intended engine and image size if known.

For each character:

### A. Analyze and lock identity

- Inspect actual source. Extract invariant shape/head/body proportions, face, hair/facial hair, eyes, silhouette, costume, prop counts, equipment orientation, palette, outline and shading.
- Determine physical motion constraints: joints, mass, stiffness, actual support/gait (steps/hop/fly), current velocity, and root contact.
- Write a per-character **identity lock** + **negative constraints** (e.g., do not add a beard, no extra accessories/legs, no change of camera or gender).
- If the source is inaccessible, explicitly record the limitation. Do not claim identity fidelity.

### B. Plan action poses and timings

- Use the action-card timeline in milliseconds, not a hard-coded eight-frame requirement.
- Idle: subtle movement; walk: ground contacts; hop: takeoff/flight/landing; fly: sustained airborne balance.
- Attack: anticipation, release, readable key contact pose, pose hold, recovery/next legal action.
- Hits: body part + incoming/impulse direction + intensity + ground/air/hover phase; distinguish head, abdomen and overhead; model displacement if gameplay authorizes it.
- Decide how many unique visual poses are actually necessary and their sampling intervals. Repeated identical frames may implement holds without redundant image calls.

### C. Generate with the current tool

- **Actually invoke** the available image generator with the original reference on the first pass, plus explicit identity lock, perspective, camera, action ID, pose description and forbidden mutations.
- Prefer reference-image editing / consistent-character modes if supported; never claim those capabilities if the tool lacks them.
- For generators supporting multi-frame grids or animation: request a **uniformly sized** grid of coherent poses or a short animation; keep characters completely within each cell, with no frame numbers/captions/borders. A rendered GIF is a **preview** unless its individual frames and timings are extracted as actual assets.
- When generating separate images, give each pose an explicit action pose index and reuse the same original anchor image. Avoid independent free-form generations that drift into different character faces.
- Generate the essential key poses first; inspect consistency. Then request only missing intermediates/transitions or do a controlled local animation/rig tween if it is supported and visually legitimate.
- Use transparent background when supported. If a white background or fake checkerboard is baked into image pixels, do not label it as transparent; remove/repair it with available editing tools or mark the gate incomplete.
- Keep all generated media in the user's target project/output, **never** this public SKILL repository.

### D. Validate and repair

For each candidate frame, compare with source and neighbors:
- Visual ID: eyes, hat, beard presence/absence, garment details, ornament counts, limb topology and proportions.
- Pose: weight support and intended force direction, significant motion vs frames that repeat with no effective change.
- Production: alpha, cropping/trim offsets, fixed logical canvas/pivot, foot contact, consistent scale, sharpness at game display size.

If the image is inconsistent or wrong, reject the bad frame. **First try editing/regenerating only that pose with source anchor and stronger pose-specific instructions**; if the tool can only regenerate the whole grid, rerender and re-evaluate the group. Do not splice visually inconsistent results into a "finished" sheet.

A reasonable default is up to two refinement passes for each failing set, subject to available compute/quotas; on persistent failure, stop and report the failed identity/physics constraint rather than silently substituting the wrong action.

### E. Assemble and preview

- Make real frame PNGs with consistent logical size and feet/pivot registration or a legitimate skeletal/rig animation where supported.
- Assemble a sprite sheet at documented `columns` × `rows`, equal frame cell sizes, and exact frame order. Use a single transparent channel only when alpha is real.
- Produce an action-card JSON defining `total_ms`, `frame_durations_ms`, phases, event windows, loop flag and visual path; document impact and gameplay root motion separately.
- Use the packaged validator and preview scripts **when the actual files exist**. A layout of separate unrelated images is not by itself an animation.
- Prefer an **in-chat/online interactive animation preview** if the current interface supports it. Never pretend a local HTML file is a public hosted URL.
- For engine-specific claims, import and test into the actual engine; do not infer integration from a GIF.

### F. Report honestly

Return real images/links or previews only after verifying their existence; list:
- images and animation files created, selected generator/tool (if known), and exact actions generated;
- passed/failed identity and motion checks, refinement count and remaining defects;
- whether an in-chat preview exists, whether engine integration was actually tested, and the current QA gate.

If the host has image-generation output but no filesystem/export/cropping functions, **generate the images anyway** and offer visual previews; mark extraction, assembly or engine-ready packaging as pending. Do not redefine images-as-preview as PNG sprite assets without extraction.

## Reusable prompt contract

Pass the following concepts to the actual image tool, adapting syntax to the tool's interface; do **not** print tool arguments as user-visible content:

```text
Character anchor: [the actual user-supplied image reference]
Immutable design: [observed facial details, head/body proportions, wardrobe, accessories, colors, line style]
Action ID: [idle/hop/attack/hit_head_front/hit_abdomen/...]
View: [fixed camera, character facing, position]
Pose sequence: [one sentence per actual distinct pose with momentum/support]
Timing: [ms per pose, emphasis / pose hold / landing]
Environment: [transparent background if supported, no text, no borders]
Negative constraints: [no new limbs, no extra hair or facial hair, no swapped accessories, no pose duplicates]
Required output: [actual full-body frames or uniform storyboard grid / animation preview]
```

## Failure policy

- Missing/disabled image tool: report blocker clearly. Do not insist a provider API integration is mandatory.
- Output image generation succeeded but character mutated: do a targeted repair, or mark G2 failed.
- Frames look good but are missing alpha/anchors/timing: asset draft only, not engine-ready.
- Animation has recoil only with no authorized root displacement: explain that engine gameplay integration is still required.
- If the user requested only a **design/specification**, do not generate images gratuitously. The automatic generation requirement applies to requests for frames/images/animations or actual motion assets.
