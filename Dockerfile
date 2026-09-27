# RunPod's own PyTorch base image already has CUDA + PyTorch set up correctly
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

# HF_TOKEN is needed because FLUX.1-dev is a gated model on Hugging Face.
# Pass it at build time so the image can be tested locally if you want:
#   docker build --build-arg HF_TOKEN=hf_xxx -t flux-endpoint .
# In production, set it as a RunPod endpoint environment variable/secret instead
# (see README) so your token never ends up baked into a pushed image.
ARG HF_TOKEN
ENV HF_TOKEN=${HF_TOKEN}

CMD ["python3", "-u", "handler.py"]
