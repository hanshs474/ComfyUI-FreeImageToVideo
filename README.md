# ComfyUI-FreeImageToVideo

Free image to video AI with no daily cap: start with no sign-up, keep going on a free account. Every video comes with sound and no watermark. This is the official ComfyUI node for [Free Image to Video](https://freeimagetovideo.ai/?utm_source=comfyui&utm_medium=package): text to video and image to video with sound from a graph, on MiniMax H3. No local GPU and no model downloads, one API key.

| Node | Inputs | Outputs |
|---|---|---|
| **Free Image to Video (MiniMax H3, with sound)** | prompt, duration, resolution, aspect ratio; optional IMAGE (first frame), api_key, seed | `video_path` (MP4 saved to ComfyUI's output folder), `url` |

Leave `image` unconnected for text to video. Connect any IMAGE from your graph (a Load Image, a render, an upscaled still) and it becomes the first frame: the node uploads it to Free Image to Video's storage as a PNG and passes its URL along, so you can [animate a photo](https://freeimagetovideo.ai/video/animate-photo-ai) you already control.

## Install

ComfyUI Manager: search **ComfyUI-FreeImageToVideo**. Or clone into `custom_nodes`:

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/hanshs474/ComfyUI-FreeImageToVideo
```

No extra Python dependencies: the client uses the standard library, and the node uses the numpy and Pillow that ComfyUI already ships.

## API key and plans

Create a key at [freeimagetovideo.ai/settings/apikeys](https://freeimagetovideo.ai/settings/apikeys), then paste it into the node's `api_key` field or set `FREEIMAGETOVIDEO_API_KEY` before starting ComfyUI. API runs need a paid plan: each run draws on the plan's full-speed allowance, then waits in the relaxed queue. See [pricing](https://freeimagetovideo.ai/pricing).

To make clips without a key, use [image to video AI with sound](https://freeimagetovideo.ai/video/image-to-video-ai-with-sound) on the site: start with no sign-up, keep going on a free account.

## Options

| option | values |
|---|---|
| `duration` | 4, 5, 6, 8, 10, 15 seconds |
| `resolution` | `480p`, `768p` |
| `aspect_ratio` | `16:9`, `9:16`, `1:1` |

Video takes minutes and the node blocks until the file is ready (30-minute limit, polled every 10 seconds). Change `seed` to force a new run with the same inputs. A wrong key, no paid plan, not enough credits or a refused prompt stops the node with the API's own message.

MIT licensed. Made by [Free Image to Video](https://freeimagetovideo.ai/?utm_source=comfyui&utm_medium=package).
