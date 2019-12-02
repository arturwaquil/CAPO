contours.reverse()

# Calculo da qtd de colunas
num_colunas = 1
x_ant, _, _, _ =  cv2.boundingRect(contours[0])
x, _, _, _ =  cv2.boundingRect(contours[1])
while( x > x_ant):
	x_ant = x
	num_colunas += 1
	x, _, _, _ =  cv2.boundingRect(contours[num_colunas])

# Num de linhas
num_linhas = len(contours) / num_colunas

# Montagem da tabela
tabela = []
linha = []
for c in contours:
	if(len(linha) < num_colunas):
		linha.append(c)
	else:
		linha = lista[1:] # Retira o primeiro elemento, pois a primeira coluna eh das alternativas
		tabela.append(linha)
		linha = []

tabela = tabela[1:]  # Retira a primeira linha, pois ela contem as celulas das questoes
		

# Montagem do gabarito
gabarito = []
for coluna in range(num_colunas):
	resposta = -1
	mediaCor_resposta = 255

	for linha in range(num_linhas):
		celula = tabela[linha][coluna]
		x, y, w, h = cv2.boundingRect(celula)
		sum = 0
		pixels = 0

		#Percorre os pixels da celula
		for i in range(y, y+h):
			for j in range(x, x+w):
				sum += gabGrey[i][j]
				pixels += 1

		if sum/pixels < mediaCor_resposta:
			mediaCor_resposta = sum/pixels
			resposta = linha

	gabarito.append(resposta)