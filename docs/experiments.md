# Experimental evidence

These CSVs are copied historical outputs, not freshly executed experiments. Higher CC, NSS and AUC Judd and lower KLDiv are the intended directions of the named metrics. Exact metric implementations are absent.

## Model comparisons

`benchmarks/quality/results.csv` contains seven model rows. The dataset/split and full evaluation protocol are not recorded in that file. It must not be used to claim general superiority of a model.

`benchmarks/quality/ueyes_results.csv` explicitly records training-domain differences:

| Model | CC | NSS | KLDiv | AUC Judd | Recorded training relationship |
|---|---:|---:|---:|---:|---|
| ensemble_sum_umsi | 0.8100 | 1.9968 | 0.4637 | 0.8690 | Both members trained on UEyes |
| sum | 0.7839 | 1.9086 | 0.4858 | 0.8602 | Trained on UEyes |
| umsi_pp | 0.7436 | 1.8540 | 0.5571 | 0.8591 | Trained on UEyes |
| ours | 0.6563 | 1.5738 | 0.7128 | 0.8292 | Trained on UEyes Train |
| transalnet | 0.4193 | 1.0100 | 1.1621 | 0.7480 | Recorded as away (fair) |
| legacy_zeros | 0.4030 | 1.0187 | 1.1318 | 0.7503 | Recorded as away (fair) |

The label `ours` belongs to the archived experiment and has not been matched to a checkpoint hash. Do not attribute these metrics directly to the bundled local checkpoint. Shared training domains do not establish test leakage, but they do prevent treating this table as a controlled comparison of generalization.

`ueyes_bycat_cc.csv` preserves category-level output. Dataset images and vendor model trees are omitted.

## Load testing

Values below come from the `/api/heatmap` rows of the archived CSVs. Response times are in milliseconds in the source tables and converted to seconds here. Stage labels are retained as filenames; they are not verified concurrency settings.

| Archive | Requests | Failures | Mean latency, s | Requests/s |
|---|---:|---:|---:|---:|
| stage_1 | 14 | 0 | 12.50 | 0.080 |
| stage_2 | 22 | 0 | 15.56 | 0.126 |
| stage_4 | 36 | 0 | 24.61 | 0.161 |
| stage_4_t2 | 43 | 0 | 21.06 | 0.187 |
| stage_8 | 50 | 0 | 44.41 | 0.167 |
| stage_8_t2 | 56 | 0 | 39.79 | 0.192 |

`stage_test_stats.csv` is also retained but has no `/api/heatmap` row. These small historical runs show increasing latency across stages; they do not demonstrate production capacity or a causal optimization gain. Hardware, input mix, warm-up, worker/thread settings and runner scripts are missing.

## Reproduction requirements

Before making a reproducibility claim, recover the original runners, exact model checkpoints, permitted dataset and splits, preprocessing and metric definitions, dependency versions, hardware and thread settings. Run quality evaluation and load tests afresh and store the commands and environment alongside results.
