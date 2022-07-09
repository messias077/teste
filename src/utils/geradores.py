# -------------------------------------------------------------------
# Funções para geração de hashs, nomes de arquivos,
# datas no formato epoch, etc...
# -------------------------------------------------------------------

import hashlib
import time
import datetime
import numpy as np
from unicodedata import normalize
from src.classes.metadados import Documento


def gerar_hash_arquivo(paginas_dump_arq):
    """
    Gera um hash MD5 baseado no conteúdo das páginas do arquivo
        :param paginas_dump_arq: Lista contendo as páginas lidas do arquivo
        :return: Hash MD5 do conteúdo das páginas do arquivo
    """
    h = hashlib.md5()

    for p in paginas_dump_arq:
        h.update(p.encode('utf-8'))

    return h.hexdigest()


def gerar_head(paginas_dump_arq, qtd_tokens):
    """
    Gera um head com as primeiras paginas que contém os 'qtd_tokens' tokens (ex.: palavras, sinais de
    pontuação, artigos, simbolos em geral pertencentes ao texto) iniciais do arquivo
        :param paginas_dump_arq: Lista contendo todas as páginas do arquivo
        :param qtd_tokens: Quantidade de tokens que serão consideradas para a geração do head
        :return: Lista com as páginas que contém os primeiros 'qtd_tokens' tokens do arquivo
    """
    qtd_tokens_lidos = 0
    head = []

    for p in paginas_dump_arq:
        head.append(p)
        tokens = p.split()
        qtd_tokens_lidos += len(tokens)

        if qtd_tokens_lidos >= qtd_tokens:
            break

    return head


def gerar_epoch():
    """
    Gera um timestamp no formato epoch utilizando a hora atual
        :return: Timestamp no formato epoch convertido para inte
    """
    return int(time.time())


def gerar_data(tempo_epoch, formato):
    """
    Gera uma string contendo a data referente ao timestamp no formato epoch
        :param tempo_epoch: Timestamp no formato epoch
        :param formato: Formato para geração da data (ex: '%d/%m/%Y %H:%M:%S')
        :return: string contendo a data referente ao timestamp passado como parâmetro
    """
    return datetime.datetime.fromtimestamp(tempo_epoch).strftime(formato)


def gerar_codigo_arquivo(nome_arq):
    """
    Gera um código para o arquivo, seguindo as regras do sistema
        :param nome_arq: Nome do arquivo
        :return: Código gerado para o arquivo
    """
    # Retira acentos, cedilhas, etc... (transforma em codificação ASCII)
    nome_ascii = normalize('NFKD', nome_arq).encode('ASCII', 'ignore').decode('ASCII')

    # Caso o nome do arquivo tenha outros pontos ('.') além do separador de extensão, retira estes pontos
    nome_split_sem_pontos = nome_ascii.split('.')
    nome_sem_pontos_adicionais = '-'.join(nome_split_sem_pontos[:-1]) + '.' + nome_split_sem_pontos[-1]

    # Substitui os espaços em branco por '_' (underscores)
    sufixo_codigo_split = nome_sem_pontos_adicionais.split()
    sufixo_codigo = '_'.join(sufixo_codigo_split)

    # Tenta gerar um prefixo único para cada arquivo para evitar que sejam sobrescritos
    prefixo_float = np.random.uniform(0, 1000)
    prefixo_split = str(prefixo_float).split('.')
    codigo = prefixo_split[0] + prefixo_split[1] + '_' + sufixo_codigo

    return codigo


def gerar_codigo_lote():
    """
    Gera um código de lote para o processamento dos arquivos
        :return: Código do lote
    """
    prefixo = str(np.random.uniform(0, 5))

    sufixo_float = time.time()
    sufixo = str(sufixo_float)

    inicio_codigo = gerar_data(sufixo_float, '%Y-%m-%d_')

    final_codigo_temp = prefixo + sufixo
    h = hashlib.md5()
    h.update(final_codigo_temp.encode('utf-8'))
    final_codigo = h.hexdigest()

    return inicio_codigo + final_codigo


def gerar_metadados_doc(codigo_lote, metadados, objeto_arq):
    """
    Gera os metadados do documento lido para facilitar no processamento e consulta
        :param codigo_lote: Código do lote onde o arquivo foi processado
        :param metadados: Dicionário contendo os metadados do arquivo
        :param objeto_arq: Objeto contendo o arquivo lido no formato texto
        :return: Objeto contendo os metadados do documento
    """
    # Gera um nome definitivo para o arquivo para movimentá-lo para o repositório de arquivos
    nome_aux = objeto_arq.nome[objeto_arq.nome.index('_') + 1:len(objeto_arq.nome)]  # Retira o prefixo do nome
    nome_split = nome_aux.split('.')
    hash_arq = gerar_hash_arquivo(objeto_arq.dumpconteudo)
    nome_arq = f"{nome_split[0]}_{hash_arq}"
    extensao = 'n/a'

    # Trata o caso do arquivo possuir extensão
    if len(nome_split) > 1 and nome_split[-1] != '':
        nome_arq += f".{nome_split[-1]}"
        extensao = nome_split[-1].upper()

    # Atualiza o nome do arquivo para o nome definitivo
    objeto_arq.nome = nome_arq

    # Cria um objeto com metadados do documento
    head = gerar_head(objeto_arq.dumpconteudo, 3000)
    doc_meta = Documento(nome=nome_arq, codigo_arq=metadados['codigo_arq'], hash_md5=hash_arq,
                         tipo_arq=metadados['tipo'], extensao=extensao, data_cadastro=int(metadados['data_cadastro']),
                         usuario_cadastrou=metadados['usuario_cadastrou'], codigo_lote=codigo_lote,
                         nome_arq_original=metadados['nome_arq_original'], url_web=metadados['url_web'],
                         caminho_base=metadados['caminho_base'], caminho_relativo=metadados['caminho_relativo'],
                         head=head)

    return doc_meta
