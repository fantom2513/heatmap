# Provenance

Extracted on 2026-10-20 from the local CX Copilot checkout, whose Git HEAD was `dede8f5` at inspection time.

- `src/`, original tests, dependency lists and pytest settings came from `services/ml-processor/` in the local working tree. They are not asserted to be byte-identical to Git HEAD. The initial Git commit preserves the inherited tests; the extraction then corrects their dependency overrides and expected exception. The obsolete `fastapi[test]` requirement is replaced with `httpx` with the owner's approval.
- Quality CSVs came from `services/ml-processor/bakeoff/results/`.
- Load CSVs came from `services/ml-processor/loadtest/results/`.
- The ignored local checkpoint came from `backend/models/websaliency_model.pth`.
- README, supporting documents, ignore rules and Docker packaging were created for this extraction.

The current source repository's Git tree does not include the inspected bakeoff/loadtest output paths. Their provenance is the local working copy, not committed experiment history.

`source-manifest.csv` records SHA-256 hashes of the copied Python files before test corrections. All 21 copied Python files matched their local sources at that checkpoint; subsequent test-only changes are visible in Git history. Application source remains unchanged.

Excluded: customer screenshots, the original screenshot example, private frontend components, application configuration, credentials, datasets, notebooks, vendor implementations and other model binaries. The parent application's history is not copied.

Names in evaluation tables identify compared models; their inclusion does not imply authorship of those models. The current service architecture has two extra input channels, but inference fills them with zeros. The rendered output mixes model saliency and contrast equally. Neither OCR nor face detection is performed by this inference path.

Before publication, establish permission to distribute the extracted source and aggregate results, select an appropriate license, and decide whether the checkpoint can be released. No license or checkpoint redistribution permission is inferred here.
