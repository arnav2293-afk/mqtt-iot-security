"""
Phase 3 helper: create a small private CA and a server certificate for the broker.
Works the same on Mac and Windows (pure Python, no openssl install needed).

Output (git-ignored): mosquitto/certs/ca.crt, ca.key, server.crt, server.key
"""
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

OUT = Path(__file__).resolve().parents[1] / "mosquitto" / "certs"


def new_key():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def save_key(key, path):
    path.write_bytes(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption(),  # lab only: broker must read it without a passphrase
    ))


def save_cert(cert, path):
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))


def key_usage(**on):
    fields = ["digital_signature", "content_commitment", "key_encipherment",
              "data_encipherment", "key_agreement", "key_cert_sign", "crl_sign",
              "encipher_only", "decipher_only"]
    return x509.KeyUsage(**{f: on.get(f, False) for f in fields})


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)

    # 1) Root CA (the "notary" the sensor and dashboard will trust)
    ca_key = new_key()
    ca_name = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IoT Security Lab"),
        x509.NameAttribute(NameOID.COMMON_NAME, "IoT Lab Root CA"),
    ])
    ca_ski = x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key())
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
        .add_extension(key_usage(digital_signature=True, key_cert_sign=True, crl_sign=True), critical=True)
        .add_extension(ca_ski, critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ca_ski), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    # 2) Server certificate for the broker, valid for "localhost" and 127.0.0.1
    srv_key = new_key()
    srv_cert = (
        x509.CertificateBuilder()
        .subject_name(x509.Name([
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "IoT Security Lab"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]))
        .issuer_name(ca_name)
        .public_key(srv_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(minutes=5))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1")),
        ]), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(key_usage(digital_signature=True, key_encipherment=True), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .add_extension(x509.SubjectKeyIdentifier.from_public_key(srv_key.public_key()), critical=False)
        .add_extension(x509.AuthorityKeyIdentifier.from_issuer_subject_key_identifier(ca_ski), critical=False)
        .sign(ca_key, hashes.SHA256())
    )

    save_key(ca_key, OUT / "ca.key")
    save_cert(ca_cert, OUT / "ca.crt")
    save_key(srv_key, OUT / "server.key")
    save_cert(srv_cert, OUT / "server.crt")
    print(f"Certificates written to {OUT}")
    for name in ["ca.crt", "ca.key", "server.crt", "server.key"]:
        print(f"  {name}")


if __name__ == "__main__":
    main()
