FROM python:3.9-bullseye

ENV telegramtoken None
ENV misskeybot None

WORKDIR /app

COPY main.py .

RUN pip install pyTelegramBotAPI requests html2text

CMD ["python", "main.py", "$telegramtoken", "$misskeybot"]