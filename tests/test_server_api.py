"""End-to-end check of the bridge server's HTTP API, with no camera needed."""
import json
import threading
import urllib.request
from http.server import HTTPServer

import pytest

import unified_bridge_server as server


@pytest.fixture(scope="module")
def base_url():
    httpd = HTTPServer(("127.0.0.1", 0), server.UnifiedBridgeHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def get(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.status, resp.read()


def post_json(url, payload):
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.status, json.loads(resp.read())


def test_serves_web_app(base_url):
    status, body = get(base_url + "/")
    assert status == 200
    assert b"Silent Voice Bridge" in body


def test_lists_sign_library(base_url):
    status, body = get(base_url + "/api/signs")
    signs = json.loads(body)
    assert status == 200
    assert "HELLO" in signs and "HOW-ARE-YOU" in signs


def test_english_to_avatar_video(base_url):
    """Typed English becomes a gloss sequence and a rendered avatar video."""
    status, body = get(base_url + "/api/synthesize?text=hello%20how%20are%20you")
    result = json.loads(body)
    assert status == 200
    assert result["glosses"] == ["HELLO", "HOW-ARE-YOU"]
    assert result["total_frames"] > 0
    status, video = get(base_url + result["video_url"])
    assert status == 200 and len(video) > 0


def test_learn_mode_coaching(base_url):
    status, result = post_json(base_url + "/api/score", {"text": "HELLO"})
    assert status == 200
    assert result["gloss"] == "HELLO"
    assert result["tip"]
