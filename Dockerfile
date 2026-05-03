# ============ Stage 1: 从 vllm-ascend 镜像提取 CANN 运行时 ============
FROM openeuler/vllm-ascend:0.9.0rc2-torch_npu2.5.1-cann8.1.rc1-python3.10-oe2203lts AS cann-extract

# ============ Stage 2: 构建最终推理镜像 ============
FROM python:3.10-slim

# 复制 CANN 运行时库
COPY --from=cann-extract /usr/local/Ascend/ascend-toolkit /usr/local/Ascend/ascend-toolkit
COPY --from=cann-extract /usr/local/Ascend/driver /usr/local/Ascend/driver
COPY --from=cann-extract /etc/ascend_install.info /etc/ascend_install.info

ENV LD_LIBRARY_PATH=/usr/local/Ascend/ascend-toolkit/latest/lib64:/usr/local/Ascend/driver/lib64:$LD_LIBRARY_PATH
ENV ASCEND_HOME_PATH=/usr/local/Ascend/ascend-toolkit/latest
ENV ASCEND_AID_LIBRARY_PATH=/usr/local/Ascend/ascend-toolkit/latest/ascend_toolkit/python/site-packages

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

CMD ["python", "app.py"]
