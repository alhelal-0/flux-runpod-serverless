"""
Calls your deployed RunPod serverless endpoint and saves the generated image.

Usage:
    export RUNPOD_API_KEY="your_runpod_api_key"
    export RUNPOD_ENDPOINT_ID="your_endpoint_id"
    python test_client.py "a photo of an astronaut riding a horse on mars"
"""
import os
import sys
import time
import base64
import requests

API_KEY = os.environ["RUNPOD_API_KEY"]
ENDPOINT_ID = os.environ["RUNPOD_ENDPOINT_ID"]
BASE_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}


def generate(prompt: str, out_path: str = "output.png"):
    payload = {"input": {"prompt": prompt}}

    # /runsync waits for the result (good for testing); for long jobs use /run + poll /status
    resp = requests.post(f"{BASE_URL}/runsync", json=payload, headers=HEADERS, timeout=600)
    resp.raise_for_status()
    result = resp.json()

    # If the endpoint was still cold/queued, /runsync can return IN_QUEUE - poll /status instead
    if result.get("status") not in ("COMPLETED", "FAILED"):
        job_id = result["id"]
        while True:
            time.sleep(3)
            status_resp = requests.get(f"{BASE_URL}/status/{job_id}", headers=HEADERS)
            result = status_resp.json()
            print("status:", result.get("status"))
            if result.get("status") in ("COMPLETED", "FAILED"):
                break

    if result.get("status") == "FAILED" or "error" in result.get("output", {}):
        print("Generation failed:", result)
        return

    img_base64 = result["output"]["image_base64"]
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(img_base64))
    print(f"Saved image to {out_path}")


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a cozy cabin in a snowy forest, golden hour"
    generate(prompt)
