# Swap the baked LLM for another model

The inference image ships with `llama3.2:1b` (Q4_K_M GGUF) baked in so airgapped clusters never touch a model registry. To serve a different model:

## 1. Point the Dockerfile at new weights

Edit `apps/inference/Dockerfile` — change the download URL to any GGUF hosted publicly (HuggingFace works well):

```dockerfile
&& curl -fL --retry 3 -o /tmp/model.gguf \
    "https://huggingface.co/<org>/<repo>/resolve/main/<model>.gguf"
```

Pick a **Q4_K_M** quant when available: smaller *and* higher fidelity than q4_0.

## 2. Keep the chat template honest

Bare-GGUF imports do **not** inherit a chat template in ollama 0.5.x. Update `TEMPLATE` and the `PARAMETER stop ...` lines in `apps/inference/Modelfile` to match your model family (llama3, phi3, qwen2 all differ). Wrong template = degenerate completions.

## 3. Rebuild and repackage

```bash
mise run build && mise run package
```

CI publishes multi-arch images on push to `main`; tags publish release bundles.

## 4. Mind the size cap

GitHub Release assets cap at **2 GiB** per file. CI enforces this — if your model pushes the bundle over, choose a smaller quant or split delivery.
