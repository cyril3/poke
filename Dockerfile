FROM python:3.10

WORKDIR /opt/poke

COPY requirements.txt ./
COPY src/* ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "/opt/poke/poke.py", "up"]