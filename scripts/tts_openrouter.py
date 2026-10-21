#!/usr/bin/env python3
"""
tts_openrouter.py — 用 OpenRouter 的 Gemini TTS 批次產生遊戲配音（mp3）

用法：
  export OPENROUTER_API_KEY=sk-or-v1-...        # 金鑰只放環境變數，絕不寫進 repo / 網頁
  python3 scripts/tts_openrouter.py example/voice_lines.json example/voice
  python3 scripts/tts_openrouter.py example/voice_lines.json example/voice throw miss   # 只重做某幾句

voice_lines.json 格式：
  { "model": "google/gemini-3.8-flash-tts",
    "lines": { "throw": {"voice": "Puck", "text": "[comedic, cartoonish, cocky] 看我的！", "pitch": 1.0}, ... } }

重點（踩過的坑）：
  - Gemini TTS 只回傳 PCM（24kHz / 16-bit / mono），要 mp3 必須自己用 ffmpeg 轉
  - 頭尾的靜音一定要剪，不然遊戲裡會「慢半拍」
  - pitch > 1 可把聲音變尖（小動物、小孩），用 ffmpeg asetrate 做
  - 不用 Python urllib：macOS 的 Python 常有 SSL 憑證問題，改用 curl 最穩
"""
import json, os, subprocess, sys, tempfile

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[2]; only = set(sys.argv[3:])
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("請先 export OPENROUTER_API_KEY=...")
    os.makedirs(out, exist_ok=True)
    model = cfg.get("model", "google/gemini-3.8-flash-tts")
    ok = 0
    for name, ln in cfg["lines"].items():
        if only and name not in only:
            continue
        body = json.dumps({"model": model, "input": ln["text"], "voice": ln.get("voice", "Puck"),
                           "response_format": "pcm"}).encode()
        pcm = os.path.join(tempfile.gettempdir(), f"_tts_{name}.pcm")
        r = subprocess.run(["curl", "-s", "-w", "%{http_code}", "-o", pcm, "https://openrouter.ai/api/v1/audio/speech",
                            "-H", "Authorization: Bearer " + key, "-H", "Content-Type: application/json",
                            "--data-binary", "@-"], input=body, capture_output=True)
        code = r.stdout.decode()
        if code != "200":
            print(f"✗ {name}: HTTP {code} {open(pcm, 'rb').read()[:200]!r}")
            continue
        af = ("silenceremove=start_periods=1:start_threshold=-45dB,areverse,"
              "silenceremove=start_periods=1:start_threshold=-45dB,areverse")
        p = float(ln.get("pitch", 1.0))
        if p != 1.0:
            af += f",asetrate=24000*{p},aresample=24000"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "s16le", "-ar", "24000", "-ac", "1",
                        "-i", pcm, "-af", af, "-b:a", "64k", os.path.join(out, name + ".mp3")], check=True)
        os.remove(pcm); ok += 1
        print(f"✓ {name}  ({ln.get('voice','Puck')})  {ln['text']}")
    print(f"done: {ok} files -> {out}")

if __name__ == "__main__":
    main()
