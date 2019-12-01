import numpy as np
import cv2

def window_is_open(windowname):

	return True if cv2.getWindowProperty(windowname, cv2.WND_PROP_VISIBLE) >= 1 else False

def imshow(windowname, img, show=True):
	if show:
		cv2.namedWindow(windowname, flags=cv2.WINDOW_GUI_NORMAL)    # hides status, toolbar etc.
		cv2.resizeWindow(windowname, img.shape[1], img.shape[0])

		while window_is_open(windowname):
			cv2.imshow(windowname, img)
			if cv2.waitKey(20) == 27:
				break

		cv2.destroyAllWindows()

def is_valid_contour(c):
	x, y, w, h = cv2.boundingRect(c)
	area = w*h - (w*h % 1000)

	# TODO: pensar em outras restricoes
	if area > 0 and w < 3*h and h < 3*w:
		return True
	else:
		return False

def desenha_contornos(contours, imgOrig):
	img = imgOrig.copy()
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		cv2.rectangle(img, (x,y), (x+w,y+h), (255,0,0), 3)
	return img


"""===== GABARITO ====="""

def run(filename, write=False):
	gabOrig = cv2.imread('imgs/' + filename); imshow("original", gabOrig)
	gabGray = cv2.cvtColor(gabOrig, cv2.COLOR_BGR2GRAY); imshow("grayscale", gabGray)
	# limiarizacao adaptativa devido a variacao de iluminacao na imagem
	gabThres = cv2.adaptiveThreshold(gabGray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,41,2); imshow("threshold", gabThres)

	# TODO: calibrar params
	vert_kernel_length = 5#gabThres.shape[0]//50
	hori_kernel_length = 5#gabThres.shape[1]//50

	# operacao morfologica para detectar retas verticais na imagem, usando um kernel (1 x vert_kernel_length)
	vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vert_kernel_length))
	temp = cv2.erode(gabThres, vert_kernel, iterations=3)
	gabVertLines = cv2.dilate(temp, vert_kernel, iterations=3)
	imshow("vert", gabVertLines)

	# operacao morfologica para detectar retas horizontais na imagem, usando um kernel (hori_kernel_length x 1)
	hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hori_kernel_length, 1))
	temp = cv2.erode(gabThres, hori_kernel, iterations=3)
	gabHoriLines = cv2.dilate(temp, hori_kernel, iterations=3)
	imshow("hori", gabHoriLines)

	# junta as verticais e horizontais
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))	# TODO: calibrar params
	gabTable = gabVertLines + gabHoriLines
	gabTable = cv2.erode(~gabTable, kernel, iterations=2)
	_, gabTable = cv2.threshold(gabTable, 128, 255, cv2.THRESH_BINARY_INV); imshow("table", gabTable)
	if write:
		cv2.imwrite('table/' + filename, gabTable)

	contours, _ = cv2.findContours(gabTable, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# imprime os contornos detectados na imagem
	gabFirstContours = desenha_contornos(contours, gabOrig)
	imshow("first contours", gabFirstContours)

	if write:
		cv2.imwrite("firstcontours/" + filename, gabFirstContours)

	# elimina contornos invalidos (i.e. muito pequenos ou de lados muito distintos)
	tempContours = []
	for c in contours:
		if is_valid_contour(c):
			tempContours.append(c)
	contours = tempContours

	# cria lista de areas (em degraus de 1000 unidades) dos contornos
	contour_areas = []
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		area = w*h - (w*h % 1000)
		contour_areas.append(area)

	# detecta a moda das areas, que representa a area das celulas da tabela
	contour_mode = max(set(contour_areas), key=contour_areas.count)

	# elimina contornos com tamanhos muito diferentes da moda
	tempContours = []
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		if w*h < 2*contour_mode and w*h > 2*contour_mode/3:	# TODO: calibrar params
			tempContours.append(c)
	contours = tempContours

	# imprime os contornos das celulas na imagem
	gabContours = desenha_contornos(contours, gabOrig)
	imshow("contours", gabContours)

	if write:
		cv2.imwrite("contours/" + filename, gabContours)

# import sys, os
# for root, _, files in os.walk('imgs/'):
# 	for file in files:
# 		try:
# 			run(file, write=True)
# 		except:
# 			pass
run('nic.jpg')