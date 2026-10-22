FROM fedora:latest
WORKDIR /bot
COPY . .
RUN dnf install -y python python-pip
RUN python -m pip install --no-cache-dir -r requirements.txt
CMD [ "python" "bot.py" ]
