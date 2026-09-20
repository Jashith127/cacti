#!/usr/bin/env bash
set -euo pipefail
cd /workspace
export PYTHONPATH=src
export PATH="$HOME/.local/bin:$PATH"

clear || true
echo "=== cacti Needle 3 assistant demo (Linux dev / routing) ==="
echo
echo "[1/4] Unit tests"
python3 -m pytest -q
echo
python3 - <<'PY'
import json, time, os
from pathlib import Path
os.makedirs(Path.home()/".cache/cacti", exist_ok=True)
cache = Path.home()/".cache/cacti/app_registry.json"
data = json.loads(Path("tests/fixtures/sample_registry.json").read_text())
data["generated_at_unix"] = time.time()
cache.write_text(json.dumps(data))
print("Seeded app registry cache:", cache)
PY
echo
echo "[2/4] Act tier: list apps (low risk, confidence 0.92)"
export CACTI_FAKE_TOOL="list_matching_applications:query=note:confidence=0.92"
python3 -m cacti.assistant.loop --text "find notepad"
echo
echo "[3/4] Refuse tier: default audio (confidence 0.40)"
export CACTI_FAKE_TOOL="set_default_audio_output:device_name=headphones:confidence=0.40"
python3 -m cacti.assistant.loop --text "switch to headphones"
echo
echo "[3b] Confirm tier: OCR (always confirm) — auto-confirm yes"
export CACTI_FAKE_TOOL="ocr_foreground_window:confidence=0.95"
printf 'yes\n' | python3 -m cacti.assistant.loop --text "read screen"
echo
echo "[4/4] Confirm tier: registry list (mock cache)"
python3 - <<'PY'
import json, time
from pathlib import Path
from cacti.apps.registry import AppRegistry

cache = Path("/tmp/cacti_demo_registry.json")
data = json.loads(Path("tests/fixtures/sample_registry.json").read_text())
data["generated_at_unix"] = time.time()
cache.write_text(json.dumps(data))
reg = AppRegistry(cache_path=str(cache), ttl_seconds=99999)
print("Search 'slack':", reg.search("slack")[0][0].display_name)
print("Resolve 'notepad':", reg.resolve_spoken_name("notepad").display_name)
PY
echo
echo "=== Demo complete (Win32 tools run on Windows 11 with pip install -e '.[windows]') ==="
sleep 4
