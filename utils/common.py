"""
DTRAIA_API - Research Project
Script for execute the generated code by the LLM and take a snapshot of the topolgy.
Authors: Rodrigo Alvarez, Adrian Rodriguez, Uriel Perez
Created on: 2023 
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from base64 import b64decode
import os
import hashlib

KEYS_DIR = os.environ["KEYS_DIR"] if "KEYS_DIR" in os.environ else "{}/keys".format(os.getcwd())


def load_private_key():
    with open(KEYS_DIR + "/dtraia_priv.pem", "rb") as key_file:
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


def dec_rsa_front(enc_text):
    private_file = KEYS_DIR + "/dtraia_priv.pem"
    private_key = RSA.import_key(open(private_file).read())
    rsa_key = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    return rsa_key.decrypt(b64decode(enc_text)).decode()