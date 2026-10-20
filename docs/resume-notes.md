# Portfolio talking points

Suggested project description, grounded in the extracted source:

> Built a visual-attention prediction service for interface screenshots using FastAPI and PyTorch, with a ResNet-34/U-Net inference pipeline, image validation, cached model loading and request-level logging. Evaluated candidate models using saliency metrics and investigated service latency through load testing.

Use this wording only where it reflects your own contribution. Third-party architectures, datasets and baselines require their original attribution.

Safe discussion topics:

- Why a model-based prediction is different from real eye tracking or click analytics.
- How domain differences affect the interpretation of benchmark results.
- Why loading a model once saves initialization work and memory churn.
- How request latency grows under the recorded test stages, and what metadata is needed before interpreting a tuning gain.
- Why the final visualization blends a learned signal with a contrast heuristic.

Avoid numerical performance improvements, production-scale throughput claims, a claim that auxiliary OCR/face channels are implemented, or a claim that the archived model rows identify the current checkpoint. The surviving evidence does not establish those statements.
