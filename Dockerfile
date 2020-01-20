FROM library/python:3.7-slim

COPY requirements.txt /app/
WORKDIR /app
RUN pip3.7 install -r requirements.txt
COPY . /app

CMD ["python", "/app/google_login/main.py"]
