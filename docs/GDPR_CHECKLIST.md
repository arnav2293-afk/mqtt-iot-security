# GDPR Checklist: MQTT Temperature Sensor System

> Lab review written against GDPR (Regulation (EU) 2016/679). It is a learning exercise, not legal advice.

## Step 0: Is this personal data at all?

A temperature number on its own is not personal data. It becomes personal data (Art. 4(1)) when it can be linked to a person, for example a sensor in a named employee's office, a hotel room, or someone's flat, where readings reveal when that person is home.

**Assumption for this review:** the sensor sits in a rented apartment, so readings are treated as personal data. Planning for the worst case is the safer design choice (Art. 25).

## Checklist

| # | Requirement | GDPR ref | How this system handles it | Evidence | Status |
|---|---|---|---|---|---|
| 1 | Lawful basis is identified and written down | Art. 6 | Basis chosen: legitimate interest (building comfort and safety monitoring) | This document | Partial: no balancing test written |
| 2 | Purpose limitation: data used only for the stated purpose | Art. 5(1)(b) | Readings only feed the dashboard: only the dashboard account receives readings; any other account that subscribes gets nothing (ACL enforced at delivery) | `mosquitto/config/acl`, `04_acl_after.png` | Met |
| 3 | Data minimisation: collect only what is needed | Art. 5(1)(c) | Payload has 3 fields: sensor_id, temp_c, ts. No location, name, or MAC address | `src/sensor.py` | Met |
| 4 | Storage limitation: delete data when no longer needed | Art. 5(1)(e) | 30-day retention, enforced by purge script. Lab run: kept 296, deleted 0 (all rows were under 30 days old, so the delete path is not yet exercised) | `src/purge_old_data.py` output | Met (run manually; schedule it in production) |
| 5 | Confidentiality in transit | Art. 5(1)(f), Art. 32(1)(a) | TLS 1.2+ on port 8883 (TLS 1.3 negotiated in the lab); broker no longer listens on plain port 1883 | `03_tls_encrypted.png`, `03_follow_stream.png` | Met |
| 6 | Only known clients can connect | Art. 32(1)(b) | Anonymous access off; username and password required | `02_anonymous_refused.png` | Met |
| 7 | Passwords stored safely on the broker | Art. 32 | `mosquitto_passwd` stores salted PBKDF2-SHA512 hashes, not plain text | `passwd` file contents, e.g. `sensor01:$7$101$…` (hashes only; the file is git-ignored, so it is not in the repo) | Met |
| 8 | Least privilege: each account can do only its job | Art. 25(2), Art. 32 | Sensor: write own topic only (its reads are blocked at delivery: 0 readings delivered). Dashboard: read only (its publishes are refused: Not authorized) | `acl_test.py`: `04_acl_before.png` (2/4) then `04_acl_after.png` (4/4) | Met |
| 9 | Privacy by default: secure settings out of the box | Art. 25(2) | Final config refuses anonymous, plaintext, and unlisted topics by default | `phase4_acl.conf` | Met |
| 10 | Secrets kept out of source code | Art. 32 | Credentials live in `.env`, which is git-ignored; repo ships `.env.example` only. `passwd`, certificates and private keys are also git-ignored. The password visible in `02_plaintext_password.png` was rotated before publishing and no longer works | `.gitignore` | Met |
| 11 | Data at rest is protected | Art. 32(1)(a) | `data/readings.csv` is plain text on disk | None | Gap: use full-disk encryption (FileVault / BitLocker) |
| 12 | Security events are logged so breaches can be detected | Art. 32(1)(d), Art. 33 | Broker logs connections, refusals, and denied publishes. Blocked reads are dropped silently and are not logged | `04_broker_denied_log.png` | Partial: logs not retained (lost when the container is recreated) or alerted on |
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
