from fashn_human_parser import FashnHumanParser
import cv2

print("Loading parser...")

parser = FashnHumanParser()

print("Parser loaded!")

image = cv2.imread("test.jpg")

result = parser(image)


print(result)