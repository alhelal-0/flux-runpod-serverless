# FLUX.1-dev on RunPod Serverless — text-to-image endpoint

This deploys `black-forest-labs/FLUX.1-dev` (a free, open-weights model) behind a
RunPod serverless endpoint that takes a text prompt and returns a generated image.

## Files
- `handler.py` — loads the model once, then generates an image per request
- `Dockerfile` — builds the worker image on top of RunPod's PyTorch base image
- `requirements.txt` — Python dependencies
- `test_input.json` — sample payload for RunPod's built-in "Test" tab
- `test_client.py` — calls your live endpoint from your own machine and saves the image

## Before you start
FLUX.1-dev is **gated** on Hugging Face — you must:
1. Visit https://huggingface.co/black-forest-labs/FLUX.1-dev and accept the license.
2. Create a Hugging Face access token: https://huggingface.co/settings/tokens
   (read access is enough).

It's also a large model — plan for a GPU with **at least 24 GB VRAM** (RunPod's
A6000, L40S or A100 tiers all work). `enable_model_cpu_offload()` in `handler.py`
is there to help it fit on smaller cards, at some cost to speed.

## 1. Build and push the Docker image
```bash
docker build -t <your-dockerhub-username>/flux-endpoint:latest .
docker push <your-dockerhub-username>/flux-endpoint:latest
```
(Any registry works — Docker Hub is just the easiest to set up.)

## 2. Create the serverless endpoint on RunPod
1. Log in to RunPod → **Serverless** → **New Endpoint**.
2. Container image: `<your-dockerhub-username>/flux-endpoint:latest`
3. GPU: pick a 24GB+ card (A6000 / L40S / A100).
4. Environment variables: add `HF_TOKEN` = your Hugging Face token (mark it as a secret).
5. Container disk: 30GB+ (model weights are large).
6. Deploy.

## 3. Test it
**Option A — RunPod's web UI:** open the endpoint's "Requests" tab and paste the
contents of `test_input.json` into the test box, then run it.

**Option B — from your machine:**
```bash
export RUNPOD_API_KEY="your_runpod_api_key"      # RunPod → Settings → API Keys
export RUNPOD_ENDPOINT_ID="your_endpoint_id"     # shown on the endpoint's page
python test_client.py "a photo of an astronaut riding a horse on mars"
```
This saves the generated image as `output.png` in your working directory — that
image plus the code here is your deliverable for the case study.

## Notes for the write-up
- The handler expects `{"input": {"prompt": "..."}}` and returns
  `{"image_base64": "..."}`; decode that base64 string to get a PNG.
- Optional input fields: `height`, `width`, `guidance_scale`, `num_inference_steps`, `seed`.
- Cold starts are slow (model load + weight download if not baked into the image);
  once a worker is warm, generation itself typically takes 15-30 seconds on a
  24-48GB GPU at the default settings.
- If your RunPod credits are limited, swapping `MODEL_ID` in `handler.py` for a
  lighter model (e.g. `stabilityai/sdxl-turbo`, which needs far less VRAM and time
  per image) will still satisfy the assignment's requirements while being cheaper
  to test — just say so in your write-up if you go that route.
