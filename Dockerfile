FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --uid 10001 --create-home focus \
    && mkdir /data && chown focus:focus /data
COPY app.py storage.py ./
COPY templates/ ./templates/
COPY static/style.css ./static/style.css
ENV FOCUS_DATA_DIRECTORY=/data FOCUS_BIND_HOST=0.0.0.0 FOCUS_PORT=8766
USER focus
EXPOSE 8766
CMD ["python", "app.py"]
