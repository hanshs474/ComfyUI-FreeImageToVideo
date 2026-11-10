import io
import os
import time

from . import fitv_client as fitv

KEY_TOOLTIP = (
    "Key from freeimagetovideo.ai/settings/apikeys. Leave empty to read FREEIMAGETOVIDEO_API_KEY "
    "from the environment. API runs need a paid plan."
)


def _to_png(image) -> bytes:
    import numpy as np
    from PIL import Image

    arr = (image[0].cpu().numpy().clip(0, 1) * 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


def _output_dir() -> str:
    try:
        import folder_paths  # ComfyUI's own module, present when running inside ComfyUI

        return folder_paths.get_output_directory()
    except ImportError:
        return os.getcwd()


def _save_clip(url: str) -> str:
    path = os.path.join(_output_dir(), f"freeimagetovideo-{int(time.time() * 1000)}.mp4")
    with open(path, "wb") as f:
        f.write(fitv.download(url))
    return path


class FreeImageToVideo:
    """Text to video, or image to video when an IMAGE is connected (it becomes the first frame).
    MiniMax H3 with sound. Saves the MP4 to ComfyUI's output folder and returns its path and URL."""

    CATEGORY = "Free Image to Video"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("video_path", "url")
    FUNCTION = "generate"
    OUTPUT_NODE = True

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {"multiline": True, "default": "the camera slowly pushes in while soft light sweeps across the scene"}),
                "duration": ([4, 5, 6, 8, 10, 15], {"default": 6, "tooltip": "Seconds"}),
                "resolution": (["480p", "768p"], {"default": "480p"}),
                "aspect_ratio": (["16:9", "9:16", "1:1"], {"default": "16:9"}),
            },
            "optional": {
                "image": ("IMAGE", {"tooltip": "Optional first frame. Connected: image to video. Empty: text to video."}),
                "api_key": ("STRING", {"default": "", "tooltip": KEY_TOOLTIP}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFF, "tooltip": "Change to force a new run with the same inputs"}),
            },
        }

    def generate(self, prompt, duration, resolution, aspect_ratio, image=None, api_key="", seed=0):
        first = fitv.upload_image(_to_png(image), "image/png") if image is not None else None
        url = fitv.generate_video(
            prompt,
            first,
            api_key=(api_key or "").strip() or None,
            duration=int(duration),
            resolution=resolution,
            aspect_ratio=aspect_ratio,
        )
        return {"ui": {"text": [url]}, "result": (_save_clip(url), url)}


NODE_CLASS_MAPPINGS = {"FreeImageToVideo": FreeImageToVideo}
NODE_DISPLAY_NAME_MAPPINGS = {"FreeImageToVideo": "Free Image to Video (MiniMax H3, with sound)"}
