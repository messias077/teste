# -----------------------------------------------------------------------------
# Limpa o banco de dados para realização de novos testes. Se não apagar, não
# será possível cadastrar um edital mais de uma vez, o script não deixa!
#
# Obs.: Não existe uma interface mais interativa para esta atividade porque
# ainda não foi decidido se o usuário terá permissão para apagar os editais
# processados.
# -----------------------------------------------------------------------------

def limpar_db_para_testes(interativo=False):
    """
    Exclui os editais cadastrados para posssibilitar a reexecução dos testes. Se não apagar, não será possível
    cadastrar um edital mais de uma vez, o script não deixa!
        :param interativo: Se vai interagir com o usuário ou não
    """
    resp = ""

    if interativo:
        resp = input("\nDeseja realmente excluir todos os editais? (S/N): ").lower()

    if resp == 's' or not interativo:
        print("\nPara fins de testes, excluindo os editais cadastrados...", end='', flush=True)

        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure
        from src.ambiente.parametros_globais import CONNECTION_ERROR

        # Conecta ao banco
        conexao = MongoClient('localhost', 27017)

        try:
            conexao.admin.command('ismaster')
        except ConnectionFailure:
            print('\nErro ao conectar ao banco de dados MongoDB. Faça testes e verifique:')
            print('- se o nome do servidor está correto;')
            print('- se a porta para conexão ao banco está correta;')
            print('- se o banco está rodando e aceitando conexões.\n')
            exit(CONNECTION_ERROR)

        # Apaga os bancos de dados
        conexao.drop_database('db_documentos')
        conexao.drop_database('db_metadados')

        conexao.close()

        print("OK!\n")
    elif resp != "n":
        print("\nResposta incorreta. Nenhum edital foi excluído!")
