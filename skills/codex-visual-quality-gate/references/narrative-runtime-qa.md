# Narrative Runtime QA

Use this matrix for scroll-driven, pinned, horizontal, and WebGL scenes. The mechanical capture gate still applies. A scene signature is a pure function of scroll progress, the active chapter index, and chapter identity.

| Check | Pass condition | Failure |
| --- | --- | --- |
| Progress source | `progress = scrollY / (scrollHeight - innerHeight)` using the live viewport height | A cached `innerHeight` drifts when the mobile URL bar shows or hides |
| Chapter index | Flips at progress `0.39`, not `0.50`. Later handoffs use `threshold(i) = (i - 1 + 0.39) / (chapter_count - 1)` | The previous chapter stays current until the midpoint |
| Hidden chapters | `inert` is set, not only `opacity: 0` | Offscreen controls trap keyboard focus |
| Capture and programmatic jumps | `scroll-behavior: smooth` is disabled on `html` for the jump | The screenshot lands mid-transition |
| Navigation parity | Forward scroll, reverse scroll, direct anchor jump, and reload at depth share one scene signature | Direction or entry path changes the scene |
| Fast-skip | Skipping several scenes plays only the final transition | Intermediate scenes queue behind the skip |
| Reduced motion | A designed still frame is visible | A `0.01ms` animation of a hidden initial state |
| Scene cadence | Default dwell `1.15` screens, move `0.85` screens, track `(span + 1) * 100vh`, weight `0.7–1.8` viewport heights | An unearned pin, or a weight outside the band without a recorded exception |
| WebGL step | `dt <= 1/30s` | A resumed tab teleports the scene |
| Pixel ratio | `devicePixelRatio <= 2` | An uncapped ratio spends the frame on fill rate |
| Hidden document or offscreen canvas | Rendering is paused and `offscreen running animations == 0` | The scene keeps integrating when nobody can see it |
| 404 asset | Essential copy and controls remain; the image-load failure fallback is the designed one | A missing texture blanks the chapter or removes the action |
| Context loss | The designed fallback frame shows, and context restore does not trap the page on a blank canvas | The canvas stays empty after the GPU context drops |
| 200% zoom | No clipped controls, no horizontal overflow, and chapter targets remain reachable | Zoom pushes the action or the pinned heading off screen |
| Profiling | Ablate in order: lower DPR -> disable post-processing -> freeze shadows -> disable particles -> hide groups -> swap LOD -> replace materials | A material swap is tried while post-processing is still the cost |

Also confirm native scroll, sticky navigation clearance, and that a chapter indicator never moves keyboard focus. Pinned scenes must release. The reduced-motion static state has to tell the same story as the designed still frame.
