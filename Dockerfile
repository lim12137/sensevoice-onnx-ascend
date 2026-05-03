FROM ascendhub.huawei.com/public-ascend-hub/ascend-pytorch:24.0.RC1-A2-2.1.0-py3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 8000

CMD ["python", "app.py"]
