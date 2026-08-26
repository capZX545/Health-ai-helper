FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY *.py .
COPY *.json .
COPY *.gz .
COPY *.db .
COPY *.csv .
COPY *.html .
COPY *.js .
COPY *.svg .
COPY fonts/ fonts/
EXPOSE 2077
CMD ["python", "run_web.py", "--host", "0.0.0.0", "--port", "2077", "--no-browser"]
