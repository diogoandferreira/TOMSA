
#TOMSA

Repositório para a criacao e desenvolvimento de um dashboard para visualização de trajetórias de logs de robots underwater.

No desenvolvimento da dashboard de visualização de dados de três robots, durante três missões diferentes, na Póvoa de Varzim.

Para correr a dashboard desenvolvida, deve ter em conta os passos abaixo mencionados:

Criar o Ambiente Virtual (caso ainda não exista)
	python3 -m venv .venv

Instalar as dependências
	pip install -r requirements.txt

Instalar depedências manual
	pip install dash dash-leaflet plotly pandas numpy scipy
 
Verificar dependências instaladas
	pip list		

Após o processo de instalação referido, seguem-se os seguintes passos:

	1- source .venv/bin/activate
	2- python3 app.py
	3- abrir o link http://127.0.0.1:8051/ numa página separada

Para o desenvolvimento desta dashboard, são necessárias as seguintes bibliotecas Python, listadas no ficheiro requirements.txt:
 
dash: Framework principal para a criação do dashboard interativo.
dash-leaflet: Componente para integração do mapa 2D (OpenSeaMap).
plotly: Biblioteca gráfica para renderização da trajetória e eixos em 3D.
pandas: Manipulação e estruturação dos dados dos logs ROS (ficheiros CSV).
numpy: Processamento vetorial e cálculos matemáticos de posições.

