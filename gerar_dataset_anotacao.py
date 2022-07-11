# -----------------------------------------------------------------------------
# Cadastra, pré-processa e salva os editais no banco de dados. Depois Lê
# os editais e gera os datasets para enviar para os anotadores.
#
# Obs.: Utiliza os parâmetros padrões. Para escolher outros parâmetros
# utilizar a interface interativa do programa: 'python interface_prog.py'
# -----------------------------------------------------------------------------

import os
import time
import suprimir_warning_tf
from src.ambiente.parametros_globais import PREPROC_CAMINHO_ARQ_CONF
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from interface_prog import cadastrar_arquivos
from src.modulos.preproc.preproc import pre_processamento
from src.modulos.ren.ren import ren


# Esta opção é para apagar os bancos de dados caso o script seja rodado novamente.
# Se não apagar, não será possível cadastrar um edital mais de uma vez, o script não deixa!
# Não tem uma interface para esta atividade porque ainda não foi decidido se o usuário terá
# permissão para apagar os editais processados.
drop_databases = True

if drop_databases:
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

# Obtém o caminho do arquivo de configuração para montar o caminho completo
caminho_arquivo_configuracao = PREPROC_CAMINHO_ARQ_CONF
nome_arquivo_configuracao = 'param_preproc.conf'
arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

conf = inicializar_parametros('preproc', arq_conf)

# Obtém alguns parâmetros de configuração do módulo
parametros = {'caminho_arq_conf': arq_conf,
              'p_caminho_entrada': conf.obter_valor_parametro('p_caminho_entrada')}

validar_pastas(parametros)

# Cadastra todos os editais que estão na pasta
print("\n### CADASTRO DOS EDITAIS")
cadastrar_arquivos('EDITAL', 'SISTEMA', parametros['p_caminho_entrada'])
time.sleep(3)  # Dá um tempo para evitar erros...

# Pré-processa os editais
print("\n### PRÉ-PROCESSAMENTO")
pre_processamento()
time.sleep(5)  # Dá um tempo para o banco de dados indexar os editais inseridos...

# Gera os datasets para enviar para os anotadores
print("\n### GERAÇÃO DOS DATASETS")
ren('ner', 100, reprocessar=False, gerar_estatisticas=True, organizar_em_pastas=True,
    retirar_sentencas_semelhantes=True, escopo_global_sentencas=False)
