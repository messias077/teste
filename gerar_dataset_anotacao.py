# -----------------------------------------------------------------------------
# Cadastra, pré-processa e salva os editais no banco de dados. Depois Lê
# os editais e gera os datasets para enviar para os anotadores.
#
# Obs.: Utiliza os parâmetros padrões. Para escolher outros parâmetros
# utilizar a interface interativa do programa: 'python interface_prog.py'
# -----------------------------------------------------------------------------

import os
import time
from src.utils import suprimir_warning_tf
from src.utils.limpar_db import limpar_db_para_testes
from src.ambiente.parametros_globais import PREPROC_CAMINHO_ARQ_CONF, FILE_NOT_FOUND_ERROR, PERMISSION_ERROR
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from interface_prog import cadastrar_arquivos
from src.modulos.preproc.preproc import pre_processamento
from src.modulos.ren.ren import ren


# Esta opção é para apagar os bancos de dados caso o script seja rodado novamente.
# Se não apagar, não será possível cadastrar um edital mais de uma vez, o script não deixa!
# Não tem uma interface para esta atividade porque ainda não foi decidido se o usuário terá
# permissão para apagar os editais processados.
def verificar_arquivos_dropar_databases(caminho):
    """
    Verifica se tem arquivos para processar. Caso positivo, limpa a base de dados, caso negativo, aborta o programa.
        :param caminho: Caminhos onde se encontram os possíveis arquivos para processar.
    """
    arquivos_verificar = []
    caminho_verificar = os.path.join(caminho, 'editais')

    # Obtém a lista de todos os arquivos que serão verificados
    try:
        arquivos_verificar = os.listdir(caminho_verificar)
    except FileNotFoundError:
        print(f"\nO caminho '{caminho_verificar}' não existe!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao listar o caminho '{caminho_verificar}'. Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    tem_arquivos_para_processar = False

    # Verifica se tem algum PDF para processar
    for a in arquivos_verificar:
        if ".pdf" in a.lower():
            tem_arquivos_para_processar = True
            break

    if tem_arquivos_para_processar:
        limpar_db_para_testes()
    else:
        print(f"\nO caminho '{caminho_verificar}' não possui arquivos para processar!\n")
        exit(FILE_NOT_FOUND_ERROR)


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    # Obtém o caminho do arquivo de configuração para montar o caminho completo
    caminho_arquivo_configuracao = PREPROC_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao = 'param_preproc.conf'
    arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

    conf = inicializar_parametros('preproc', arq_conf)

    # Obtém alguns parâmetros de configuração do módulo
    parametros = {'caminho_arq_conf': arq_conf,
                  'p_caminho_entrada': conf.obter_valor_parametro('p_caminho_entrada')}

    validar_pastas(parametros)

    # Se existir arquivo para processar, faz a limpeza da base de dados.
    # Obs.: Esta ação é específica para realizar testes... pois não é interessante ficar reprocessando os editais
    # e gravando os editais no banco cada vez que for gerar os datasets para anotação!
    verificar_arquivos_dropar_databases(parametros['p_caminho_entrada'])

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
