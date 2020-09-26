"""
qrcomm-py is a Python implementation of a QR-code communication protocol.
"""

import qrcode
from PIL import Image
import secrets

from hmac import compare_digest
from Crypto.Cipher import AES, Salsa20, ChaCha20, XChaCha20
import hashlib

hashes = {
	"BLAKE2b": [hashlib.blake2b, 0]
}
ciphers = {
	"AES": [AES, 1],
	"Salsa20": [Salsa20, 2],
	"ChaCha20": [ChaCha20, 3],
	"XChaCha20": [XChaCha20, 4],
}

qr_max_bytes = 1273	# Maximum bytes supported by a v40 QR code
qr_data_bytes = 1024	# Number of bytes to encode.
			# Number of bytes for the hash (64 bytes = 512 bits)
			
			# When sending data the first (0th) frame must be a header frame.
			# A header frame uses the frametype	0x0000
			# A seed frame uses the frametype	0x0001
			# A message frame uses the frametype	0x0002
			
			# With the default options a single frame can contain 1024 data bytes,
			# plus a 32-bit frametype (appended to the plaintext before encryption)
			# plus a 512-bit HMAC hash of the ciphertext, with the encryption key and nonce as the MAC key,
			# plus a 512-bit HMAC hash of the plaintext (including frametype) with the encryption key and nonce as the MAC key,
			# plus a 128-bit frame index (unencrypted; each QR code represents 1 frame).
			
			# the nonce is simply the frame index, XORd with an IV defined in a seed frame.
			# The seed frame's IV is chosen randomly using a secure RNG.
			# The data bytes are XORd with the IV before encryption.
			
			# All encryption is done with a stream cipher or a block cipher in CTR mode.
			# The default cipher is AES with a 256-bit key, and BLAKE2b as the hashing algorithm.
			# Encryption algorithms may be cascaded. The algorithm(s) used are defined in the header frame.
			# Hashing algorithms may not be cascaded, but can be chosen freely.
			# So far only BLAKE2b is implemented, but that's trivial to fix.
			
			# Hashes use KMAC for hashes that support it without compromising security, otherwise HMAC.
			# I let hashlib decide which MAC construction to use, since this is a messaging library, not a crypto library.
			
			# There can be multiple seed and header frames within data. The reason for this is to reinitialize the cryptography,
			# if necesary. This allows encrypting unlimited amounts of data (as if 2**128 bits isn't enough).
			# Seed frame reinitialization is only useful if a suitable TRNG is available.
			# The seed frame contains a 1024-byte IV.
			# The IV is sent the same as any other message, except within a seed frame (frametype 0x0002).
			# If no seed frame is sent the IV defaults to a string of zero-bits.
			# A seed frame is decrypted using the IV prior to receiving the seed frame. The first seed frame is decrypted
			# with an IV being all zero-bits.

qr = qrcode.QRCode(
    version=40,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data()
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("qr.png")

class qrcomm:
	def qrcomm_init(self):
		pass
	"""
	`msg` is a bytes object containing the message to send.
	`key` is an encryption key. If a password is used it must
		be expanded before using it here. PBKDF2 is recommended.
	`crypto_options` is a 32-bit int.
	`hash_options` is a 32-bit int.
	"""
	def build_message(msg, key, crypto_options=0, hash_options=0):
		iv = b'\x00' * 1024
		frames = []
		crypto_alg = parse_crypto(crypto_options)
		hash_alg = parse_hash(hash_options)
		new_iv = secrets.token_bytes(1024) # Seed frame IV
		frames += [build_seed_frame(new_iv, key, 0, iv, crypto_alg, hash_alg)]
		iv = new_iv # Now that the seed frame has defined an IV we must use it
		frames += [build_header_frame(msg, key, 1, iv, crypto_alg, hash_alg)]
		for ix in range(0, len(msg), qr_data_bytes):
			frames += [build_frame(msg, key, 2, 2+ix, iv, crypto_alg, hash_alg)]
	def build_frame(msg, key, frametype, ix, iv, crypto_alg, hash_alg):
		plaintext = list(msg) # msg length must equal 1024 bytes exactly
		plaintext += list(frametype.to_bytes(4, 'big'))
		for a in range(qr_data_bytes):
			plaintext[a] ^= iv[a]
		plaintext = bytes(plaintext)
		crypto_alg.new(
	def build_header_frame(msg, key, ix, iv, crypto_alg, hash_alg):
		# a header frame contains the number of frames that will be sent.
		# The count must also include any seed frames to be sent.
		# If another header frame is to be sent it must include
		# every frame up to (and including) the next header frame.
		pass
	def build_seed_frame(msg, key, ix, iv, crypto_alg, hash_alg):
		pass
