"""Shared connection code for the sensor, dashboard and ACL test."""
import os
import ssl
import threading
from pathlib import Path

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

HOST = os.getenv("MQTT_HOST", "localhost")
TOPIC = os.getenv("MQTT_TOPIC", "sensors/lab1/temperature")
CA_FILE = ROOT / "mosquitto" / "certs" / "ca.crt"


def add_common_args(parser):
    parser.add_argument("--auth", action="store_true",
                        help="log in with the username/password for this role from .env (phase 2+)")
    parser.add_argument("--tls", action="store_true",
                        help="connect over TLS on port 8883 (phase 3+)")


def connect_or_exit(client_id, role, auth, tls):
    """
    Connect as 'sensor' or 'dashboard'. Returns a connected client with its
    network loop running, or exits with a clear message if the broker says no.
    """
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2,
                         client_id=client_id, protocol=mqtt.MQTTv5)
    port = 1883

    if auth:
        user = os.getenv(f"{role.upper()}_USER")
        password = os.getenv(f"{role.upper()}_PASS")
        if not user or not password:
            raise SystemExit(f"Missing {role.upper()}_USER / {role.upper()}_PASS in .env")
        client.username_pw_set(user, password)

    if tls:
        if not CA_FILE.exists():
            raise SystemExit(f"{CA_FILE} not found. Run: python scripts/gen_certs.py")
        # Trust only our lab CA, and check the server name matches "localhost"
        client.tls_set(ca_certs=str(CA_FILE), cert_reqs=ssl.CERT_REQUIRED)
        port = 8883

    ready = threading.Event()
    result = {}

    def on_connect(c, userdata, flags, reason_code, properties):
        result["rc"] = reason_code
        ready.set()

    client.on_connect = on_connect

    try:
        client.connect(HOST, port, keepalive=60)
    except OSError as e:  # includes TLS errors and "connection refused"
        raise SystemExit(f"[{client_id}] could not connect to {HOST}:{port}: {e}")

    client.loop_start()
    if not ready.wait(10):
        client.loop_stop()
        raise SystemExit(f"[{client_id}] no answer from broker on {HOST}:{port}")

    rc = result["rc"]
    if rc.is_failure:
        client.loop_stop()
        raise SystemExit(f"[{client_id}] broker refused the connection: {rc}")

    mode = "TLS" if tls else "PLAINTEXT"
    who = os.getenv(f"{role.upper()}_USER") if auth else "anonymous"
    print(f"[{client_id}] connected to {HOST}:{port} ({mode}) as {who}")
    return client
