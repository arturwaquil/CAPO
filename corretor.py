import numpy as np
import cv2
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--numFotos', type=int,  help='Quantidade de fotos para corrigir', default=6)
parser.add_argument('-e', '--extensao', type=str,  help='Extensao das fotos (sem o ponto)', default='jpg')
args = parser.parse_args()


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

def is_valid_contour(c):
	x, y, w, h = cv2.boundingRect(c)
	area = w*h - (w*h % 1000)

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

def detecta_contornos(imgOrig, writename=None):
	imshow("original", imgOrig)
	imgGray = cv2.cvtColor(imgOrig, cv2.COLOR_BGR2GRAY); imshow("grayscale", imgGray)
	# limiarizacao adaptativa devido a variacao de iluminacao na imagem
	imgThres = cv2.adaptiveThreshold(imgGray,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY_INV,41,2); imshow("threshold", imgThres)
	if writename is not None:
		cv2.imwrite('threshold/' + writename, imgThres)

	vert_kernel_length = 5#imgThres.shape[0]//50
	hori_kernel_length = 5#imgThres.shape[1]//50

	# operacao morfologica para detectar retas verticais na imagem, usando um kernel (1 x vert_kernel_length)
	vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vert_kernel_length))
	temp = cv2.erode(imgThres, vert_kernel, iterations=3)
	imgVertLines = cv2.dilate(temp, vert_kernel, iterations=3)
	imshow("vert", imgVertLines)

	# operacao morfologica para detectar retas horizontais na imagem, usando um kernel (hori_kernel_length x 1)
	hori_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (hori_kernel_length, 1))
	temp = cv2.erode(imgThres, hori_kernel, iterations=3)
	imgHoriLines = cv2.dilate(temp, hori_kernel, iterations=3)
	imshow("hori", imgHoriLines)

	# junta as verticais e horizontais
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
	imgTable = imgVertLines + imgHoriLines
	imgTable = cv2.erode(~imgTable, kernel, iterations=2)
	_, imgTable = cv2.threshold(imgTable, 128, 255, cv2.THRESH_BINARY_INV); imshow("table", imgTable)
	if writename is not None:
		cv2.imwrite('table/' + writename, imgTable)

	contours, _ = cv2.findContours(imgTable, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

	# imprime os contornos detectados na imagem
	imgFirstContours = desenha_contornos(contours, imgOrig)
	imshow("first contours", imgFirstContours)

	if writename is not None:
		cv2.imwrite("firstcontours/" + writename, imgFirstContours)

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
	imgContours = desenha_contornos(contours, imgOrig)
	imshow("contours", imgContours)

	if writename is not None:
		cv2.imwrite("contours/" + writename, imgContours)

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
		col = temp[:6]
		# ordena pelo y
		col.sort(key=lambda c:cv2.boundingRect(c)[1])
		col = col[1:]
		temp = temp[6:]
		tabela.append(col)
	tabela = tabela[1:]

	# inverte ordem de linhas e colunas
	# newTabela = []
	# for i in range(num_linhas):
	# 	linha = []
	# 	for j in range(num_colunas):
	# 		linha.append(tabela[j][i])
	# 	newTabela.append(linha)
	# tabela = newTabela

	return tabela

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

def detecta_respostas(filename):

	img = cv2.imread(filename)
	_, contours = detecta_contornos(img, writename=filename)

	imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	imgCanny = cv2.Canny(imgGray, 100, 200); imshow("canny", imgCanny)

	num_linhas, num_colunas = dimensoes_tabela(contours)
	num_linhas -= 1
	num_colunas -= 1
	tabela = monta_tabela(contours)

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

	return respostas

def testa_imgs():
	import sys, os
	for root, _, files in os.walk('imgs/'):
		for file in files:
			print(file + ': ', end='')
			testa('imgs/' + file)

def testa(filename):
	try:
		gabarito = detecta_respostas(filename)
		print(gabarito)
	except:
		print('erro no arquivo ' + filename)

if __name__ == "__main__":
	nomeGab = 'teste/' + 'gabarito.' + args.extensao
	nomeAluno = 'teste/' + 'aluno'

	gabarito = detecta_respostas(nomeGab)
	respostas = []

	for i in range(args.numFotos):
		nome = nomeAluno + str(i+1) + '.' + args.extensao
		respostas.append(detecta_respostas(nome))
		
	for aluno in range(len(respostas)):
		resp = respostas[aluno]
		acertos = 0
		print('\nAluno ' + str(aluno+1) + ':')
		
		for questao in range(len(resp)):
			if gabarito[questao] == resp[questao]:
				resultado = 'correto'
				acertos += 1
			else:
				resultado = 'errado'
			print('Questao ' + str(questao+1) + ': ' + resultado)	
		
		print('Nota: ' + str(acertos) + '/' + str(len(resp)))
