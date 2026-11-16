# Engine integration, preview and acceptance

## Division of responsibilities

```text
ActorRoot (authoritative game position, velocity, collision, hit state)
├── VisualPivot (only visual lean, scale, recoil offset)
│   └── Sprite / Skeleton / Model
├── ShadowAnchor (ground contact or projected ground point)
└── HitPoint / WeaponAttach / EffectAnchor
```

For 2D use the target engine's actual node/transform semantics; for 3D use equivalent bones/hierarchies. Only **one** system owns actual knockback and world position. Pose change should not reset ActorRoot after a hit. Root-driven animation can be supported if explicitly declared as the authority with collision handling and cancellation.

## Game events, not magic animation frames

1. Attack action begins and receives an attack-instance ID.
2. Active window opens by elapsed action time (e.g. 130–160 ms), not by exact rendering frame equality.
3. Collision/swept check identifies potential targets.
4. Combat system checks alignment, invulnerability, block, team and prior hits for the same segment.
5. A **confirmed hit result** supplies hit point, impulse, hit region, strength, target locomotion/support state.
6. Select context-sensitive reaction and update gameplay root when knockback is authorized; visual pose, sound and VFX follow that result.
7. Hitstop uses its own release clock; queued commands/cancel windows use explicitly chosen action or simulation clocks.
8. End/cancel/death cleans up active hitboxes, callbacks, queued events and visual offsets.

Multiple simultaneous hits on one target need an explicit priority or aggregation rule. Do not accumulate infinite stun, stack duplicate impact audio, or overwrite a later death with an earlier attack completion callback.

## Cocos Creator 3.x guidance

- 2D Sprite/AnimationClip for frame-by-frame with event or timeline synchronization; actual spritesheet slicing/anchors must be validated.
- For skeleton animations, read the Cocos/Spine runtime version and cache mode before applying track mixing. Cocos 3.8 Spine shared-cache mode is not suitable for arbitrary realtime animation mixing/layering.
- `AnimationState.pause/resume/speed` controls animation; **it does not automatically freeze custom movement, gameplay timers or physics**. Implement local clocks and state-specific pause policies.
- Attack events should originate from action time in a shared authoritative motion configuration; use animation events as signals but test frame skips and fast action.
- Mobile/multi-channel builds: test actual render scale, draw calls, texture limits, memory pressure, and representative number of simultaneous enemies.

Official reference: https://docs.cocos.com/creator/3.8/manual/en/animation/animation-event.html

## Unity / other engine guidance

- Use Animator/Timeline, Animation Events or an authoritative combat timeline; preserve the same action card semantics.
- 3D ragdoll/physics impulses should be blended intentionally with pose control. Avoid uncontrolled violent tumbling for every minor hit.
- Coordinate conventions and skeletal root motion differ between engines; adapters must translate units, time and event windows rather than rewriting design intent.
- Never claim a tested adapter exists until the relevant runtime and sample project have actually been exercised.

## Preview

When real sprite-sheet PNG and `action-card.json` exist, run:

```bash
python scripts/validate_motion.py output/action-card.json --check-assets
python scripts/preview.py output/action-card.json -o output/preview.html
```

The self-contained HTML embeds the selected sprite sheet as a data URI and renders frames according to the card durations. This is **visual preview only**, not authoritative hit collision, asset conversion, sound, or performance measurement. Its playback speed controls affect visual timing only. The preview must not reset or invent position/state; if the animation asset has no actual root-motion track, mark displacement as not visualized.

Prefer an inline browser/embedded visualization when available. When no host is available, provide a verified local file and openly state it is not a publicly hosted web URL. Do not make up preview URLs or claim to have run a browser test.

## Quality gates

| Gate | Minimum evidence | Fail cases |
| --- | --- | --- |
| G0 Source | Supplied actual source inspected, ID constraints documented | Assumed/unseen source presented as verified |
| G1 Motion design | Distinct gait/impact logic, force direction, poses, timing and phase diagram | Universal walk/backbend; identical head/abdomen/top reaction |
| G2 Asset fidelity | Per-frame identity and proportion audit; correct transparency, rig/anchors | Costume mutation, changed face/limb count, background baked |
| G3 Playback | Normal-speed playback, deliberate holds, readable hit response, clean loop/recovery, root consistency | Frozen idle or random motion, floating feet, teleport to idle |
| G4 Combat | Hit vs whiff vs block, impact point, lockouts, displacement, interrupts, repeat/death cases | Sprite shakes without gameplay knockback, duplicate damage, infinite hitstun |
| G5 Engine | Real import/running build, target FPS & crowd performance inspection | Preview-only animation claimed as engine-ready |

## Essential test matrix

- Grounded idle → walk, walk → attack, attack → idle/move, attack → block/whiff/hit.
- Grounded head front, head side, abdomen, overhead, leg, and blocked strike.
- Hop takeoff, midair, landing hit; hover hit; obstacle/wall near victim.
- Heavy vs light target and light vs heavy impact.
- Animation at slow and fast scaling; 30/60 FPS; long frame skip.
- Two hits in one frame, stagger on top of stagger, death during hitstop, pooled actor reuse.
- Reduced gameplay display size; target engine on device; high count of active enemies.

## Verification record

Deliver a report containing: character and action IDs; inputs; output paths and revisions; gates completed; observed motion errors (identity, posture, force, trajectory, loops); tested engine and version when available; scope of any missing assets; specific next correction. Unsupported checks must be marked `not_tested`, never `passed`.
