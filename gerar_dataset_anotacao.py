# -----------------------------------------------------------------------------
# Cadastra, pré-processa e salva os editais no banco de dados. Depois Lê
# os editais e gera os datasets para enviar para os anotadores.
#
# Obs.: Utiliza os parâmetros padrões. Para escolher outros parâmetros
# utilizar a interface interativa do programa: 'python interface_prog.py'
# -----------------------------------------------------------------------------

import os
import time
from src.ambiente.parametros_globais import PREPROC_CAMINHO_ARQ_CONF
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from interface_prog import cadastrar_arquivos
from src.modulos.preproc.preproc import pre_processamento
from src.modulos.ren.ren import ren

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
    retirar_sentencas_semelhantes=True, escopo_global_sentencas=True)
