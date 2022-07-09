# ----------------------------------------------------------------------------------------------
# Algumas classes que representam os parâmetros de configuração utilizados no sistema
# ----------------------------------------------------------------------------------------------

class Config:
    """
    Configurações do sistema
    """
    def __init__(self, caminho_arq_conf):
        self.__caminho_arq_conf = caminho_arq_conf
        self.__parametros = []

    @property
    def caminho_arq_conf(self):
        return self.__caminho_arq_conf

    @property
    def parametros(self):
        return self.__parametros

    def inserir_parametro(self, p):
        self.__parametros.append(p)

    def obter_valor_parametro(self, parametro):
        for p in self.__parametros:
            if p.nome == parametro:
                return p.valor


class Parametro:
    """
     Parâmetros que serão lidos do arquivo de configurações (extensão '.conf') ou diretamente do sistema
    """
    def __init__(self, nome='', valor='', tipo='str', descricao='', persistido=True):
        self.__nome = nome
        self.__valor = valor
        self.__tipo = tipo  # Para realizar as conversões de tipo se necessário (Valores = 'str', 'int' ou 'float')
        self.__descricao = descricao  # Para facilitar o entendimento da função do parâmetro
        self.__persistido = persistido  # Indica se o parâmetro está persistido no arquivo 'parametros.conf'

    @property
    def nome(self):
        return self.__nome

    @property
    def valor(self):
        return self.__valor

    @property
    def tipo(self):
        return self.__tipo

    @property
    def descricao(self):
        return self.__descricao

    @property
    def persistido(self):
        return self.__persistido

    @valor.setter
    def valor(self, valor):
        self.__valor = valor
