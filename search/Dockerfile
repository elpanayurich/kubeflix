FROM python:3.13-slim

WORKDIR /app

COPY search/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY search/app.py ./

EXPOSE 5000

CMD ["python", "app.py"]