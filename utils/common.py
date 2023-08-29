from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
import os
import hashlib

KEYS_DIR = os.environ["KEYS_DIR"] if "KEYS_DIR" in os.environ else "{}/keys".format(os.getcwd())


def load_private_key():
    with open(KEYS_DIR + "/dtraia_server.key", "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )
    
    return private_key


def get_raw_private_key(private_key: PrivateKeyTypes):
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )


def get_raw_public_key(private_key: PrivateKeyTypes):
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.PKCS1
    )

def cipher_rsa(raw_text):
    pub_key = load_private_key().public_key()
    
    return pub_key.encrypt(
        raw_text.encode(), 
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).hex()

    
def decipher_rsa(enc_hex_text):
    return load_private_key().decrypt(
        bytes.fromhex(enc_hex_text),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    ).decode()


def hash_data(raw_data):
    return hashlib.sha256(raw_data.encode()).hexdigest()


    