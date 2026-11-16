# Evidence

Save screenshots here as you go. Suggested names:

| File | What it shows |
|---|---|
| `01_plaintext_payload.png` | Phase 1: Wireshark PUBLISH packet with readable JSON |
| `02_plaintext_password.png` | Phase 2: Wireshark CONNECT packet showing username and password in clear text |
| `02_anonymous_refused.png` | Phase 2: sensor without `--auth` refused by broker |
| `03_tls_encrypted.png` | Phase 3: Wireshark shows only TLS "Application Data" on 8883 |
| `03_follow_stream.png` | Phase 3: Follow TCP Stream shows unreadable bytes |
| `04_acl_before.png` | `acl_test.py` on phase 3 (2 FAIL) |
| `04_acl_after.png` | `acl_test.py` on phase 4 (4/4 PASS) |
| `04_broker_denied_log.png` | Broker log lines showing denied publish/subscribe |

Do not commit .pcapng captures from phase 2. They contain the lab passwords.
