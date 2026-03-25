# Edge Cases - Model Serving

### 3.1. Model Version Mismatch
* **Scenario**: Serving layer uses a model incompatible with feature version.
* **Impact**: Incorrect ranking or runtime errors.
* **Solution**:
    * **Compatibility**: Enforce feature/model version pinning.
    * **Validation**: Pre-deploy checks before traffic shift.

### 3.2. Cold Cache in Vector DB
* **Scenario**: Vector index is cold after restart.
* **Impact**: High latency and timeouts.
* **Solution**:
    * **Warmup**: Preload popular items and embeddings.
    * **Fallback**: Serve cached recommendations temporarily.

### 3.3. Latency Spikes
* **Scenario**: Inference time exceeds SLA.
* **Impact**: API timeouts and poor UX.
* **Solution**:
    * **Optimization**: Batch inference, model quantization.
    * **Scaling**: Autoscale serving pods.