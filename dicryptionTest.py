# It's time for encryption :D

from ecies.utils import generate_key
from ecies import encrypt, decrypt
import binascii

FORMAT = "utf-8"

def fixBS(s):
    return str(s)

def genKeys():
    print("Generating keys...")
    key = generate_key()
    secretBytes = key.secret
    publicBytes = key.public_key.format(True)

    global privateKey
    global publicKey

    privateKey = binascii.hexlify(secretBytes)
    publicKey = binascii.hexlify(publicBytes)
    print("Keys generated")

def encryptText(text):
    print("Encrypting text...")
    publicHex = binascii.unhexlify((publicKey))

    encryptedText = encrypt(publicHex, text.encode(FORMAT))

    return binascii.hexlify(encryptedText)

def decryptText(text):
    print("Decrypting text...")
    privateHex = binascii.unhexlify((privateKey))

    encryptedHex = binascii.unhexlify((text))

    decryptedText = decrypt(privateHex, encryptedHex)

    return decryptedText.decode(FORMAT)

def dicryptionTest():
    print("Started dicryption test")
    print("Message to test:")
    msg = input()
    if msg == "":
        msg = "Failure"
    genKeys()
    print(f"Keys: Public: {privateKey}. Private: {publicKey}")
    encMsg = encryptText(msg)
    print(f"Encrypted message: {encMsg}")
    decMsg = decryptText(encMsg)
    print(f"Decrypted message: {decMsg}")



dicryptionTest()

