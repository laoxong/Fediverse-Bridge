FROM python:3.9-bullseye

ENV telegramtoken="None"
ENV misskeybot="None"
ENV DOCKER_CONTAINER=true

WORKDIR /app

COPY main.py .
COPY requirements.txt ./

RUN pip install -r requirements.txt

CMD ["python", "main.py"]