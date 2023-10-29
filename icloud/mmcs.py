from dataclasses import dataclass
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import random
import requests


CHUNK_SIZE = 0x500000

# @dataclass
# class Chunk:
#     data: bytes # may be encrypted
#     key: bytes | None = None # may be None if not encrypted
#     signature: bytes # Will be incorrect before decryption

#     def _update_signature(self) -> bytes: # Really just a hash
#         return b'\x81' + hashlib.sha256(hashlib.sha256(self.data).digest()).digest()[:20]

#     def __post_init__(self):
#         self.signature = self._update_signature()

#     def decrypt(self):
#         if self.key is None:
#             return # Nothing to do
#         iv = 16 * b'\x00'
#         decryptor = Cipher(algorithms.AES(self.key), modes.CFB(iv)).decryptor()
#         self.data = decryptor.update(self.data) + decryptor.finalize()
#         self._update_signature() # The signature should always be calculated after decryption
#         self.key = None # We do not need the key anymore
    
#     def encrypt(self):
#         self.key = random.randbytes(16)
#         iv = 16 * b'\x00'
#         encryptor = Cipher(algorithms.AES(self.key), modes.CFB(iv)).encryptor()
#         self.data = encryptor.update(self.data) + encryptor.finalize()
#         # We do not update the signature

@dataclass
class Bucket: # Also known as a container
    url: str
    headers: dict[str, str]
    chunks: list[bytes] # list[hash]

    def upload(self, datas: list[bytes]):
        # list[data]
        requests.put(self.url, data=b''.join(datas), headers=self.headers, verify=False)

    def download(self) -> list[bytes]:
        pass
    
def hash_chunk(chunk: bytes) -> bytes:
    return b'\x81' + hashlib.sha256(hashlib.sha256(chunk).digest()).digest()[:20]

def encrypt_chunk(chunk: bytes, key: bytes) -> bytes:
    iv = 16 * b'\x00'
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    return  encryptor.update(chunk) + encryptor.finalize()

def chunk(data: bytes) -> list[tuple[bytes, bytes, bytes]]:
    # list[tuple[hash, key, data]]
    chunks = []
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i:i+CHUNK_SIZE]
        key = random.randbytes(16)
        hash = hash_chunk(chunk)
        chunk = encrypt_chunk(chunk, key)
        chunks.append((hash, key, chunk))

    return chunks

def upload_chunks(chunks: list[tuple[bytes,bytes,bytes]], buckets: list[Bucket]):
    # list[dict[Bucket, tuple[hash, key, data]]]
    for bucket in buckets:
        to_upload = []
        for c in bucket.chunks:
            chunk = [x for x in chunks if x[0] == c][0]
            #chunk = encrypt_chunk(chunk[2], chunk[1])
            to_upload.append(chunk[2])
        bucket.upload(to_upload)

def decrypt_chunk(chunk: bytes, key: bytes) -> bytes:
    iv = 16 * b'\x00'
    decryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).decryptor()
    return decryptor.update(chunk) + decryptor.finalize()

def download_chunks(download: list[dict[Bucket, tuple[bytes, bytes]]], reconstruct: list[bytes]) -> bytes:
    # list[dict[Bucket, tuple[hash, key]]]
    # list[hash]
    output = {} # dict[hash, data]
    for bucket, refs in download:
        chunks = bucket.download()
        for i in range(len(chunks)):
            chunk = chunks[i]
            chunk = decrypt_chunk(chunk, refs[i][1])
            assert hash_chunk(chunk) == refs[i][0]
            output[refs[i][0]] = chunk

    # Reorder according to order of references
    reordered = []
    for reference in reconstruct:
        reordered.append(output[reference])
    
    return b''.join(reordered)


