import importlib.util
import json
import os
import sys
import types
from unittest import mock

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class FakeTensor:
    """Stands in for a ComfyUI IMAGE (torch tensor [B,H,W,C], 0..1) without torch."""

    def __init__(self, arr):
        self.arr = arr

    def __getitem__(self, i):
        return FakeTensor(self.arr[i])

    def cpu(self):
        return self

    def numpy(self):
        return self.arr


@pytest.fixture()
def pkg(tmp_path):
    spec = importlib.util.spec_from_file_location("comfyui_fitv", os.path.join(ROOT, "__init__.py"), submodule_search_locations=[ROOT])
    mod = importlib.util.module_from_spec(spec)
    sys.modules["comfyui_fitv"] = mod
    sys.modules["folder_paths"] = types.SimpleNamespace(get_output_directory=lambda: str(tmp_path))
    spec.loader.exec_module(mod)
    yield mod
    for k in [k for k in sys.modules if k.startswith("comfyui_fitv")] + ["folder_paths"]:
        sys.modules.pop(k, None)


def replay(answers, calls):
    it = iter(answers)

    def transport(url, payload, headers):
        calls.append((url, payload, headers))
        st, env = next(it)
        return st, json.dumps(env).encode()

    return transport


def run(pkg, answers, calls, **kw):
    client = sys.modules["comfyui_fitv.fitv_client"]
    real = client.generate_video
    t = replay(answers, calls)
    with mock.patch.object(client, "generate_video", side_effect=lambda *a, **k: real(*a, transport=t, poll_every=0, **k)), \
         mock.patch.object(client, "download", return_value=b"MP4DATA"):
        node = pkg.NODE_CLASS_MAPPINGS["FreeImageToVideo"]()
        return node.generate(**{"prompt": "a fox", "duration": 6, "resolution": "480p", "aspect_ratio": "9:16", "api_key": "sk-x", **kw})


DONE = [
    (200, {"code": 0, "message": "ok", "data": {"id": "task_1", "status": "pending"}}),
    (200, {"code": 0, "message": "ok", "data": {"id": "task_1", "status": "processing", "videos": []}}),
    (200, {"code": 0, "message": "ok", "data": {"id": "task_1", "status": "success", "videos": ["https://cdn.freeimagetovideo.ai/v/1.mp4"]}}),
]


def test_text_to_video_saves_mp4(pkg, tmp_path):
    calls = []
    out = run(pkg, DONE, calls)
    path, url = out["result"]
    assert url == "https://cdn.freeimagetovideo.ai/v/1.mp4"
    assert path.startswith(str(tmp_path)) and path.endswith(".mp4") and open(path, "rb").read() == b"MP4DATA"
    body = calls[0][1]
    assert calls[0][0] == "https://freeimagetovideo.ai/api/ai/generate"
    assert body["model"] == "minimax-h3" and body["scene"] == "text-to-video"
    assert body["options"] == {"duration": 6, "resolution": "480p", "aspect_ratio": "9:16", "sound": True}


def test_image_uploads_then_image_to_video(pkg):
    client = sys.modules["comfyui_fitv.fitv_client"]
    seen = {}

    class Resp:
        status = 200

        def __init__(self, req):
            seen["req"] = req

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self):
            return json.dumps({"code": 0, "message": "ok", "data": {"urls": ["https://cdn.freeimagetovideo.ai/uploads/input/a.png"]}}).encode()

    calls = []
    img = FakeTensor(np.random.rand(1, 8, 8, 3).astype(np.float32))
    with mock.patch.object(client.urllib.request, "urlopen", side_effect=lambda req, timeout=0: Resp(req)):
        run(pkg, DONE, calls, image=img)
    req = seen["req"]
    assert req.full_url == "https://freeimagetovideo.ai/api/storage/upload-image"
    assert b"Content-Type: image/png" in req.data and req.data.count(b"\x89PNG") == 1
    body = calls[0][1]
    assert body["scene"] == "image-to-video"
    assert body["options"]["image_input"] == ["https://cdn.freeimagetovideo.ai/uploads/input/a.png"]


def test_wrong_key_raises_auth(pkg):
    client = sys.modules["comfyui_fitv.fitv_client"]
    with pytest.raises(client.AuthError):
        run(pkg, [(401, {"code": -1, "message": "Invalid API key", "data": {"reason": "invalid_api_key"}})], [])


def test_refusal_on_http_200(pkg):
    client = sys.modules["comfyui_fitv.fitv_client"]
    with pytest.raises(client.PlanError):
        run(pkg, [(200, {"code": -1, "message": "API runs need a paid plan", "data": {"reason": "plan_required"}})], [])


def test_failed_run(pkg):
    client = sys.modules["comfyui_fitv.fitv_client"]
    with pytest.raises(client.GenerationFailed):
        run(pkg, [DONE[0], (200, {"code": 0, "data": {"id": "task_1", "status": "failed", "errorMessage": "vendor error"}})], [])
