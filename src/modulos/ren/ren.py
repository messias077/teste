# ----------------------------------------------------------------------------------------------
# MÓDULO DE REN PARA O PROCESSAMENTO DOS DOCUMENTOS DE EDITAIS
#
# >Função:
#   - Fazer a classificação das subseções; gerar sentenças e gerar datasets para a tarefa de REN
#
# >Tarefas executadas:
#   - Obter as subseções dos documentos pré-processados;
#   - Classificar as subseções em jurídicas (JUR) e técnicas (TEC);
#   - Gerar datasets para a tarefa de REN;
#   - Gerar datasets para a classificação das subseções;
#   - Marcar os metadados dos documentos no MongoDB como processados.
# ----------------------------------------------------------------------------------------------

import os
import src.ambiente.preparar_ambiente as pre
from src.modulos.ren.construtor_datasets import construir_dataset
from src.ambiente.parametros_globais import REN_CAMINHO_ARQ_CONF, PERMISSION_ERROR
from src.utils.geradores import gerar_data, gerar_epoch


def gerar_estatisticas_documentos(data_hora, documentos_sentencas, codproc, caminho):
    """
    Gera as estatísticas dos documentos (quantidade de sentenças por documento, total e média de sentenças)
        :param data_hora: Data e hora para compor o nome do arquivo de estatísticas
        :param documentos_sentencas: Dicionário cuja chave é o código do arquivo e o valor é uma lista de sentenças
        :param codproc: Código do processamento para gerar a estatística (ner ou classificacao)
        :param caminho: Caminho para a geração do arquivo com as estatísticas
    """
    nome_arquivo_estatisticas = f"estatisticas_{codproc}_{data_hora}.csv"
    caminho_arquivo_estatisticas = os.path.join(caminho, nome_arquivo_estatisticas)
    arq_sents = None
    qtd_documentos = len(documentos_sentencas)
    total_sentencas = 0

    try:
        arq_sents = open(caminho_arquivo_estatisticas, 'w')
    except PermissionError:
        print(f"\nErro ao criar o arquivo de estatísticas na pasta '{caminho}'. Permissão de gravação negada!\n")
        exit(PERMISSION_ERROR)

    arq_sents.write("Descrição,valor\n")  # Adiciona um cabeçalho genérico para facilitar a leitura do CSV

    for cod_arq, sentencas in documentos_sentencas.items():
        qtd_sentencas = len(sentencas)
        total_sentencas += qtd_sentencas
        arq_sents.write(f"{cod_arq},{qtd_sentencas}\n")

    media_sentencas = total_sentencas/qtd_documentos if qtd_documentos > 0 else 0
    arq_sents.write(f"Quantidade de documentos processados,{qtd_documentos}\n")
    arq_sents.write(f"Total de sentenças,{total_sentencas}\n")
    arq_sents.write(f"Média de sentenças por documento,{media_sentencas}\n")
    arq_sents.close()


def ren(codproc, qtd_max_sent, reprocessar=False, gerar_estatisticas=False, organizar_em_pastas=False,
        retirar_sentencas_semelhantes=False, escopo_global_sentencas=True):
    """
    Módulo de REN para o processamento dos documentos de editais
        :param codproc: Código do processamento a ser realizado (ner ou classificacao)
        :param qtd_max_sent: Quantidade máxima de sentenças em cada arquivo
        :param reprocessar: Indica se deve fazer o reprocessamento dos documentos, caso já tenha sido construido um
        dataset antes
        :param gerar_estatisticas: Indica se gerará as estatísticas dos documentos processados
        :param organizar_em_pastas: Indica se os editais serão organizados em pasta (uma pasta para cada edital)
        :param retirar_sentencas_semelhantes: Indica se as sentenças semelhantes devem ser retiradas no momento de
                                              geração dos datasets
        :param escopo_global_sentencas: Escopo para a análise de sentenças. Se True, fará a comparação com todos os
                                        documentos, caso contrário a comparação será somente no próprio documento
    """
    # Lista para validação dos códigos de processamento
    lista_codproc = ['ner', 'classificacao', 'classificacao_label']

    if codproc in lista_codproc:
        # Obtém o caminho do arquivo de configuração para montar o caminho completo
        caminho_arquivo_configuracao = REN_CAMINHO_ARQ_CONF
        nome_arquivo_configuracao = 'param_ren.conf'
        arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

        conf = pre.inicializar_parametros('ren', arq_conf)

        # Obtém os parâmetros de configuração do módulo
        parametros = {'caminho_arq_conf': arq_conf,
                      'p_caminho_datasets': conf.obter_valor_parametro('p_caminho_datasets'),
                      'p_tamanho_minimo_sentenca': conf.obter_valor_parametro('p_tamanho_minimo_sentenca'),
                      'p_caminho_sentencas_base': conf.obter_valor_parametro('p_caminho_sentencas_base')}

        pre.validar_pastas(parametros)

        data_hora = gerar_data(gerar_epoch(), '%Y-%m-%d_%H%M%Shs')

        documentos_sentencas, caminho_estatisticas = \
            construir_dataset(data_hora, codproc, parametros['p_caminho_datasets'],
                              parametros['p_caminho_sentencas_base'], parametros['p_tamanho_minimo_sentenca'],
                              qtd_max_sent, reprocessar, organizar_em_pastas, cabecalho=True,
                              retirar_sentencas_semelhantes=retirar_sentencas_semelhantes,
                              escopo_global_sentencas=escopo_global_sentencas, limiar=0.90)

        if codproc == 'ner' and documentos_sentencas and gerar_estatisticas:
            gerar_estatisticas_documentos(data_hora, documentos_sentencas, codproc, caminho_estatisticas)
    else:
        print("\nCódigo de processamento inválido! Opções: 'ner', 'classificacao' ou 'classificacao_label'.")


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    ren('ner', 200, reprocessar=False, gerar_estatisticas=False, organizar_em_pastas=True,
        retirar_sentencas_semelhantes=False, escopo_global_sentencas=True)
