# This is the final build file #

# String.prototype.ljust(64, " ")

# ---------- Imports ---------- #

import cv2 as cv
import numpy as np
import RPi.GPIO as GPIO

from time import sleep
from gpiozero import AngularServo
from mfrc522 import SimpleMFRC522
from ecies.utils import generate_key
from ecies import encrypt, decrypt

import pytesseract, time, re, socket, binascii

GPIO.setwarnings(False)

# ---------- Constant Variables ---------- #

# Constant for the escape key when using cv.waitKey
ESC_KEY = 27

# Constant for the amount of money charged when exiting (in $)
CHARGE_RATE = 5

# Constants for the slicing dimensions for OCR
OCR_SLICE_WIDTH = 700
OCR_SLICE_HEIGHT = 200

# Constant for UID file
REGISTERED_CARDS_PATH = "/home/username/Parcark/registered_cards.txt"

# ----- Socket Constants ----- #

HEADER = 64                         # Header message size
PORT = 50512                        # Server port
FORMAT = "utf-8"                    # encode/decode format
DISCONNECT_MESSAGE = "DISCONNECT"   # Disconnect message
SERVER = "10.76.95.177"                # Sever IP Address
ADDR = (SERVER, PORT)               # IP-Port tuple

# Screw you Python. Only you and Lua are properly different and I let C++ because it's actually a good language
null = None

# ---------- External Peripheral Creation ---------- #

# Create servo object
servo = AngularServo(18, min_pulse_width = 0.0005, max_pulse_width = 0.0025)

# Create rfid object
rfid = SimpleMFRC522()

# Create camera object
camera = cv.VideoCapture(0)
if not camera.isOpened():
    print("Error: Could not open camera.")
    exit()

# ---------- Main functions ---------- #

def init():
    SocketHandler.init()
    RFIDTagRegister.init()


    print("testing time :D")

    log("init", "Entering main loop.")
    mainLoop()

    cleanUpAndExit()

def mainLoop():
    #licensePlate = getOCRResult()

    # Fake a license plate for testing
    licensePlate = "ABCDEF"

    if licensePlate:
        print("Please present your RFID tag")
        rfidTag = getRFID()
        if RFIDTagRegister.verifyTag(rfidTag):
            print("Your tag has been verified")
            # The integer casts here are safe because they've already been verified
            if LPDatabase.query(licensePlate):
                LPDatabase.pull(licensePlate, int(rfidTag[0]))
                print("Have a nice day! :D")
            else:
                LPDatabase.push(licensePlate, int(rfidTag[0]), int(rfidTag[1]))
                print()
        else:
            print("This tag has not been registered or has a corrupted format\nWould you like to (re)register it now? [y/n]")
            ans = input().lower()
            if ans == "y":
                print("Please enter your PIN")
                pin = getValidPin()

                print("Enter the card\'s initial balance")
                mons = getValidInitial()

                RFIDTagRegister.registerCard(rfidTag[0], pin, mons)
                print("Your tag has now been registered.\nPlease rescan your card to enter")
            else:
                print("LEAVE")
        
        # Return to null because we only want to test once
        licensePlate = null

def getValidPin():
    pin = null
    while True:
        try:
            pin = input()
            if len(pin) == 4:
                pin = int(pin)

                break
            else:
                print("PIN must be 4 characters in length")
            
        except ValueError:
            print("That is not a number")
    return pin

def getValidInitial():
    initial = null
    while True:
        try:
            initial = input()
            initial = int(initial)
            break
        except ValueError:
            print("That is not a number")
    return initial


# ----- This code is blocking ----- #
def getOCRResult():
    sameResultCount = 0
    ocrRes = null

    while True:
        # Get cam frame
        img = getCameraFrame(False)

        if img is null:
            continue



        # Modify frame for better reading
        height, width = img.shape[:2]
    
        # Calculate center coordinates
        mid_x, mid_y = width // 2, height // 2
        
        # Calculate crop boundaries
        cw2, ch2 = OCR_SLICE_WIDTH // 2, OCR_SLICE_HEIGHT // 2
        x_start = mid_x - cw2
        x_end = mid_x + cw2 + (OCR_SLICE_WIDTH % 2)  # Handles odd widths
        y_start = mid_y - ch2
        y_end = mid_y + ch2 + (OCR_SLICE_HEIGHT % 2)  # Handles odd heights
        
        # Perform the crop
        img = img[y_start:y_end, x_start:x_end]



        # Turn the image into a ndarray object
        # This is NumPy's class for array manipulation
        img = np.array(img)

        # Create an empty array using the dimensions of the img
        img_empty = np.zeros((img.shape[0], img.shape[1]))

        # Apply various image modifactions to make text reading easier

        # Convert image from normal colorspace to grayscale colorspace
        img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        # Applies normalisation. Since I can't understand the documentation for this, I assume that it means mapping the colors of the array
        img = cv.normalize(img, img_empty, 0, 255, cv.NORM_MINMAX)
        # According to the docs, applies a threshold mechanic, as to effectively limit pixels colors whose values are to small or large
        img = cv.threshold(img, 100, 255, cv.THRESH_BINARY)[1]
        # This applies a Gaussian filter. Magic really.
        img = cv.GaussianBlur(img, (1, 1), 0)

        # Show the fully modified image
        cv.imshow("Camera Vision", img)

        # Obtain the raw processed text
        text = pytesseract.image_to_string(img)

        # Use RegEx to filter the output so only characters we expect are outputed
        filteredText = "".join(re.findall("[0-9a-zA-Z-]", text))

        if ocrRes == filteredText and ocrRes != "" and len(filteredText) == 6:
            sameResultCount = sameResultCount + 1
        else:
            ocrRes = filteredText
            sameResultCount = 0

        if sameResultCount == 5:
            break
        
        print(f"result: {ocrRes}, same res count: {sameResultCount}")

        if exitOnEsc():
            break
    
    print(f"final result: {ocrRes}")
    return ocrRes

def getRFID():
    tagID, tagText = rfid.read()
    return (tagID, tagText)

# ---------- License Plate Database System ---------- #

class LPDatabase:
    lpDict = {}

    @staticmethod
    def pull(uid, pin):
        if uid in LPDatabase.lpDict:
            val = LPDatabase.lpDict[uid]
            # Pop deletes an entry in a dictionary
            LPDatabase.lpDict.pop(uid)

            log("LPDatabase", f"Attempting to charge {uid}")
            sckt_msg = SocketHandler.send(f"{DatabaseCommands.TRYCHARGE}:{uid}:{pin}:{CHARGE_RATE}")
            if sckt_msg == "NULL":
                print("User account empty")
            else:
                print("Charge successful")

            return val
        else:
            raise Exception("Unable to fetch time from non-existent entry")

    @staticmethod
    def push(uid, pin, inital):
        if uid in LPDatabase.lpDict:
            raise Exception("A duplicate license plate entry cannot exist")
        else:
            LPDatabase.lpDict[uid] = time.strftime("%H:%M:%S")

            log("LPDatabase", f"Adding license plate '{uid}' to register")
            SocketHandler.send(f"{DatabaseCommands.REGISTERCARD}:{uid}:{pin}:{inital}")
    
    @staticmethod
    def query(uid):
        return uid in LPDatabase.lpDict

# ---------- Socket Handler Class ---------- #

class SocketHandler:
    clientSocket = null
    publicKey = null

    @staticmethod
    def init():
        log("SocketHandler", "Initalizing socket connection...")
        SocketHandler.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        SocketHandler.clientSocket.connect(ADDR)
        log("SocketHandler", "Socket connected")

        public_key = SocketHandler.receive()

        log("SocketHandler", "Received public key")
        hexedKey = public_key.split(":")[1]
        print("Public key: " + hexedKey)
        SocketHandler.publicKey = binascii.unhexlify(hexedKey)

    # Be aware that this method blocks while it waits for server to respond
    # This shouldn't be an issue as the server will always respond with something but it's good to know
    @staticmethod
    def send(send_msg):
        msg_bytes = encrypt(SocketHandler.publicKey, send_msg.encode(FORMAT))
        send_msg_length = len(msg_bytes)
        send_length = str(send_msg_length).encode(FORMAT)
        send_length += b" " * (HEADER - len(send_length))
        SocketHandler.clientSocket.send(send_length)
        SocketHandler.clientSocket.send(msg_bytes)
        log("SocketHandler", f"Sent message to '{SERVER}' on port '{PORT}': {send_msg}")

        receive_msg = SocketHandler.receive()
        log("SocketHandler", f"Received message from {SERVER} on port {PORT}: {receive_msg}")

        if send_msg == DISCONNECT_MESSAGE:
            return null

        receive_key = SocketHandler.receive()
        
        log("SocketHandler", "Received public key")
        hexedKey = receive_key.split(":")[1]
        print("Public key: " + hexedKey)
        SocketHandler.publicKey = binascii.unhexlify(hexedKey)

        return receive_msg
    
    @staticmethod
    def receive():
        msg_length = SocketHandler.clientSocket.recv(HEADER).decode(FORMAT)
        if msg_length:
            return SocketHandler.clientSocket.recv(int(msg_length)).decode(FORMAT)
        else:
            raise Exception("Receiving length doesn't exist")

    @staticmethod
    def disconnect():
        SocketHandler.send(DISCONNECT_MESSAGE)
        log("SocketHandler", "Disconnected from socket")

class DatabaseCommands:
    TRYCHARGE = "TRYCHARGE"
    GETBANKBALANCE = "GETBANKBALANCE"
    REGISTERCARD = "REGISTERCARD"
    DISCONNECT = DISCONNECT_MESSAGE

    GETPLATEINFO = 0xf
    SHUTDOWN = 0xff

# ---------- En/Decryption Class ---------- #

# That's just what I name classes that do both encryption and decryption
class DicryptionHandler:
    privateKey = null
    publicKey = null


    @staticmethod
    def generateKeys():
        log("DicryptionHandler", "Generating new key pair...")
        key = generate_key()

        DicryptionHandler.privateKey = binascii.hexlify(key.secret)
        DicryptionHandler.publicKey = binascii.hexlify(key.public_key.format(True))

        log("DicryptionHandler", "Generated new key pair")

    @staticmethod
    def encryptText(text):
        DicryptionHandler.generateKeys()

        log("DicryptionHandler", "Attempting to encrypt message")

        unhexedPublicKey = binascii.unhexlify(DicryptionHandler.publicKey)

        encryptedText = encrypt(unhexedPublicKey, text.encode(FORMAT))

        return binascii.hexlify(encryptedText)

    @staticmethod    
    def decryptText(text):
        log("DicryptionHandler", "Attempting to decrypt message")

        unhexedPrivateKey = binascii.unhexlify(DicryptionHandler.privateKey)

        unhexedText = binascii.unhexlify(text)

        decryptedText = decrypt(unhexedPrivateKey, unhexedText)

        return decryptedText.decode(FORMAT)

# ---------- RFID Tag Register ---------- #

class RFIDTagRegister:
    registeredCards = []
    rCardsFile = null

    @staticmethod
    def init():
        try:
            RFIDTagRegister.rCardsFile = open(REGISTERED_CARDS_PATH, "r")
            log("RFIDTagRegister", "Found registed cards file. Reading...")

            for line in RFIDTagRegister.rCardsFile:
                RFIDTagRegister.registeredCards.append(line)
            log("RFIDTagRegister", f"Loaded {len(RFIDTagRegister.registeredCards)} cards")
        except FileNotFoundError:
            RFIDTagRegister.rCardsFile = open(REGISTERED_CARDS_PATH, "w")
            log("RFIDTagRegister", "Registered cards file was not found. Generated new file.")
        except Exception as e:
            print(e)
    
    @staticmethod
    def verifyTag(tagTuple):
        print(tagTuple)

        splitValues = tagTuple[1].split(":")
        try:
            # 1, tag contents must be in the correct format and reletive type
            if len(splitValues[0]) != 4:
                # PIN must be 4 characters
                print("PIN not 4")
                return False

            pin = int(splitValues[0])
            inital = int(splitValues[1])
        # ValueError means the conversion of at least one of these failed
        except ValueError:
            print("conversion failed")
            return False

        # 2, tag must be in this register
        if not includes(RFIDTagRegister.registeredCards, str(tagTuple[0])):
            print("not in")

        return includes(RFIDTagRegister.registeredCards, str(tagTuple[0]))
        
    @staticmethod
    def isCardRegistered(uid):
        return includes(RFIDTagRegister.registeredCards, str(uid))
    
    @staticmethod
    def registerCard(uid, pin, initalCardValue):
        rfid.write(f"{pin}:{initalCardValue}")

        # This is required because the card could already be registered but the formatting could be corrupt
        if not includes(RFIDTagRegister.registeredCards, str(uid)):
            RFIDTagRegister.registeredCards.append(str(uid))

        log("RFIDTagRegister", f"Registered card with UID {uid}")
    
    @staticmethod
    def save():
        print(RFIDTagRegister.registeredCards)
        RFIDTagRegister.rCardsFile.write("\n".join(RFIDTagRegister.registeredCards))
        RFIDTagRegister.rCardsFile.close()
        log("RFIDTagRegister", "Saved registered cards")

# ---------- Quick functions for opening and closing the boomgate ---------- #

def openBoomGate():
    servo.angle = 90

def closeBoomGate():
    servo.angle = 0

# ---------- Util Functions ---------- #

# Frame getter
def getCameraFrame(resize = True, nW = 320, nH = 240):
    success, frame = camera.read()
    if success:
        if resize:
            frame = cv.resize(frame, (nW, nH))
        return frame

# Fn for cleaning up handles and resources
def cleanUpAndExit():
    # Release the camera capture
    camera.release()

    # Close all the OpenCV windows
    cv.destroyAllWindows()

    # Cleanup the GPIO system... whatever that actually does
    GPIO.cleanup()

    # Disconnect from the socket
    SocketHandler.disconnect()

    # Save the registered cards file
    RFIDTagRegister.save()

    # Exit the Python runtime
    exit()

# Fn for exiting on pressing the Escape key
def exitOnEsc():
    if cv.waitKey(1) == ESC_KEY:
        return True

# Pretty printing for 'debug' messages
def log(source, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{source}]: {msg}")

# JS Array.prototype.includes logic for Python because for some reason there is no native method for this
def includes(arr, val):
    try:
        return arr.index(val) >= 0
    except ValueError:
        return False









# Banish this to the Shadow Realm so everything works properly
init()