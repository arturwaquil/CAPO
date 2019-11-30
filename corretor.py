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

def clearLines(lines):
	newLines = []
	for line in lines:
		newLines.append(line[0])

	return newLines

''' GABARITO '''

gabOrig = cv2.imread('imgs/print1.png')
gabGrey = cv2.cvtColor(gabOrig, cv2.COLOR_BGR2GRAY)
gabCanny = cv2.Canny(gabGrey, 100, 200) # TODO: params
# _, gabThres = cv2.threshold(gabGrey, 140, 255, cv2.THRESH_BINARY_INV)

# gabThres = cv2.adaptiveThreshold(gabGrey,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY_INV,11,2)
# gabCanny = cv2.morphologyEx(gabCanny, cv2.MORPH_CLOSE,  np.ones((7,7),np.uint8))

imshow("canny", gabCanny)

lines = cv2.HoughLines(gabCanny, 1, np.pi/180, 150)	# TODO: params
lines = clearLines(lines)

# lines[0] -> primeira linha
# lines[i][0] -> d
# lines[i][1] -> theta


horLines = []
verLines = []
for line in lines:
	if abs(line[1]) < np.pi/4:
		verLines.append(line)
	else:
		horLines.append(line)

verLines.sort(key = lambda line: abs(line[0]))
horLines.sort(key = lambda line: abs(line[0]))

# Eliminacao de linhas duplicadas e da primeira linha e primera coluna (para nao ler as questoes e as alternativas)
dist_min_etre_linhas = 5

horLinesAux = []
for i in range (1,len(horLines)):
	if abs(horLines[i][0] - horLines[i-1][0]) > dist_min_etre_linhas:    # Se diferenca for maior que a dist_min, mantem a linha
		horLinesAux.append(horLines[i])
horLines = horLinesAux
		
verLinesAux = []
for i in range (1,len(verLines)):
	if abs(verLines[i][0] - verLines[i-1][0]) > dist_min_etre_linhas:    # Se diferenca for maior que a dist_min, mantem a linha
		verLinesAux.append(verLines[i])		
verLines = verLinesAux
		
# Identificacao da tabela (intersecoes entre linhas)
tabela = []

for linha in horLines:
	intersecoes = []
	d1 = linha[0]
	t1 = linha[1]
	for coluna in verLines:
		d2 = coluna[0]
		t2 = coluna[1]
		A = np.asmatrix([[np.cos(t1), np.sin(t1)],[np.cos(t2), np.sin(t2)]])
		b = np.asmatrix([[d1],[d2]])
		coord = np.linalg.inv(A) * b
		coord.resize(2)
		intersecoes.append(coord)
	tabela.append(intersecoes)

''' Print intersecoes '''
#for i in range(len(horLines)):			
#	for j in range(len(verLines)):
#		coord = tabela[i][j] 
#		cv2.circle(gabOrig, (coord[0], coord[1]), 5, (0,255,0))


# Monta o gabarito
gabarito = []
for coluna in range(len(verLines)-1):
	resposta = -1
	mediaCor_resposta = 255

	for linha in range(len(horLines)-1):
		coord_sup_esq = tabela[linha][coluna]
		coord_inf_dir = tabela[linha+1][coluna+1]
		sum = 0
		pixels = 0

		#Percorre os pixels da celula
		for i in range(int(coord_sup_esq[1]), int(coord_inf_dir[1])):
			for j in range(int(coord_sup_esq[0]), int(coord_inf_dir[0])):
				sum += gabGrey[i][j]
				pixels += 1
		
		if sum/pixels < mediaCor_resposta:
			mediaCor_resposta = sum/pixels
			resposta = linha
	
	gabarito.append(resposta)

''' Print do gabarito '''
#print(gabarito)

''' Print linhas '''
for line in verLines:
	d = line[0]
	theta = line[1]

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

	cv2.line(gabOrig, (x1,y1), (x2,y2), (255,0,0), 2, cv2.LINE_AA)

for line in horLines:
	d = line[0]
	theta = line[1]
	
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

	cv2.line(gabOrig, (x1,y1), (x2,y2), (255,0,0), 2, cv2.LINE_AA)

imshow("img", gabOrig)