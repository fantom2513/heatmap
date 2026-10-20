# Checkpoint

The service expects `models/websaliency_model.pth`, loaded as the state dictionary of `WebSaliencyUNet(in_channels=5)`.

The local extraction contains the existing checkpoint copied from the parent application's `backend/models/`. Model binaries are ignored by Git and excluded from the Docker image; mount this directory at `/app/models`.

No public checkpoint download is currently configured. A fresh clone cannot perform inference until a compatible checkpoint is supplied. Do not substitute `sum_model.pth`: it is not the architecture loaded by this service.

Distribution rights and training-data provenance must be checked before publishing weights as a release asset. Training and checkpoint creation are not reproducible from this extraction alone.
