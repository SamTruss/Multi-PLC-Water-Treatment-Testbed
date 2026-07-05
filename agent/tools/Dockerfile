# Attacker / agent harness for the Multi-PLC Water Treatment Testbed
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY modbus_client.py /app/modbus_client.py

# Kept alive so you can `docker exec` into it to run engagements.
CMD ["sleep", "infinity"]
