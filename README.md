# ren_editais
Repositório para disponibilização da ferramenta para executar a tarefa de REN (Reconhecimento de Entidades Nomeadas) em editais de compras

---
## 1. Preparação do ambiente
Antes de utilizar o programa, é necessário preparar o sistema do seu computador para executá-lo.

### 1.1 - Pré-requisitos
Instale os programas abaixo:
* **MongoDB.** Instale e deixe o MongoDB em execução (*Nota: Para fins de testes, não há necessidade de criar usuário e senha para acesso ao banco, o programa funcionará sem*). Instruções: [Linux](https://www.mongodb.com/docs/manual/administration/install-on-linux/) ou [Windows](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-windows).

* **Python.** Instruções: [Linux (Geralmente já vem instalado por padrão)](https://python.org.br/instalacao-linux) ou [Windows](https://www.python.org/downloads/windows).

* **Git.** Instruções: [Linux](https://git-scm.com/download/linux) ou [Windows](https://git-scm.com/download/win).

*Nota: Há possibilidade de instalar o MongoDB via container do [Docker](https://www.docker.com/), porém esta forma de instalação não será abordada nos testes. Caso queira instalar dessa forma, fique à vontade, pois o programa suporta e funciona perfeitamente.*

### 1.2 - Organize as coisas
* **Crie uma pasta para organizar os arquivos em um local de sua preferência.**

### 1.3 - Tela preta
* **Comandos.** Todos os comandos daqui em diante serão na famosa tela preta do terminal! Abra um shell Linux ou prompt de comando Windows para executar os próximos passos.

### 1.4 - Ambiente virtual Python (opcional)
*Nota: Apesar de não ser mandatório, a criação de um ambiente virtual ajuda na organização dos projetos e evita conflitos entre bibliotecas de projetos diferentes.*
* **Instale e ative o Venv.** Entre na pasta criada no passo 1.2, instale e ative Venv. Instruções: [Linux e Windows (escolha o sistema na página)](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment).

### 1.5 - Clone o repositório
* **Clone.** Ainda de dentro da pasta criada no passo 1.2, clone o repositório com o comando:
```
git clone https://github.com/messias077/ren_editais.git
```

### 1.6 - Dependências do projeto
* **Instale as dependências.** Entre na pasta criada pelo processo de clonagem do repositório...
```
cd ren_editais
```
e rode o comando:
```
pip install -r requirements.txt
```
*Nota: Caso dê algum erro na instalação das dependências, não continue antes de resolver... Pesquisar o erro no Google pode ajudar!*

---
## 2. Instruções de uso

Para utilizar o programa e rodar os testes com parâmetros padrão execute os passos abaixo:

### 2.1 - Copiar editais
* **Copie editais de testes.** Copie os editais de testes que estão localizados na pasta ['ren_editais/testes'](editais_testes/) para a pasta de entrada padrão do programa que é, 'ren_editais/repo/editais', ou para outra pasta, caso tenha alterado os arquivos de configuração.

### 2.2 - Processar editais
* **Rode o script para processar editais e gerar os arquivos para anotação.** Execute o comando abaixo para converter os editais em texto plano, cadastrar no banco de dados e gerar os arquivos que os anotadores utilizam para importar no Doccano e realizar as anotações.
```
python gerar_dataset_anotacao.py
```
### 2.3 - Anotação das entidades
* **Realizar anotações.** Importe os arquivos gerados no  para dentro da ferramenta Doccano, faça as anotações e exporte os arquivos anotados. Instruções: [Tutorial para anotação](tutoriais/).

### 2.4 - Geração do *corpus*
* **Copie os arquivos anotados.** Copie os arquivos JSONL que foram anotados exportados pela ferramenta Doccano para a pasta de arquivos anotados padrão do programa, que é 'repo/arquivos_anotados', ou para outra pasta, caso tenha alterado os arquivos de configuração.

* **Gere o *corpus* no formato CONLL.** Para converter os arquivos anotados e gerar o *corpus* no formato CONLL rode o comando abaixo:
```
converter_arquivos_anotados.py
```
Pronto! Se tudo aconteceu conforme esperado, nesse ponto você tem um *corpus*, baseado nos editais de testes, que pode ser utilizado como base para realizar as tarefas de REN.
