import hashlib


def sha256_hash(text:str)->str:
    text = text.strip()
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

print(sha256_hash("0.27#&"))