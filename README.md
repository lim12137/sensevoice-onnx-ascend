# SenseVoice-Small ONNX Ascend

SenseVoice-small 模型在昇腾 NPU 上的 ONNX 推理服务，基于 FastAPI，模型通过挂载加载。

## 快速开始

### 1. 准备模型文件

将 ONNX 模型和词表放到宿主机目录：

```bash
mkdir -p ./models
# 放入 model.onnx 和 vocab.json
```

### 2. 构建镜像

```bash
docker build -t sensevoice-onnx-ascend:latest .
```

### 3. 运行（昇腾 NPU）

```bash
docker run -d \
  --name sensevoice \
  --network host \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  --device=/dev/hisi_hdc \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver:ro \
  -v $(pwd)/models:/app/models:ro \
  -e ONNX_PROVIDERS=AscendExecutionProvider,CPUExecutionProvider \
  sensevoice-onnx-ascend:latest
```

### 4. 运行（CPU 模式，无昇腾设备）

```bash
docker run -d \
  --name sensevoice \
  -p 8000:8000 \
  -v $(pwd)/models:/app/models:ro \
  sensevoice-onnx-ascend:latest
```

### 5. 调用接口

```bash
# 健康检查
curl http://localhost:8000/health

# 语音识别
curl -X POST http://localhost:8000/recognize \
  -F "file=@test.wav" \
  -F "language=auto"
```

## GitHub Actions 自动构建

推送到 `main` 分支或打 tag 即自动构建并推送镜像到 Docker Hub。

需要在仓库 Settings → Secrets 中配置：

- `DOCKERHUB_USERNAME` — Docker Hub 用户名
- `DOCKERHUB_TOKEN` — Docker Hub Access Token

## 目录结构

```
├── .github/workflows/build.yml
├── app.py
├── Dockerfile
├── requirements.txt
├── .dockerignore
└── models/          ← 挂载，不写入镜像
    ├── model.onnx
    └── vocab.json
```
