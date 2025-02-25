# Imports
import cv2 as cv
import os

# Array of tests to do
tests = ["OCR", "RFID", "Servo"]

# A loop to select a test
def selectTest():
    print("Select a test to run:")
    for test in tests:
        print(tests.index(test), ":", test)

    selectedTest = input()

    try:
        testIndex = tests.index(selectedTest)
        print("Selected", selectedTest)
        if selectedTest == "OCR":
            OCRTest()
        elif selectedTest == "RFID":
            RFIDTest()
        elif selectedTest == "Servo":
            ServoTest()
    except:
        print("That is not an option")
        selectTest()

# OCR test function
def OCRTest():
    pass

# RFID test function
def RFIDTest():
    pass

# Servo test function
def ServoTest():
    pass