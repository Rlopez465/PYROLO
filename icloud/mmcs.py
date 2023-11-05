from dataclasses import dataclass
import hashlib
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import random
import requests


CHUNK_SIZE = 0x500000

MMCS_HEADERS = {
    "x-apple-mmcs-plist-version": "v1.0",
    "x-apple-mmcs-proto-version": "5.0",
    "x-apple-mmcs-plist-sha256": "fvj0Y/Ybu1pq0r4NxXw3eP51exujUkEAd7LllbkTdK8=",
}

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
class Chunk:  # Always encrypted if data contained, turn back into whole file when decrypting
    data: bytes | None = None  # None when this is just a chunk reference
    key: bytes | None = None  # None when this is just a chunk reference
    hash: bytes = b""


@dataclass
class Bucket:  # Also known as a container
    name: str
    token: str
    url: str
    headers: dict[str, str]
    chunks: list[Chunk]  # list[hash]

    def upload(self, data):
        return requests.put(self.url, data=data, headers=self.headers, verify=False)

    def download(self) -> list[bytes]:
        pass

def hash_chunk(chunk: bytes) -> bytes:
    return b"\x81" + hashlib.sha256(hashlib.sha256(chunk).digest()).digest()[:20]


def encrypt_chunk(chunk: bytes, key: bytes) -> bytes:
    iv = 16 * b"\x00"
    encryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).encryptor()
    return encryptor.update(chunk) + encryptor.finalize()


def chunk(data: bytes) -> list[Chunk]:
    chunks = []
    for i in range(0, len(data), CHUNK_SIZE):
        chunk = data[i : i + CHUNK_SIZE]
        key = random.randbytes(16)
        hash = hash_chunk(chunk)
        chunk = encrypt_chunk(chunk, key)
        chunks.append(Chunk(data=chunk, key=key, hash=hash))
    return chunks


@dataclass
class UploadReceipt:
    md5: bytes
    headers: dict[str, str]
    size: int


def upload_chunks(chunks_to_upload: list[Chunk], buckets: list[Bucket]) -> list[UploadReceipt]:
    receipts = []
    for bucket in buckets:
        to_upload = []
        for bucket_chunk in bucket.chunks:
            # Get the chunk from the list of chunks to upload that matches the hash
            chunk = [
                chunk for chunk in chunks_to_upload if chunk.hash == bucket_chunk.hash
            ][0]
            to_upload.append(chunk.data)
        to_upload = b"".join(to_upload)
        resp = bucket.upload(to_upload)
        receipts.append(
            UploadReceipt(hashlib.md5(to_upload).digest(), dict(resp.headers), len(to_upload))
        )

    return receipts


# def decrypt_chunk(chunk: bytes, key: bytes) -> bytes:
#     iv = 16 * b"\x00"
#     decryptor = Cipher(algorithms.AES(key), modes.CFB(iv)).decryptor()
#     return decryptor.update(chunk) + decryptor.finalize()


# def download_chunks(
#     download: list[tuple[Bucket, list[Chunk]]], reconstruct: list[Chunk]
# ) -> bytes:
#     # Mapping of Chunks to Buckets and order of Chunks
#     raise NotImplementedError()
#     # output = {} # dict[hash, data]
#     # for bucket, chunks in download:
#     #     downloaded_chunks = bucket.download()
#     #     for i in range(len(downloaded_chunks)):
#     #         chunk = downloaded_chunks[i]
#     #         chunk = decrypt_chunk(chunk, chunks[i].key)
#     #         assert hash_chunk(chunk) == refs[i][0]
#     #         output[refs[i][0]] = chunk

#     # # Reorder according to order of references
#     # reordered = []
#     # for reference in reconstruct:
#     #     reordered.append(output[reference])

#     # return b''.join(reordered)
