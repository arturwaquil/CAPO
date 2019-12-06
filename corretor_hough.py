import numpy as np
import cv2
import copy

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

gabOrig = cv2.imread('imgs/gab-bolinhas.jpg')
gabGrey = cv2.cvtColor(gabOrig, cv2.COLOR_BGR2GRAY)
gabCanny = cv2.Canny(gabGrey, 100, 200) 

imshow("canny", gabCanny)

lines = cv2.HoughLines(gabCanny, 1, np.pi/180, 150)
lines = clearLines(lines)

# lines[0] -> primeira linha
# lines[i][0] -> d
# lines[i][1] -> theta


horLines = []
verLines = []
for line in lines:
	if line[1] < np.pi/4 or line[1] > np.pi*3/4:
		verLines.append(line)
	else:
		horLines.append(line)

		
''' Print linhas '''
todas = copy.copy(gabOrig)
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

	cv2.line(todas, (x1,y1), (x2,y2), (255,0,0), 2, cv2.LINE_AA)

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

	cv2.line(todas, (x1,y1), (x2,y2), (255,0,0), 2, cv2.LINE_AA)

imshow("todas", todas)
		


# Mediana do angulo das linhas horizontais 
angulos = []
for line in range(int(0.3*len(horLines))):
	angulos.append(horLines[line][1])

angulos.sort()
mediana_hor = angulos[int( len(angulos)/2 )]

# Mediana do angulo das linhas verticais
angulos = []
for line in range(int(0.3*len(verLines))):
	angulos.append(verLines[line][1])

angulos.sort()
mediana_ver = angulos[int( len(angulos)/2 )]

# Eliminação de duplicados: se as linhas se intersectam dentro da imagem, são duplicadas (ou uma delas é gerada por outliers)
altura, largura, _ = gabOrig.shape

		# HORIZONTAIS
horLinesAux = []
for linha1 in horLines:
	d1 = linha1[0]
	t1 = linha1[1]
	manter = True

	for linha2 in horLines:
		d2 = linha2[0]
		t2 = linha2[1]

		if t1 != t2: # Se nao forem paralelas 
			A = np.asmatrix([[np.cos(t1), np.sin(t1)],[np.cos(t2), np.sin(t2)]])
			b = np.asmatrix([[d1],[d2]])
			coord = np.linalg.inv(A) * b
			coord.resize(2)

			if 0 <= coord[0] <= largura and 0 <= coord[1] <= altura: #Se intersecao esta dentro da imagem
				if abs(t1 - mediana_hor) > abs(t2 - mediana_hor):    #Se a linha estiver mais "longe" da mediana do que alguma outra linha, 
					manter = False									 #eliminamos ela

	if manter:
		horLinesAux.append(linha1)

horLines = horLinesAux


		# VERTICAIS
verLinesAux = []
for linha1 in verLines:
	d1 = linha1[0]
	t1 = linha1[1]
	manter = True

	for linha2 in verLines:
		d2 = linha2[0]
		t2 = linha2[1]

		if t1 != t2: # Se nao forem paralelas 
			A = np.asmatrix([[np.cos(t1), np.sin(t1)],[np.cos(t2), np.sin(t2)]])
			b = np.asmatrix([[d1],[d2]])
			coord = np.linalg.inv(A) * b
			coord.resize(2)

			if 0 <= coord[0] <= largura and 0 <= coord[1] <= altura: #Se intersecao esta dentro da imagem
				if abs(t1 - mediana_ver) > abs(t2 - mediana_ver):    #Se a linha estiver mais "longe" da mediana do que alguma outra linha, 
					manter = False									 #eliminamos ela

	if manter:
		verLinesAux.append(linha1)

verLines = verLinesAux



verLines.sort(key = lambda line: abs(line[0]))
horLines.sort(key = lambda line: abs(line[0]))

# Eliminacao de linhas muito proximas 
dist_min_etre_linhas = 25
	
	# Hor
horLinesManter = []
for i in range(len (horLines)):
	horLinesManter.append(True)

for line1 in range(len(horLines)):
	if horLinesManter[line1]:	# Se a linha ja nao foi eliminada
		for line2 in range(line1+1, len(horLines)):
			if abs(horLines[line1][0] - horLines[line2][0]) < dist_min_etre_linhas:    # Se diferenca for menor que a dist_min, 
				horLinesManter[line2] = False												#elimina a linha com menos votos

removidos = 0
for i in range(len(horLinesManter)):
	if not horLinesManter[i]:   # Se false, isto eh, nao queremos manter a linha
		del(horLines[i-removidos]) #Retiramos a linha da lista 
		removidos += 1
			
	# Vert
verLinesManter = []
for i in range(len (verLines)):
	verLinesManter.append(True)

for line1 in range(len(verLines)):
	if verLinesManter[line1]:	# Se a linha ja nao foi eliminada
		for line2 in range(line1+1, len(verLines)):
			if abs(verLines[line1][0] - verLines[line2][0]) < dist_min_etre_linhas:    # Se diferenca for menor que a dist_min, 
				verLinesManter[line2] = False												#elimina a linha com menos votos

removidos = 0
for i in range(len(verLinesManter)):
	if not verLinesManter[i]:   # Se false, isto eh, nao queremos manter a linha
		del(verLines[i-removidos]) #Retiramos a linha da lista 
		removidos += 1
			
			
			
# Eliminacao da primeira linha e primera coluna (para nao ler as questoes e as alternativas)
verLines.sort(key = lambda line: abs(line[0]))
horLines.sort(key = lambda line: abs(line[0]))
verLines = verLines[1:]
horLines = horLines[1:]


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



# Monta o gabarito
gabarito = []
for coluna in range(len(verLines)-1):
	resposta = -1
	qtd_resposta = 0

	for linha in range(len(horLines)-1):
		coord_sup_esq = tabela[linha][coluna]
		coord_inf_dir = tabela[linha+1][coluna+1]
		sum = 0

		#Percorre os pixels da celula
		for i in range(int(coord_sup_esq[1]), int(coord_inf_dir[1])):
			for j in range(int(coord_sup_esq[0]), int(coord_inf_dir[0])):
				if(gabCanny[i][j] == 255):
					sum += 1

		if sum > qtd_resposta:
			qtd_resposta = sum
			resposta = linha

	gabarito.append(resposta)

''' Print do gabarito '''
print(gabarito)