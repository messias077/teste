# ----------------------------------------------------------------
# Funções para extração de seções contidas no texto obtido
# ----------------------------------------------------------------

import re
from src.classes.documentos import Secao
from src.classes.documentos import Subsecao
import copy as cp


def separar_em_termos(documento):
    """
    Separa o documento em termos (palavras, números, etc.)
        :param documento: Edital lido
        :return: Lista contendo listas com os termos do documento e suas respectivas páginas
    """
    termos = []

    for pagina, texto in documento.items():
        termos_aux = texto.split()

        for termo in termos_aux:
            termos.append([termo, pagina])

    return termos


def encontrar_itens_numerados(string):
    """
    Encontra os itens numerados que constam numa string (Exemplo: 1.1, 1.1.2, 2.3.4.2, 2020, 2019., 00, 0., etc.)
        :param string: String contendo o texto onde os itens serão pesquisados
        :return: Lista com todos os itens encontrados
    """
    #  Encontra os itens utilizando expressões regulares
    expressao_regular = re.compile('[0-9][0-9.]*')

    return expressao_regular.findall(string)


def separar_secao(secao_candidata, termo):
    """
    Verifica se o texto começa com uma provável seção e a separa, se for o caso
        :param secao_candidata: Seção candidata a ser avaliada
        :param termo: Termo a ser avaliado
        :return: Uma lista com o texto separado da seção candidata e a página onde ele se encontra; ou uma lista
        vazia, se não for possível separar o termo da seção candidata
    """
    indice_fim_secao = 0  # Guarda o índice onde termina a seção candidata no texto

    # Verifica se o texto inicia com a seção candidata, se não iniciar, retorna uma lista vazia indicando que
    # o termo não é uma seção candidata
    for i in range(len(secao_candidata)):
        if secao_candidata[i] != termo[0][i]:  # termo[0] = termo; termo[1] = página onde o termo se encontra
            return []
        else:
            indice_fim_secao += 1

    # A seção candidata tem que terminar com '.'
    if secao_candidata[indice_fim_secao - 1] == '.':
        texto_depois_da_secao = ''

        # Obtém o texto que estava grudado na seção candidata
        for i in range(indice_fim_secao, len(termo[0])):
            texto_depois_da_secao += termo[0][i]  # termo[0] = termo; termo[1] = página onde o termo se encontra

        # Retorna um novo termo formado pelo texto que estava grudado na seção candidata e a página onde ele se encontra
        return [texto_depois_da_secao, termo[1]]
    else:
        return []


def encontrar_secoes_candidatas(termos):
    """
    Encontra os termos que podem representar uma seção.
    >> Obs.: Esta função causa um efeito colateral, pois a lista de termos pode ser alterada caso possua um termo que
    tem uma seção candidata com um texto grudado nela (ex.: 2.1.termo_grudado).
        :param termos: Todos os termos encontrados no documento
        :return: Lista contendo os termos que podem representar uma seção
    """
    secoes_candidatas = []
    inserir_em_termos = []  # Armazena os textos que estavam grudados no final de uma seção candidata

    for indice, t in enumerate(termos):  # t[0] = Termo; t[1] = Página do documento onde o termo se encontra
        validado = False
        # Se tiver um ou mais itens numerados no termo, receberá uma lista de strings contendo estes itens, como por
        # exemplo: ['1.1', '1.1.2']; ['2.3.4.2']; ['2020', '2019.', '00', '0.']; etc.
        secao_cand = encontrar_itens_numerados(t[0])

        # Só será uma seção candidata se o termo possuir somente um item numerado
        if len(secao_cand) == 1:
            # Obs.: Não permite seções candidatas começando com '0' e verifica se tem texto grudado com a seção
            if secao_cand[0][0] != '0' and secao_cand[0] == t[0]:  # termo[0] = termo; termo[1] = pág onde o termo está
                validado = True
            else:
                texto_separado = separar_secao(secao_cand[0], t)

                # Se havia texto grudado na seção candidata e esta é válida
                if texto_separado:
                    # Guarda o novo termo para inserir na lista de termos do documento logo após a seção candidata
                    inserir_em_termos.append([indice + 1, texto_separado])

                    # >>AVISO: A atribuição abaixo causa um efeito colateral, pois a lista de termos será alterada!!!
                    # Altera o termo da lista de termos com a seção candidata sem o termo grudado
                    termos[indice] = [secao_cand[0], t[1]]  # t[1] = página onde a seção se encontra

                    validado = True

        if validado:
            secoes_candidatas.append(termos[indice])

    # Caso existam, inserem os novos termos na lista de termos
    for termo_novo in inserir_em_termos:
        # termo_novo[0] = Índice da lista de termos onde o novo termo será inserido
        # termo_novo[1] = Lista contendo o termo e a página onde ele se encontra no documento
        termos.insert(termo_novo[0], termo_novo[1])

    return secoes_candidatas


def validar_secao_repescagem(secoes_candidatas, secao_verificar, ind_prox_secao):
    """
    Faz uma repescagem e tenta validar uma seção candidata caso ela não tenha se encaixado em nenhum padrão anterior
        :param secoes_candidatas: Seções que estão sendo validadas
        :param secao_verificar: Seção que será verificada
        :param ind_prox_secao: Índice da seção posterior à que está sendo verificada
        :return: 'True' se a seção for válida, 'False' caso contrário
    """
    secao_valida = False
    quantidade_verificacoes = 0
    quantidade_maxima_verificacoes = 30

    for i in range(ind_prox_secao, len(secoes_candidatas)):
        # secoes_candidatas[i][0] = Termo; secoes_candidatas[i][1] = Página do documento onde o termo se encontra
        prox_secao = secoes_candidatas[i][0].split('.')

        # Trata os casos de seções candidatas que não possuem '.', exemplo: 1, 2, 3
        # Obs.: Para não dar erro de índice inexistente
        if len(prox_secao) == 1:
            prox_secao.append('')

        # Trata o caso de um início de seção que teve a sua sequência interrompida por números que não são
        # seções válidas. Ex.: [6.9, 7.1, 5, 80, 7.2, 7.3, 7.4]. Neste caso, a 7.1 será validada porque encontrará
        # como uma das próximas seções a seção 7.2, mesmo depois dos números 5 e 80
        # Obs.: secao_verificar[0] = seção; secao_verificar[1] = subseção. O mesmo vale para 'prox_secao'
        if secao_verificar[0] == prox_secao[0] and secao_verificar[1] == '1' and prox_secao[1] == '2':
            secao_valida = True
            break
        elif quantidade_verificacoes > quantidade_maxima_verificacoes:
            break

        quantidade_verificacoes += 1

    return secao_valida


def extrair_secoes(secoes_candidatas):
    """
    Valida e extrai as seções
        :param secoes_candidatas: Seções candidatas que serão validadas e utilizadas para extrair as seções
        :return: Lista com as seções extraídas
    """
    secoes_extraidas = []

    # Permitem validar a partir da seção que está na posição 0 da lista de seções candidatas
    ultima_secao_validada = ['-1', '']

    for i in range(len(secoes_candidatas) - 1):
        sessao_valida = False

        # Se a seção candidata tiver '.', vai retornar uma lista com a seçao e a subseção:
        # => Ex.: para '2.1' retorna ['2', '1']; já se for '2.' retorna ['2', '']
        secao_corrente = secoes_candidatas[i][0].split('.')
        proxima_secao = secoes_candidatas[i+1][0].split('.')

        # Trata os casos de seções candidatas que não possuem '.', exemplo: 1, 2, 3, 20
        # Obs.: Para não dar erro de índice inexistente
        if len(secao_corrente) == 1:
            secao_corrente.append('')

        if len(proxima_secao) == 1:
            proxima_secao.append('')

        # Verifica comparando com a seção corrente ou com a próxima seção. Deve cumprir requisitos que
        # indicam que a seção que está sendo verificada é uma nova seção ou sequência de uma seção anterior
        # - Exemplos de novas seções: 1.; 1.1; 2.1 | Exemplos de próximas seções: 1.2; 1.3; 2.4; 2.5
        if secao_corrente[0] == ultima_secao_validada[0]:

            # Para evitar erro nas conversões para 'int'
            if secao_corrente[1] != '' and ultima_secao_validada[1] != '':

                # Verifica se é sequência da última seção validada ou se é o segundo nível de uma seção.
                # Exemplo de seções com o mesmo segundo nível: ['1.1.1', '1.1.2', '1.1.3'] todas derivam da '1.1.'
                if int(secao_corrente[1]) - 1 == int(ultima_secao_validada[1]) or \
                        secao_corrente[1] == ultima_secao_validada[1]:
                    sessao_valida = True

            # Trata os casos de seções que são sequências de seções terminadas com '.' ou quando acontece um
            # reinício de seção após uma seção '1'. Exemplo: ['1.', '1.1', '1.3', '1.'(reinício), '1.1']
            elif secao_corrente[1] == '1' or secao_corrente[0] == '1':
                sessao_valida = True

        # Verifica se é um início de seção do tipo 'x.', exemplos: 1.; 2.; 10.
        elif secao_corrente[0] == proxima_secao[0] and secao_corrente[1] == '' and proxima_secao[1] == '1':
            sessao_valida = True

        # Verifica se é um início de seção do tipo 'x.1', exemplos: 1.1; 2.1; 10.1
        elif secao_corrente[0] == proxima_secao[0] and secao_corrente[1] == '1' and proxima_secao[1] == '2':
            sessao_valida = True

        # Verifica, se mesmo não se encaixando com as regras anteriores, é um início de seção do tipo 'x.1'
        elif secao_corrente[1] == '1':
            sessao_valida = validar_secao_repescagem(secoes_candidatas, secao_corrente, i + 1)

        if sessao_valida:
            secoes_extraidas.append(secoes_candidatas[i])
            ultima_secao_validada = secao_corrente

    # Assume que a última seção candidata é válida, pois não tem como validar com o mesmo nível de certeza das outras
    if secoes_candidatas:
        secoes_extraidas.append(secoes_candidatas[-1])

    return secoes_extraidas


def extrair_descricao(secao_inicial, secao_final, termos):
    """
    Extrai a descrição entre duas seções/subseções
        :param secao_inicial: A seção/subseção a qual a descrição pertence
        :param secao_final: A seção/subseção que indicará o fim da descrição
        :param termos: Texto de onde a descrição será extraída
        :return: Descrição extraida do texto
    """
    qtd_maxima_termos_ultima_secao = 300  # Quantos termos serão lidos caso seja a última seção do documento
    descricao = []

    # Pega o índice da primeira ocorrência da seção inicial no texto
    index_secao_inicial = termos.index(secao_inicial)

    index_secao_final = []

    # Se a seção não é a última do documento
    if secao_final != '-1.':
        # Caso no texto existam mais de uma ocorrência da seção final, pega os índices das primeiras
        # 'quantidade_maxima_termos_lidos' ocorrências
        if termos.count(secao_final) > 1:
            quantidade_termos_lidos = 0
            quantidade_maxima_termos_lidos = 300

            # Começa na primeira ocorrência e vai até o final da lista de termos ou até atingir o limite máximo
            # de termos lidos
            for i in range(termos.index(secao_final), len(termos)):
                if secao_final == termos[i]:
                    index_secao_final.append(i)

                quantidade_termos_lidos += 1

                if quantidade_termos_lidos > quantidade_maxima_termos_lidos:
                    break
        else:
            index_secao_final.append(termos.index(secao_final))
    else:
        # Escolhe quantos termos serão lidos caso a seção/subseção seja a última do edital
        index_secao_final.append(min(len(termos), qtd_maxima_termos_ultima_secao))

    # Pega todos os termos entre a primeira ocorrência da seção inicial e a última ocorrência da seção final
    for i in range(index_secao_inicial + 1, max(index_secao_final)):
        descricao.append(termos[i][0])  # termos[i][0] = Termo; termos[i][1] = Pág do documento onde o termo se encontra

    return ' '.join(descricao)


def preencher_descricao(secoes_extraidas, termos_no_doc):
    """
    Preenche as descrições das seções extraídas com base no documento
        :param secoes_extraidas: Seções extraídas que receberão as descrições
        :param termos_no_doc: Termos extraídos do Edital de compras lido
    """
    secao_inicial = None

    for i in range(len(secoes_extraidas) - 1):
        secao_inicial = secoes_extraidas[i]
        secao_final = secoes_extraidas[i+1]

        # >>AVISO: A inserção abaixo causa um efeito colateral:
        # Os elementos da lista de seções candidatas serão alterados!!!
        secao_inicial.append(extrair_descricao(secao_inicial, secao_final, termos_no_doc))

    if secao_inicial:
        # Preenche a última seção da lista de seções extraídas
        secoes_extraidas[-1].append(extrair_descricao(secao_inicial, '-1.', termos_no_doc))
    elif len(secoes_extraidas) == 1:
        secoes_extraidas[0].append('')  # Evita erro de índice na função "agrupar_secoes"


def agrupar_secoes(secoes_extraidas):
    """
    Agrupa as seções e cria um objeto para cada seção agrupada
        :param secoes_extraidas: Seções que foram extraídas do documento
        :return: Lista contendo as seções agrupadas
    """
    # Permite agrupar a partir da seção que está na posição 0 da primeira lista de seções extraídas
    ultima_secao_lida = '0'

    secao = None
    secoes_agrupadas = []

    for s in secoes_extraidas:
        # Se a seção candidata tiver '.', vai retornar uma lista com a seçao e a subseção:
        # => Ex.: para '2.1' retorna ['2', '1']; já se for '2.' retorna ['2', '']
        # Obs.: secao_atual[0] guardará a seção para ser comparada no 'if' a seguir
        secao_atual = s[0].split('.')

        # Se for uma nova seção, instancia e inicializa um objeto para esta seção
        if secao_atual[0] != ultima_secao_lida:
            if ultima_secao_lida != '0':
                secoes_agrupadas.append(cp.deepcopy(secao))

            ultima_secao_lida = secao_atual[0]
            secao = Secao(s[0] + ' ')  # Para evitar erro na hora de criar o mapeamento ao salvar no Elasticsearch
            secao.titulo = s[2]
            secao.inserir_pagina(s[1])
        else:  # Senão, atualiza a lista de subseções do objeto que contém a seção
            subsecao = Subsecao(s[0] + ' ')  # Para evitar erro na hora de criar o mapeamento ao salvar no Elasticsearch
            subsecao.descricao = s[2]
            subsecao.pagina = s[1]
            secao.inserir_subsecao(cp.deepcopy(subsecao))

            if s[1] not in secao.paginas:
                secao.inserir_pagina(s[1])

    return secoes_agrupadas
