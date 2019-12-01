import numpy as np
import cv2

def window_is_open(windowname):

	return True if cv2.getWindowProperty(windowname, cv2.WND_PROP_VISIBLE) >= 1 else False

def imshow(windowname, img, show=False):
	if show:
		cv2.namedWindow(windowname, flags=cv2.WINDOW_GUI_NORMAL)    # hides status, toolbar etc.
		cv2.resizeWindow(windowname, img.shape[1], img.shape[0])

		while window_is_open(windowname):
			cv2.imshow(windowname, img)
			if cv2.waitKey(20) == 27:
				break

		cv2.destroyAllWindows()

def separa_linhas(lines):
	newLines = []
	for line in lines:
		newLines.append(line[0])

	horLines = []
	verLines = []
	for line in newLines:
		theta_deg = 180*line[1]/np.pi
		if theta_deg < 10 or theta_deg > 170:
			verLines.append(line)
		elif theta_deg > 80 and theta_deg < 100:
			horLines.append(line)

	verLines.sort(key = lambda line: abs(line[0]))
	horLines.sort(key = lambda line: abs(line[0]))

	return horLines, verLines

def infos_reta(d, theta):
	cos = np.cos(theta)
	sin = np.sin(theta)
	
	x0 = cos*d
	y0 = sin*d
	x1 = int(x0 + 10000*(-sin))
	y1 = int(y0 + 10000*(cos))
	x2 = int(x0 - 10000*(-sin))
	y2 = int(y0 - 10000*(cos))
	
	a = -np.tan((np.pi/2)-theta)
	b = y0 - a*x0
	
	return x1,y1,x2,y2,a,b

def desenha_linhas(verLines, horLines):
	# gabLinhas = np.zeros([gabOrig.shape[0], gabOrig.shape[1], 3], np.uint8)	
	gabLinhas = gabOrig.copy()

	for line in verLines:
		x1,y1,x2,y2,_,_ = infos_reta(line[0], line[1])
		cv2.line(gabLinhas, (x1,y1), (x2,y2), (255,255,0), 2, cv2.LINE_AA)

	for line in horLines:
		x1,y1,x2,y2,_,_ = infos_reta(line[0], line[1])
		cv2.line(gabLinhas, (x1,y1), (x2,y2), (255,0,0), 2, cv2.LINE_AA)

	imshow("linhas", gabLinhas)

def is_valid_contour(c):
	x, y, w, h = cv2.boundingRect(c)
	area = w*h - (w*h % 1000)

	# TODO: pensar em outras restricoes
	if area > 0 and w < 3*h and h < 3*w:
		return True
	else:
		return False

"""===== GABARITO ====="""

gabOrig = cv2.imread('imgs/' + filename); imshow("original", gabOrig)
gabGray = cv2.cvtColor(gabOrig, cv2.COLOR_BGR2GRAY); imshow("grayscale", gabGray)
# limiarizacao adaptativa devido a variacao de iluminacao na imagem
gabThres = cv2.adaptiveThreshold(gabGray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,41,2); imshow("threshold", gabThres)

# TODO: calibrar params
vert_kernel_length = gabThres.shape[0]//50
hori_kernel_length = gabThres.shape[1]//50

# operacao morfologica para detectar retas verticais na imagem, usando um kernel (1 x vert_kernel_length)
vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vert_kernel_length))
temp = cv2.erode(gabThres, vert_kernel, iterations=3)
gabVertLines = cv2.dilate(temp, vert_kernel, iterations=3)

# operacao morfologica para detectar retas horizontais na imagem, usando um kernel (hori_kernel_length x 1)
hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hori_kernel_length, 1))
temp = cv2.erode(gabThres, hori_kernel, iterations=3)
gabHoriLines = cv2.dilate(temp, hori_kernel, iterations=3)

# junta as verticais e horizontais
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))	# TODO: calibrar params
gabTable = gabVertLines + gabHoriLines
gabTable = cv2.erode(~gabTable, kernel, iterations=2)
_, gabTable = cv2.threshold(gabTable, 128, 255, cv2.THRESH_BINARY_INV); imshow("table", gabTable)

contours, _ = cv2.findContours(gabTable, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

# cria lista de areas (em degraus de 1000 unidades) dos contornos validos (i.e. nao muito pequenos e de lados nao muito distintos)
contour_areas = []
newContours = []
for c in contours:
	x, y, w, h = cv2.boundingRect(c)
	area = w*h - (w*h % 1000)

	if is_valid_contour(c):
		contour_areas.append(area)
		newContours.append(c)
contours = newContours

# detecta a moda das areas validas, que representa a area das celulas
contour_mode = max(set(contour_areas), key=contour_areas.count)

# imprime os contornos das celulas na imagem
gabContours = gabOrig.copy()
for c in contours:
	x, y, w, h = cv2.boundingRect(c)
	if w*h < 2*contour_mode and w*h > contour_mode/2:
		cv2.rectangle(gabContours, (x,y), (x+w,y+h), (255,0,0), 3)
imshow("contours", gabContours, True)
