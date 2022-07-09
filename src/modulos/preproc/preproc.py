# ----------------------------------------------------------------------------------------------
# MÓDULO DE PRÉ-PROCESSAMENTO DOS ARQUIVOS DE EDITAIS
#
# >Função:
#   - Preparar o conteúdo dos arquivos para o processamento futuro e persistir em banco de dados.
#
# >Tarefas executadas:
#   - Ler os arquivos e converter para texto plano;
#   - Separar os editais em seções;
#   - Gerar um dump do conteúdo dos editais;
#   - Gerar metadados dos arquivos para facilitar consultas;
#   - Organizar os documentos em pastas bem definidas após o pré-processamento;
#   - Persistir os documentos processados no MongoDB;
#   - Persistir os metadados no MongoDB;
# ----------------------------------------------------------------------------------------------

import os
import src.ambiente.preparar_ambiente as pre
import src.modulos.preproc.pre_processador as proc
from src.ambiente.parametros_globais import PREPROC_CAMINHO_ARQ_CONF, PERMISSION_ERROR, PARAMETER_ERROR


def validar_preparar_pastas(p):
    """
    Valida os nomes das pastas e prepara os caminhos para o pré-processamento dos arquivos
        :param p: Dicionário contendo as configurações/parâmetros do sistema
    """
    pre.validar_pastas(p)

    # Não podem ser iguais, pois senão os arquivos ficarão bagunçados e a leitura para pré-processamento falhará
    if p['p_caminho_entrada'].upper() == p['p_caminho_base'].upper():
        print(f"\nOs parâmetros 'p_caminho_entrada' e 'p_caminho_base' não podem ser iguais!\n"
              f"Edite o arquivo de configuração ('{p['caminho_arq_conf']}') e corrija este erro.\n")
        exit(PARAMETER_ERROR)

    # Monta o caminho das pastas de onde os arquivos serão lidos para execução do pré-processamento
    caminho_entrada_editais = os.path.join(p['p_caminho_entrada'], 'editais')

    # Monta o caminho das pastas para onde os arquivos serão movidos após o pré-processamento
    caminho_destino_editais = os.path.join(p['p_caminho_base'], 'editais', p['p_caminho_relativo'])

    # Guarda os caminhos para criação das pastas utilizadas no pré-processamento
    caminhos = [caminho_entrada_editais, caminho_destino_editais]

    # Se essas pastas não existirem, elas serão criadas
    for c in caminhos:
        try:
            os.makedirs(c, exist_ok=True)
        except PermissionError:
            print(f"\nErro ao criar a pasta '{c}'. Permissão de escrita negada!\n")
            exit(PERMISSION_ERROR)


def pre_processamento():
    """
    Módulo de pré-processamento dos arquivos de editais
    """
    # Obtém o caminho do arquivo de configuração para montar o caminho completo
    caminho_arquivo_configuracao = PREPROC_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao = 'param_preproc.conf'
    arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

    conf = pre.inicializar_parametros('preproc', arq_conf)

    # Obtém os parâmetros de configuração do módulo
    parametros = {'caminho_arq_conf': arq_conf,
                  'p_caminho_entrada': conf.obter_valor_parametro('p_caminho_entrada'),
                  'p_caminho_base': conf.obter_valor_parametro('p_caminho_base'),
                  'p_caminho_relativo': conf.obter_valor_parametro('p_caminho_relativo'),
                  'nome_pasta_erros': conf.obter_valor_parametro('nome_pasta_erros'),
                  'timeout_lock': conf.obter_valor_parametro('timeout_lock')}

    validar_preparar_pastas(parametros)

    # Inicia o pré-processamento dos arquivos
    proc.pre_processar_arquivos('EDITAL', os.path.join(parametros['p_caminho_entrada'], 'editais'),
                                os.path.join(parametros['p_caminho_base'], 'editais'),
                                parametros['p_caminho_relativo'],
                                parametros['nome_pasta_erros'],
                                parametros['timeout_lock'])


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    pre_processamento()
