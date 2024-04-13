FROM python:3.10

ENV POKE_PATH=/poke

COPY requirements.txt /opt/poke/
COPY src/* /opt/poke/
RUN pip install --no-cache-dir -r /opt/poke/requirements.txt

CMD ["python3", "/opt/poke/poke.py", "up"]