
from dtraia_api.utils.common import cipher_rsa, decipher_rsa, hash_data

TEST_TEXT = "Este es un simple texto"
TEST_HEX = "0f27032f65f79e54a4631a967a993f6841ed9caae7929ebad3cc11584c9c86b91411e15c6295b0f7266d48b414b18136e8b9addb6fe658aeec873840e1b069e4b224812646dd471e398f94569ba781344d7ca6c8f1d1a2d92ea480b4ec129d598a24923023397c7b867614ec1879e443b710646df57b5593df123e5c56067275"

def test_rsa_cipher():
    hex_cipher = cipher_rsa(TEST_TEXT)
    assert hex_cipher != None
    assert type(hex_cipher) == str

def test_decipher_rsa():
    decipher_text = decipher_rsa(TEST_HEX)
    assert decipher_text != None
    assert type(decipher_text) == str

def test_cipher_decipher():
    hex_cipher = cipher_rsa(TEST_TEXT)
    decipher_text = decipher_rsa(hex_cipher)
    assert TEST_TEXT == decipher_text
    
def test_hash():
    hash_digest = hash_data(TEST_TEXT)
    assert hash_digest != None
    assert type(hash_digest) == str