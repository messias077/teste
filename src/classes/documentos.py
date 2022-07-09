# ----------------------------------------------------------------------------------------------
# Algumas classes que representam os documentos processados pelo sistema
#
# ATENÇÃO: Se uma nova classe for criada ou modificada e houver a necessidade de persisti-la
# em banco de dados, implemente ou altere a sua entrada na rotina da função de desserialização
# no arquivo src.classes.persistencia.serializacao.py
# ----------------------------------------------------------------------------------------------

class Edital:
    """
    Edital com as seções extraídas de um arquivo contendo um edital de compras
    """
    def __init__(self, nome='', codigo_arq='', codigo_lote='', secoes=None, dumpconteudo=None):
        # self.__nome: Nome do arquivo que será salvo no BD após o pré-processamento.
        # Obs.: O arquivo original será renomeado para este mesmo nome e guardado na pasta de arquivos processados
        self.__nome = nome
        self.__codigo_arq = codigo_arq
        self.__codigo_lote = codigo_lote
        self.__secoes = secoes
        self.__dumpconteudo = dumpconteudo

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """
        return {'Edital__nome': self.__nome,
                'Edital__codigo_arq': self.__codigo_arq,
                'Edital__codigo_lote': self.__codigo_lote,
                'Edital__secoes': self.__secoes,
                'Edital__dumpconteudo': self.__dumpconteudo}

    @property
    def nome(self):
        return self.__nome

    @property
    def codigo_arq(self):
        return self.__codigo_arq

    @property
    def codigo_lote(self):
        return self.__codigo_lote

    @property
    def secoes(self):
        return self.__secoes

    @property
    def dumpconteudo(self):
        return self.__dumpconteudo

    @nome.setter
    def nome(self, nome):
        self.__nome = nome

    @codigo_arq.setter
    def codigo_arq(self, codigo_arq):
        self.__codigo_arq = codigo_arq

    @codigo_lote.setter
    def codigo_lote(self, codigo_lote):
        self.__codigo_lote = codigo_lote

    @secoes.setter
    def secoes(self, secoes):
        self.__secoes = secoes

    @dumpconteudo.setter
    def dumpconteudo(self, dumpconteudo):
        self.__dumpconteudo = dumpconteudo


class Secao:
    """
    Seção extraída de um edital de compras
    """
    def __init__(self, numero=''):
        self.__numero = numero
        self.__titulo = ''
        self.__paginas = []  # Guarda os números das páginas onde a seção se encontra
        self.__subsecoes = []  # Guarda todas as subseções que pertencem à seção

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """
        return {'Secao__numero': self.__numero,
                'Secao__titulo': self.__titulo,
                'Secao__paginas': self.__paginas,
                'Secao__subsecoes': self.__subsecoes}

    @property
    def numero(self):
        return self.__numero

    @property
    def titulo(self):
        return self.__titulo

    @property
    def paginas(self):
        return self.__paginas

    @property
    def subsecoes(self):
        return self.__subsecoes

    @numero.setter
    def numero(self, numero):
        self.__numero = numero

    @titulo.setter
    def titulo(self, titulo):
        self.__titulo = titulo

    @paginas.setter
    def paginas(self, paginas):
        self.__paginas = paginas

    @subsecoes.setter
    def subsecoes(self, subsecoes):
        self.__subsecoes = subsecoes

    def inserir_pagina(self, pagina):
        self.__paginas.append(pagina)

    def inserir_subsecao(self, subsecao):
        self.__subsecoes.append(subsecao)


class Subsecao:
    """
    Subsecao extraída de uma seção de um edital de compras
    """
    def __init__(self, numero=''):
        self.__numero = numero
        self.__descricao = ''
        self.__pagina = ''  # Número da página onde a subseção começa

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """
        return {'Subsecao__numero': self.__numero,
                'Subsecao__descricao': self.__descricao,
                'Subsecao__pagina': self.__pagina}

    @property
    def numero(self):
        return self.__numero

    @property
    def descricao(self):
        return self.__descricao

    @property
    def pagina(self):
        return self.__pagina

    @numero.setter
    def numero(self, numero):
        self.__numero = numero

    @descricao.setter
    def descricao(self, descricao):
        self.__descricao = descricao

    @pagina.setter
    def pagina(self, pagina):
        self.__pagina = pagina
