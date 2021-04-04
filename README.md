# Clima X Ibovespa
Relação do clima com o índice da bolsa de valores

### Requisitos
- Python 3.8.5 ou superior instalado
- MongoDB instalado
- PostgreSQL instalado ou um banco disponível na nuvem
- Utilizar Ubuntu ou outra distribuição Linux

### Passos para Execução
1. Alterar ```.gotodata_env``` com os seguintes dados:
	- Chave da api de clima (API_KEY)
	- Banco PostgreSQL (DB_CONNECTION)
	- Banco MongoDB (MONGODB_CONNECTION)
2. Executar arquivo ```install.sh``` para instalar dependências e configurar bancos
3. Executar arquivo ```execute.sh``` para subir aplicação
    - ```execute.sh --update``` caso precise instalar dependências
4. Acessar aplicação via http://localhost:5001/
5. Acessar flower via http://localhost:5555/
    - Login: admin
    - Senha: 1234goto
6. Executar arquivo ```stop.sh``` para interromper a aplicação

### Observação
- [Oito municípios detinham 25% do PIB do país em 2018](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/29728-oito-municipios-detinham-25-do-pib-do-pais-em-2018):
	- São Paulo (SP)
	- Rio de Janeiro (RJ)
	- Brasília (DF)
	- Belo Horizonte (MG)
	- Curitiba (PR)
	- Manaus (AM)
	- Porto Alegre (RS)
	- Osasco (SP)
