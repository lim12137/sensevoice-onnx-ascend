import os
import json
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse

# ONNX Runtime 在昇腾上通过 CANN ACL 后端加速
import onnxruntime as ort

app = FastAPI(title="SenseVoice-Small ONNX Service")

MODEL_DIR = os.environ.get("MODEL_DIR", "/app/models")
MODEL_PATH = os.path.join(MODEL_DIR, "model.onnx")
VOCAB_PATH = os.path.join(MODEL_DIR, "vocab.json")

session = None
vocab = None


def load_model():
    global session, vocab
    if not Path(MODEL_PATH).exists():
        print(f"[WARN] model not found: {MODEL_PATH}, skip loading")
        return

    providers = os.environ.get("ONNX_PROVIDERS", "CPUExecutionProvider").split(",")
    sess_options = ort.SessionOptions()
    sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    session = ort.InferenceSession(MODEL_PATH, sess_options=sess_options, providers=providers)
    print(f"[INFO] model loaded, providers: {session.get_providers()}")

    if Path(VOCAB_PATH).exists():
        with open(VOCAB_PATH, "r", encoding="utf-8") as f:
            vocab = json.load(f)


def preprocess(audio_path: str, sr: int = 16000) -> np.ndarray:
    audio, _ = librosa.load(audio_path, sr=sr)
    feat = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80, fmax=8000)
    feat = librosa.power_to_db(feat, top_db=80)
    feat = (feat - feat.mean()) / (feat.std() + 1e-6)
    return feat.astype(np.float32)


def decode(output: np.ndarray) -> str:
    if vocab is None:
        tokens = output.argmax(axis=-1).flatten().tolist()
        return " ".join(str(t) for t in tokens)
    tokens = output.argmax(axis=-1).flatten().tolist()
    text = "".join(vocab.get(str(t), "") for t in tokens)
    return text.strip()


@app.on_event("startup")
async def startup():
    load_model()


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": session is not None}


@app.post("/recognize")
async def recognize(file: UploadFile = File(...), language: str = Form(default="auto")):
    if session is None:
        return JSONResponse(status_code=503, content={"error": "model not loaded"})

    tmp_path = f"/tmp/{file.filename}"
    content = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        feat = preprocess(tmp_path)
        feat_input = np.expand_dims(feat, axis=0)
        inputs = {session.get_inputs()[0].name: feat_input}
        output = session.run(None, inputs)[0]
        text = decode(output)
        return {"text": text, "language": language}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
