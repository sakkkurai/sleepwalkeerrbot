FROM python:3.13.17-slim-trixie
WORKDIR /bot
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.txt
CMD [ "python", "bot.py" ]
