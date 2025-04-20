import cv2
import numpy as np

# 1) Cargo y suavizo
img = cv2.imread("taponesjuntos.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (5,5), 0)

# 2) (Opcional) cerrar pequeños agujeros para homogeneizar:
kernel = np.ones((7,7), np.uint8)
gray_closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
cv2.imshow("Gray cerrado (close)", gray_closed)
cv2.waitKey(0)

# 3) Otsu inverso
_, bin_otsu = cv2.threshold(gray_closed, 0, 255,cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
cv2.imshow("Umbral Otsu INV", bin_otsu)
cv2.waitKey(0)

# 4) Umbral manual (ajusta  cien entre 50–150)
th = 150
_, bin_manual = cv2.threshold(gray_closed, th, 255,cv2.THRESH_BINARY_INV)
cv2.imshow(f"Umbral manual INV = {th}", bin_manual)
cv2.waitKey(0)

# 5) Adaptativo media
bin_adapt_mean = cv2.adaptiveThreshold(gray_closed, 255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,blockSize=15,
C=3)
cv2.imshow("Umbral adaptativo MEAN", bin_adapt_mean)
cv2.waitKey(0)

# 6) Adaptativo gaussiano
bin_adapt_gauss = cv2.adaptiveThreshold(gray_closed, 255,
                                        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                        cv2.THRESH_BINARY_INV,
                                        blockSize=15,
                                        C=3)
cv2.imshow("Umbral adaptativo GAUSSIAN", bin_adapt_gauss)
cv2.waitKey(0)

cv2.destroyAllWindows()
