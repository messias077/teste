# ----------------------------------------------------------------
# Conector para acesso ao banco de dados MongoDB
# ----------------------------------------------------------------

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure
from src.ambiente.parametros_globais import CONNECTION_ERROR


class ConectorMongoDb:
    """
    Conector para o banco de dados MongoDB
    """
    def __init__(self, servidor, porta, banco):
        self.__conexao = MongoClient(servidor, porta)

        try:
            self.__conexao.admin.command('ismaster')
        except ConnectionFailure:
            print('\nErro ao conectar ao banco de dados MongoDB. Faça testes e verifique:')
            print('- se o nome do servidor está correto;')
            print('- se a porta para conexão ao banco está correta;')
            print('- se o banco está rodando e aceitando conexões.\n')
            exit(CONNECTION_ERROR)

        # Seta o banco onde os dados serão gravados. Obs.: Um mesmo banco de dados pode ter uma ou várias coleções
        self.__banco = self.__conexao[banco]

    def fechar_conexao(self):
        pass
        # self.__conexao.close() # Retirado porque estava dando erro no Windows!

    def inserir(self, colecao, objeto):
        destino = self.__banco[colecao]  # Indica a coleção onde os dados serão gravados no banco setado anteriormente
        destino.insert_one(objeto)

    # ATENÇÃO:
    # É possível utilizar expressões regulares para realizar buscas utilizando as funções 'buscar_um' e 'buscar_todos'
    # Mais detalhes consultar: https://stackoverflow.com/questions/20175122/how-can-i-use-not-like-operator-in-mongodb

    def buscar_um(self, colecao, chave, valor):
        destino = self.__banco[colecao]
        resultado = None

        try:
            resultado = destino.find_one({chave: {'$regex': valor, '$options': 'i'}})
        except OperationFailure:
            print("\nExpressão regular inválida!\n")

        return resultado

    def buscar_todos(self, colecao, chave, valor):
        destino = self.__banco[colecao]
        resultado = None

        try:
            resultado = destino.find({chave: {'$regex': valor, '$options': 'i'}})
        except OperationFailure:
            print("\nExpressão regular inválida!\n")

        return resultado

    def excluir(self, colecao, cod):
        destino = self.__banco[colecao]
        destino.remove({"_id": cod})

    def alterar(self, colecao, chave_buscar, valor_buscar, chave_alterar, valor_alterar):
        destino = self.__banco[colecao]
        return destino.update_one({chave_buscar: valor_buscar}, {'$set': {chave_alterar: valor_alterar}})
