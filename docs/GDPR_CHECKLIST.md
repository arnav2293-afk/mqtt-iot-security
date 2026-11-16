# GDPR Checklist: MQTT Temperature Sensor System

> Lab review written against GDPR (Regulation (EU) 2016/679). It is a learning exercise, not legal advice.

## Step 0: Is this personal data at all?

A temperature number on its own is not personal data. It becomes personal data (Art. 4(1)) when it can be linked to a person, for example a sensor in a named employee's office, a hotel room, or someone's flat, where readings reveal when that person is home.

**Assumption for this review:** the sensor sits in a rented apartment, so readings are treated as personal data. Planning for the worst case is the safer design choice (Art. 25).

## Checklist

| # | Requirement | GDPR ref | How this system handles it | Evidence | Status |
|---|---|---|---|---|---|
| 1 | Lawful basis is identified and written down | Art. 6 | Basis chosen: legitimate interest (building comfort and safety monitoring) | This document | Partial: no balancing test written |
| 2 | Purpose limitation: data used only for the stated purpose | Art. 5(1)(b) | Readings only feed the dashboard; no other consumer can subscribe (ACL) | `mosquitto/config/acl` | Met |
| 3 | Data minimisation: collect only what is needed | Art. 5(1)(c) | Payload has 3 fields: sensor_id, temp_c, ts. No location, name, or MAC address | `src/sensor.py` | Met |
| 4 | Storage limitation: delete data when no longer needed | Art. 5(1)(e) | 30-day retention, enforced by purge script | `src/purge_old_data.py` output | Met (run manually; schedule it in production) |
| 5 | Confidentiality in transit | Art. 5(1)(f), Art. 32(1)(a) | TLS 1.2+ on port 8883; plain port 1883 closed | Wireshark phase 3 screenshot | Met |
| 6 | Only known clients can connect | Art. 32(1)(b) | Anonymous access off; username and password required | Phase 2 refusal screenshot | Met |
| 7 | Passwords stored safely on the broker | Art. 32 | `mosquitto_passwd` stores salted PBKDF2-SHA512 hashes, not plain text | `passwd` file contents (hashes only) | Met |
| 8 | Least privilege: each account can do only its job | Art. 25(2), Art. 32 | Sensor: write own topic only. Dashboard: read only | `acl_test.py` 4/4 PASS | Met |
| 9 | Privacy by default: secure settings out of the box | Art. 25(2) | Final config refuses anonymous, plaintext, and unlisted topics by default | `phase4_acl.conf` | Met |
| 10 | Secrets kept out of source code | Art. 32 | Credentials live in `.env`, which is git-ignored; repo ships `.env.example` only | `.gitignore` | Met |
| 11 | Data at rest is protected | Art. 32(1)(a) | `data/readings.csv` is plain text on disk | None | Gap: use full-disk encryption (FileVault / BitLocker) |
| 12 | Security events are logged so breaches can be detected | Art. 32(1)(d), Art. 33 | Broker logs connections, refusals, and denied publish/subscribe | `docker compose logs` screenshot | Partial: logs not retained or alerted on |
| 13 | Breach notification within 72 hours | Art. 33, Art. 34 | No written procedure yet | None | Gap: write a one-page response plan |
| 14 | People can access or erase their data | Art. 15, Art. 17 | Readings can be filtered and deleted by sensor_id in the CSV | Manual | Partial: no request process |
| 15 | People are told what is collected and why | Art. 13 | No privacy notice yet | None | Gap: tenant notice needed |
| 16 | Record of processing activities | Art. 30 | This checklist captures purpose, data, retention, and security | This document | Partial |
| 17 | DPIA considered | Art. 35 | Single low-risk sensor, no profiling, so a full DPIA is likely not required. Reason recorded here | This document | Met (screening done) |

## Score

- Met: 10 of 17
- Partial: 4 of 17
- Gap: 3 of 17

## Top 3 fixes if this went to production

1. Encrypt data at rest and schedule `purge_old_data.py` daily (closes #4 note and #11).
2. Ship broker logs to a central store with an alert on repeated failed logins (#12).
3. Write the tenant privacy notice and a 72-hour breach plan (#13, #15).
