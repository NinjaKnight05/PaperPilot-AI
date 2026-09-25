# import fitz
# doc = fitz.open("sample.pdf")
# page = doc[0]
# print(page)
# pix = page.get_pixmap()
# pix.save("page1.png")

# import pytesseract
# from PIL import Image
# pytesseract.pytesseract.tesseract_cmd = r"D:\OCR\tesseract.exe"
# image = Image.open("page1.png")
# text = pytesseract.image_to_string(image)
# print(text)

import io
import fitz
import pytesseract
from PIL import Image



def ocr_page(page, zoom: float = 2.0)-> str:
    matrix = fitz.Matrix(zoom,zoom)
    pix = page.get_pixmap(matrix=matrix)
    image_byte = pix.tobytes("png")

    image = Image.open(io.BytesIO(image_byte))
    text = pytesseract.image_to_string(image)

    return text