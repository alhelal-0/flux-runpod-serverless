import os
import base64
from io import BytesIO

import torch
from diffusers import FluxPipeline
import runpod

MODEL_ID = "black-forest-labs/FLUX.1-dev"

# --- Cold start: model loads once per worker, then stays warm in memory ---
print("Loading FLUX.1-dev pipeline (this can take a few minutes on cold start)...")
pipe = FluxPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    token=os.environ.get("HF_TOKEN"),  # FLUX.1-dev is a gated model on Hugging Face
)
# Offloads parts of the model to CPU when idle - lets FLUX run on GPUs with less VRAM
# (comment this out if you're on an 80GB GPU and want max speed instead)
pipe.enable_model_cpu_offload()
print("Model loaded. Worker is ready.")


def handler(event):
    """
    RunPod serverless entrypoint.

    Expected event["input"]:
      {
        "prompt": "a photo of an astronaut riding a horse on mars",  # required
        "height": 1024,             # optional, default 1024
        "width": 1024,              # optional, default 1024
        "guidance_scale": 3.5,      # optional, default 3.5
        "num_inference_steps": 28,  # optional, default 28
        "seed": 0                   # optional, default 0
      }

    Returns:
      { "image_base64": "<png bytes as base64 string>" }
      or
      { "error": "<message>" }
    """
    job_input = event.get("input", {}) or {}

    prompt = job_input.get("prompt")
    if not prompt:
        return {"error": "Missing required field: 'prompt'"}

    height = int(job_input.get("height", 1024))
    width = int(job_input.get("width", 1024))
    guidance_scale = float(job_input.get("guidance_scale", 3.5))
    num_inference_steps = int(job_input.get("num_inference_steps", 28))
    seed = int(job_input.get("seed", 0))

    try:
        generator = torch.Generator("cpu").manual_seed(seed)

        image = pipe(
            prompt=prompt,
            height=height,
            width=width,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            generator=generator,
        ).images[0]

        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        return {"image_base64": img_base64}

    except Exception as e:
        return {"error": str(e)}


runpod.serverless.start({"handler": handler})
