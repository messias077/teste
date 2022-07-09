# ----------------------------------------------------------------
# Cliente genérico para acesso aos bancos de dados
# ----------------------------------------------------------------

from src.classes.persistencia.conectores.mongodb import ConectorMongoDb
from src.ambiente.parametros_globais import UNDEFINED_DATABASE_TYPE


class ClienteGenerico:
    """
    Cliente genérico para acesso aos bancos de dados. Conectores serão utilizados para que o acesso aos bancos
    seja transparente para as aplicações. As validações serão concentradas aqui nesta classe
    """
    def __init__(self, tipo, servidor, porta, banco=''):
        self.__bd = None
        self.__tipo = tipo

        # Escolhe o tipo de conexão
        if self.__tipo == 'MongoDB':
            self.__bd = ConectorMongoDb(servidor, porta, banco)
        else:
            print(f"\nO tipo de banco '{self.__tipo}' não está definido na classe "
                  f"'classes.persistencia.cliente.ClienteGenerico'.\n")
            exit(UNDEFINED_DATABASE_TYPE)

    def fechar_conexao(self):
        self.__bd.fechar_conexao()

    def inserir(self, destino, registo):
        """
        Insere um registro ou documento no banco de dados
            :param destino: Tabela, coleção ou índice que receberá o novo dado
            :param registo: Objeto que será inserido
        """
        if destino != '':
            self.__bd.inserir(destino, registo)
        else:
            print('O nome do destino não pode estar vazio!')

    def buscar_um(self, origem, atributo, valor):
        """
        Busca um registro ou documento no banco de dados que atenda ao critério de busca
            :param origem: Tabela, coleção ou índice onde o dado será buscado
            :param atributo: Atributo que será pesquisado
            :param valor: Valor do atributo que será pesquisado
            :return: Documento buscado, se existir
        """
        return self.__bd.buscar_um(origem, atributo, valor)

    def buscar_todos(self, origem, atributo, valor):
        """
        Busca todos os registros ou documentos no banco de dados que atendam ao critério de busca
            :param origem: Tabela, coleção ou índice onde o dado será buscado
            :param atributo: Atributo que será pesquisado
            :param valor: Valor do atributo que será pesquisado
            :return: Documento(s) buscado(s), se existir(em)
        """
        return self.__bd.buscar_todos(origem, atributo, valor)

    def excluir(self, origem, cod):
        """
        Exclui um registro ou documento no banco de dados
            :param origem: Tabela, coleção ou índice onde o dado será excluido
            :param cod: Código do registro ou documento que será excluido
        """
        self.__bd.excluir(origem, cod)

    def alterar(self, origem, chave_buscar, valor_buscar, chave_alterar, valor_alterar):
        """
        Altera um registro ou documento no banco de dados
            :param origem: Tabela, coleção ou índice onde o dado será alterado
            :param chave_buscar: Chave que será utilizada para buscar o documento a ser alterado
            :param valor_buscar: Valor da chave de busca
            :param chave_alterar: Chave que terá o valor alterado
            :param valor_alterar: Novo valor para a chave_alterar
            :return: True se o documento foi alterado, False caso contrário
        """
        resultado = self.__bd.alterar(origem, chave_buscar, valor_buscar, chave_alterar, valor_alterar)

        if self.__tipo == 'MongoDB':
            if resultado.raw_result['nModified'] == 1:
                return True
            else:
                return False
