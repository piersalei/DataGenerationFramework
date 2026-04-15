# Pitfalls Research

## Domain-Specific Pitfalls

| Pitfall | Warning Signs | Prevention Strategy | Phase |
|---------|---------------|---------------------|-------|
| No canonical latent sample model | Each export format starts inventing its own fields and semantics | Define one normalized sample schema before exporter implementation | Phase 1 |
| Hidden-state modeling stays implicit in prompts | Beliefs, intentions, or motivations are not inspectable after generation | Make latent mental states explicit sampled fields, not only prompt prose | Phase 2 |
| Template diversity is fake diversity | Many outputs differ only lexically while reasoning pattern stays constant | Track template families, slot distributions, and near-duplicate clusters | Phase 2 and 4 |
| Provider-specific logic leaks into pipeline nodes | Local and remote generation paths behave differently and are hard to compare | Use one adapter interface and persist normalized request metadata | Phase 3 |
| QC relies only on one judge pass | Benchmark quality becomes unstable and hard to audit | Combine schema checks, heuristic rules, and optional score-based judging | Phase 4 |
| Human review is bolted on too late | Reviewers cannot trace why a sample exists or what stage failed | Build review queues and arbitration artifacts into the pipeline from the start | Phase 4 and 6 |
| MCQ exporter creates weak distractors | Multiple-choice accuracy becomes inflated and benchmark loses value | Add distractor strategy contracts and reject low-separation options | Phase 5 |
| Reproducibility stops at config files | Same config cannot actually replay because prompts, model ids, or seeds drift | Save run manifest with prompt version, model id, seed, and code revision | Phase 6 |
| Benchmark scope expands too early | Framework starts absorbing training, UI, and publication tooling | Keep v1 focused on data generation, QC, and export only | Phase 1 onward |

## Additional Notes

- Social-mind datasets are especially vulnerable to hidden leakage between narration and answer because mental-state labels are easy to accidentally reveal.
- Quality failures often look like "plausible text" rather than obvious structural errors, so audit artifacts matter.
- The strongest temptation will be to overfit the framework to one first benchmark. Guard against this by making task packs extensions over shared contracts.
