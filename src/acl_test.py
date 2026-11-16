"""
Phase 4 proof: checks that each account can do only its own job.

  python src/acl_test.py

Run it once on phase3_tls (expect 2 FAIL: no rules yet) and once on
phase4_acl (expect 4 PASS). Screenshot both for the evidence folder.

How each check decides "allowed" vs "denied":
  publish   - the broker's PUBACK reason code (MQTT v5 + QoS 1).
  subscribe - whether a test reading is actually DELIVERED. Mosquitto 2.0
              grants every SUBSCRIBE and enforces "read" rules when it
              delivers each message, so the SUBACK alone does not show
              whether the client can read anything.
"""
import sys
import threading

from mqtt_common import TOPIC, connect_or_exit

TEST_PAYLOAD = '{"sensor_id": "acl-test", "temp_c": 0, "ts": "acl-test"}'
DELIVERY_WAIT = 3  # seconds to wait for the probe reading to arrive


def publish_once(client_id, role):
    """Publish TEST_PAYLOAD at QoS 1 and return the broker's PUBACK reason code (or None)."""
    client = connect_or_exit(client_id, role, auth=True, tls=True)
    done, result = threading.Event(), {}

    def on_publish(c, userdata, mid, reason_code, properties):
        result["rc"] = reason_code
        done.set()

    client.on_publish = on_publish
    client.publish(TOPIC, TEST_PAYLOAD, qos=1)  # QoS 1 + MQTT v5 = broker replies with a reason code
    done.wait(5)
    client.disconnect()
    client.loop_stop()
    return result.get("rc")


def try_publish(role):
    """Returns (allowed, what the broker said). allowed is None if the broker never answered."""
    rc = publish_once(f"acltest-{role}-pub", role)
    if rc is None:
        return None, "no reply"
    return not rc.is_failure, str(rc)


def try_subscribe(role):
    """
    Subscribe to sensors/#, then have the sensor account publish one probe reading.
    Allowed only if the broker grants the subscription AND delivers the reading.
    """
    client = connect_or_exit(f"acltest-{role}-sub", role, auth=True, tls=True)
    subscribed, delivered, result = threading.Event(), threading.Event(), {}

    def on_subscribe(c, userdata, mid, reason_codes, properties):
        result["rc"] = reason_codes[0]
        subscribed.set()

    def on_message(c, userdata, msg):
        delivered.set()

    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.subscribe("sensors/#", qos=1)
    subscribed.wait(5)
    rc = result.get("rc")

    try:
        if rc is None:
            return None, "no reply"
        if rc.is_failure:
            return False, str(rc)  # refused outright at subscribe time

        # Granted. Now check whether a real reading actually reaches this client.
        probe_rc = publish_once("acltest-probe-pub", "sensor")
        if probe_rc is None or probe_rc.is_failure:
            return None, "probe publish failed"
        got_it = delivered.wait(DELIVERY_WAIT)
        return got_it, f"{rc}, {'1' if got_it else '0'} delivered"
    finally:
        client.disconnect()
        client.loop_stop()


def main():
    checks = [
        ("sensor publishes reading", try_publish, "sensor", True),
        ("sensor subscribes sensors/#", try_subscribe, "sensor", False),
        ("dashboard subscribes sensors/#", try_subscribe, "dashboard", True),
        ("dashboard publishes reading", try_publish, "dashboard", False),
    ]
    rows, passed = [], 0
    for label, fn, role, should_allow in checks:
        allowed, said = fn(role)
        ok = allowed is not None and allowed == should_allow
        passed += ok
        rows.append((label, "allowed" if should_allow else "denied", said, "PASS" if ok else "FAIL"))

    print(f"\n{'Check':<34}{'Expected':<11}{'Broker said':<30}Result")
    print("-" * 81)
    for r in rows:
        print(f"{r[0]:<34}{r[1]:<11}{r[2]:<30}{r[3]}")
    print(f"\n{passed}/{len(checks)} least-privilege checks passed")
    sys.exit(0 if passed == len(checks) else 1)


if __name__ == "__main__":
    main()
