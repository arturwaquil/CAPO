import numpy as np
import cv2
import sys, os

save = True

def window_is_open(windowname):

	return True if cv2.getWindowProperty(windowname, cv2.WND_PROP_VISIBLE) >= 1 else False

def imshow(windowname, img, show=False):
	if save:
		cv2.imwrite(windowname + '.jpg', img)

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

	if area > 0 and w < 3*h and h < 3*w:
		return True
	else:
		return False

def desenha_contornos_retangulares(contours, img, cor=(255,0,0)):
	for c in contours:
		x, y, w, h = cv2.boundingRect(c)
		cv2.rectangle(img, (x,y), (x+w,y+h), cor, 3)

def dimensoes_tabela(contours):

	temp = contours.copy()
	# ordena pelo x
	temp.sort(key=lambda c:cv2.boundingRect(c)[0])

	leftmost = temp[0]
	x_leftmost, _, w_leftmost, _ = cv2.boundingRect(leftmost)

	num_linhas = 0
	for c in contours:
		x,_,_,_ = cv2.boundingRect(c)
		if x < x_leftmost + w_leftmost/2:
			num_linhas += 1

	num_colunas = int(len(contours)/num_linhas)

	return num_linhas, num_colunas


def detecta_contornos(imgOrig):
	imshow("original", imgOrig)
	imgGray = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2GRAY); imshow("grayscale", imgGray)
	# limiarizacao adaptativa devido a variacao de iluminacao na imagem
	imgThres = cv2.adaptiveThreshold(imgGray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,41,2); imshow("threshold", imgThres)

	kernel_length = 5

	# operacao morfologica para detectar retas verticais na imagem, usando um kernel (1 x kernel_length)
	vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_length))
	temp = cv2.erode(imgThres, vert_kernel, iterations=3)
	imgVertLines = cv2.dilate(temp, vert_kernel, iterations=3)
	imshow("vertical_lines", imgVertLines)

	# operacao morfologica para detectar retas horizontais na imagem, usando um kernel (kernel_length x 1)
	hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_length, 1))
	temp = cv2.erode(imgThres, hori_kernel, iterations=3)
	imgHoriLines = cv2.dilate(temp, hori_kernel, iterations=3)
	imshow("horizontal_lines", imgHoriLines)

	# junta as verticais e horizontais
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
	imgTable = imgVertLines + imgHoriLines
	imgTable = cv2.erode(~imgTable, kernel, iterations=2)
	_, imgTable = cv2.threshold(imgTable, 128, 255, cv2.THRESH_BINARY_INV)
	imshow("table", imgTable)

	contours, _ = cv2.findContours(imgTable, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# imprime os contornos detectados na imagem
	imgFirstContours = imgOrig.copy()
	cv2.drawContours(imgFirstContours, contours, -1, (255,0,0), 3)
	imshow("first_contours", imgFirstContours)

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
		if w*h < 2*contour_mode and w*h > 2*contour_mode/3:
			tempContours.append(c)
	contours = tempContours

	# imprime os contornos das celulas na imagem
	imgContours = imgOrig.copy()
	cv2.drawContours(imgContours, contours, -1, (255,0,0), 3)
	imshow("contours", imgContours)

	return imgContours, contours

def monta_tabela(contours):

	temp = contours.copy()
	# ordena pelo x
	temp.sort(key=lambda c:cv2.boundingRect(c)[0])

	leftmost = temp[0]
	x_leftmost, _, w_leftmost, _ = cv2.boundingRect(leftmost)

	num_linhas, num_colunas = dimensoes_tabela(contours)

	tabela = []
	for i in range(num_colunas):
		col = temp[:num_linhas]
		# ordena pelo y
		col.sort(key=lambda c:cv2.boundingRect(c)[1])
		col = col[1:]
		temp = temp[num_linhas:]
		tabela.append(col)
	tabela = tabela[1:]

	return tabela


def detecta_respostas(filename):

	img = cv2.imread(filename)
	_, contours = detecta_contornos(img)

	tabela = monta_tabela(contours)
	num_linhas = len(tabela[0])
	num_colunas = len(tabela)

	imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	imgCanny = cv2.Canny(imgGray, 100, 200); imshow("canny", imgCanny)

	respostas = []
	for coluna in range(num_colunas):
		resposta = -1
		qtd_brancos_resposta = 0

		for linha in range(num_linhas):
			celula = tabela[coluna][linha]
			x, y, w, h = cv2.boundingRect(celula)
			sum = 0

			#Percorre os pixels da celula
			for i in range(y, y+h):
				for j in range(x, x+w):
					if imgCanny[i][j] == 255:
						sum += 1

			if sum > qtd_brancos_resposta:
				qtd_brancos_resposta = sum
				resposta = linha

		respostas.append(resposta)

	return respostas, tabela

def marca_respostas(gabarito, respostas, tabela, img):
	num_linhas = len(tabela[0])
	num_colunas = len(tabela)

	corretas = []
	erradas = []
	for questao in range(len(respostas)):
		alt = respostas[questao]
		if gabarito[questao] == respostas[questao]:
			corretas.append(tabela[questao][alt])
		else:
			erradas.append(tabela[questao][alt])

	imgRespostas = img.copy()
	desenha_contornos_retangulares(corretas, imgRespostas, (0,255,0))
	desenha_contornos_retangulares(erradas, imgRespostas, (0,0,255))
	imshow("respostas", imgRespostas)
	return imgRespostas


def testa(filename):
	try:
		gabarito, tabela = detecta_respostas(filename)
		imgRespostas = marca_respostas(gabarito, gabarito, tabela, cv2.imread(filename))
	except:
		print('erro no teste do arquivo ' + filename)

def corrige_alunos(gab_name, dir_provas):

	try:
		os.chdir(dir_provas)
		cwd = os.getcwd()
	except:
		exit('erro na abertura do diretorio de provas')

	# cria lista das imagens a serem corrigidas
	entries = os.scandir()
	files = []
	[ files.append(e.name) for e in entries if e.name != gab_name and e.is_file() ]

	# detecta as respostas para a imagem do gabarito
	try:
		if save:
			dir_gab = os.path.splitext(gab_name)[0]
			if not os.path.exists(dir_gab):
				os.mkdir(dir_gab)
			os.chdir(dir_gab)
			gab_name = '../' + gab_name

		gabarito, _ = detecta_respostas(gab_name)

		if save: os.chdir('..')
	except:
		exit('erro na deteccao do gabarito')
	
	# roda o corretor para toda imagem no diretorio, exceto o gabarito
	for file in files:

		try:
			print('\nAluno: ' + file)

			# cria diretorio onde serao salvas as imagens do aluno
			if save:
				dir_aluno = os.path.splitext(file)[0]
				if not os.path.exists(dir_aluno):
					os.mkdir(dir_aluno)
				os.chdir(dir_aluno)
				file = '../' + file

			respostas, tabela = detecta_respostas(file)
			
			acertos = 0
			for questao in range(len(respostas)):
				if gabarito[questao] == respostas[questao]:
					resultado = 'correto'
					acertos += 1
				else:
					resultado = 'errado'
				print('Questao ' + str(questao+1) + ':\t' + resultado)	
			
			print('Nota: ' + str(acertos) + '/' + str(len(respostas)))

			imgRespostas = marca_respostas(gabarito, respostas, tabela, cv2.imread(file))

			if save: os.chdir('..')

		except:
			print('erro no arquivo ' + file)
			if os.getcwd() != cwd:
				os.chdir(cwd)
			continue

if __name__ == "__main__":
	corrige_alunos('gabarito.jpg', 'imgs/')
	# testa('imgs/gabarito.jpg')