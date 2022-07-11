# ----------------------------------------------------------------
# Funções para conversão de arquivos anotados no Doccano e
# exportados no formato JSONL para o formato CONLL
# ----------------------------------------------------------------

import json
import os
import magic
import platform
from sklearn.model_selection import train_test_split
from src.ambiente.parametros_globais import PERMISSION_ERROR, REN_CAMINHO_ARQ_CONF, FILE_NOT_FOUND_ERROR, \
    INVALID_CONTENT, VALUE_ERROR
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from src.modulos.ren.construtor_datasets import retirar_sentencas_similares


def fatiar_sentenca(sentenca, marcadores_entidades):
    """
    Fatia uma sentença com base nos marcadores dos labels e separas as entidades que receberam label, dos outros tokens
        :param sentenca: Sentença que será fatiada
        :param marcadores_entidades: Lista contendo listas com os marcadores de entidades
        :return: Lista contendo tuplas de fatias da sentença com suas respectivas tags
    """
    # Prepara um dicionário com os marcadores para auxiliar no fatiamento. Ficará com o formato conforme exemplo:
    # - Marcador original: [[0, 6, 'Organizacao'], [69, 79, 'Local']]
    # - Marcador auxiliar: {'0-6': 'Organizacao', '69-79': 'Local'}
    dict_marcadores_entidades = {str(m[0]) + '-' + str(m[1]): m[2] for m in marcadores_entidades}

    # Cria uma lista com os índices dos marcadores para auxiliar no fatiamento. Ficará com o formato conforme exemplo:
    # - Marcador original: [[0, 6, 'Organizacao'], [69, 79, 'Local']]
    # - lista auxiliar com os índices: [0, 0, 6, 69, 79, None]. Obs.: Inclusão do 0 e do None para ajudar no fatiamento
    lista_aux = [0]

    for m in marcadores_entidades:
        lista_aux.append(m[0])
        lista_aux.append(m[1])

    # Ordena a lista para evitar erros no fatiamento, pois o Doccano pode exportar a lista de marcadores fora de ordem.
    # Exemplo real de export da lista de marcadores fora de ordem:
    # {'id': 78, 'data': '14h em 12/09/17 Página 2', 'label': [[7, 15, 'Tempo'], [0, 3, 'Tempo']]}
    # Se utilizar a lista auxiliar com os marcadores fora de ordem, o fatiamento ficará errado!
    lista_aux.sort()

    lista_aux.append(None)

    # Fatia as sentenças e atribui os labels a cada token
    sentenca_fatiada = []

    # Percorre a lista axiliar e pega os marcadores de 2 em 2 (i e i+1) e utiliza como início (i) e fim (i+1) para
    # fatiar sentença e obter as entidades (obs.: Ainda não serão tokenizadas) e atribuir as tags correspondentes.
    # A tag 'O' não é informada pelo Doccano, ela é atribuida aqui nesta função para as entidades que não foram nomeadas
    for i in range(len(lista_aux) - 1):
        inicio = lista_aux[i]
        fim = lista_aux[i + 1]
        entidade = sentenca[inicio:fim]
        chave = str(inicio) + '-' + str(fim)
        tag = dict_marcadores_entidades[chave].upper() if chave in dict_marcadores_entidades else 'O'

        # Evita fatias vazias:
        # - no caso de inicio e fim iguais (0,0): Se fatiar assim vai retornar uma string vazia;
        # - caso a sentença termine com uma entidade diferente de 'O', exemplo: "hoje é dia 20/01/2022", nesta sentença
        #   a última entidade é uma data e o marcador de fim estará apontado para 21 (tamanho da sentença), logo, fatiar
        #   a partir da posição 21 retornará uma string vazia.
        if entidade != '':
            sentenca_fatiada.append((entidade, tag))

    return sentenca_fatiada


def distribuir_tags(sentenca_fatiada):
    """
    Distribui as tags entre os tokens da sentença fatiada e, caso for necessário, aninha as tags de entidades que
    possuem mais de um token
        :param sentenca_fatiada: Lista contendo tuplas de fatias da sentença com suas respectivas tags
        :return: Lista contendo tuplas de entidades com suas respectivas tags
    """
    entidades = []

    for fatia in sentenca_fatiada:
        # Obs.: fatia[0] = fatia da sentença; fatia[1] = tag referente à fatia
        entidade_tokens = fatia[0].split()

        if entidade_tokens:
            tag = 'B-' + fatia[1] if fatia[1] != 'O' else 'O'
            entidades.append((entidade_tokens[0], tag))

            if len(entidade_tokens) > 1:
                tag = 'I-' + fatia[1] if fatia[1] != 'O' else 'O'

                for e in entidade_tokens[1:]:
                    entidades.append((e, tag))

    return entidades


def carregar_arquivo(caminho):
    """
    Carrega as linhas de um arquivo no formato JSONL (Arquivo com sentenças anotadas e exportadas através do Doccano)
        :param caminho: Caminho do aquivo que será carregado
        :return: Linhas lidas e codificação do arquivo
    """
    # Verifica qual a codificação do arquivo
    try:
        if platform.system().lower() == 'windows':
            codificacao = magic.Magic(mime_encoding=True,
                                      magic_file="C:\\Windows\\System32\\magic.mgc").from_file(caminho)
        else:
            codificacao = magic.Magic(mime_encoding=True).from_file(caminho)
    except PermissionError:
        codificacao = 'utf-8'  # Assume que a codificação será 'utf-8'

    arq_json = None

    try:
        arq_json = open(caminho, 'r', encoding=codificacao)
    except PermissionError:
        print(f"Erro ao ler o arquivo '{caminho}'. Permissão de leitura negada!")
        return [], None
    except FileNotFoundError:
        print(f"\nErro ao ler o arquivo '{caminho}'. Arquivo não encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except LookupError:
        print(f"Falhou: A Codificação '{codificacao}' não é suportada!")
        return [], None

    linhas = []

    try:
        linhas = arq_json.readlines()
    except UnicodeDecodeError as e:
        print(f"Falha ao ler as linhas do arquivo. Erro: {e}")

    if arq_json:
        arq_json.close()

    return linhas, codificacao


def concatenar_ordenar_linhas(arq_1, arq_2):
    """
    Concatena e ordena as linhas de dois arquivos JSONL
        :param arq_1: linhas lidas do primeiro arquivo
        :param arq_2: linhas lidas do segundo arquivo
        :return: Lista com as linhas dos dois arquivos concatenadas e ordenadas
    """
    linhas_juntas = []

    # Obtém os IDs de cada linha do arquivo e cria tuplas auxiliares para facilitar a ordenação das linhas pelo ID
    for arq in [arq_1, arq_2]:
        for linha in arq:
            linhas_juntas.append((int(linha.split(",")[0].split(":")[1]), linha))

    linhas_juntas.sort()

    # Retira os IDs aulixiares e obtém as linhas ordenadas
    linhas_juntas_ordenadas = [linha[1] for linha in linhas_juntas]

    return linhas_juntas_ordenadas


def concatenar_arquivos_jsonl(caminho):
    """
    Concatena os arquivos JSON 'admin.jsonl' e 'unknown.jsonl' ordenando as linhas
        :param caminho: Caminho dos aquivos que serão verificados e concatenados se necessário
    """
    print("\n=> Concatenando e ordenando as linhas dos arquivos JSONL:\n")

    # obtém os caminhos das pastas recursivamente e os ordena
    caminhos_pastas = [pasta for pasta, subpastas, arquivos in os.walk(caminho)]
    caminhos_pastas.sort()

    arquivos_concatenar = []  # Guarda os arquivos que serão verificados e concatenados se necessário

    # Apura quais arquivos serão concatenados
    for pasta in caminhos_pastas:
        arq_admin = os.path.join(pasta, "admin.jsonl")
        arq_unknown = os.path.join(pasta, "unknown.jsonl")

        # Trata o caso de existir somente o arquivo "admin.jsonl" ou "unknown.jsonl"
        if os.path.exists(arq_admin) and os.path.exists(arq_unknown):
            arquivos_concatenar.append((pasta, arq_admin, arq_unknown))
        elif os.path.exists(arq_admin) and not os.path.exists(arq_unknown):
            arquivos_concatenar.append((pasta, arq_admin))
        elif not os.path.exists(arq_admin) and os.path.exists(arq_unknown):
            arquivos_concatenar.append((pasta, arq_unknown))

    # Concatena os arquivos
    for a in arquivos_concatenar:
        codificacao = None
        arq_admin_lido = None
        arq_unknown_lido = None
        arq_sozinho_lido = None  # Guardará ou o arquivo 'admin.jsonl' ou 'unknown.jsonl', caso tenha somente um deles

        if len(a) == 3:
            print(f"Concatenando e ordenando os arquivos: '{a[1]}' e '{a[2]}'...", end='', flush=True)
            arq_admin_lido, codificacao = carregar_arquivo(a[1])  # Assume que a codificação dos dois arquivos é a mesma
            arq_unknown_lido, _ = carregar_arquivo(a[2])

            if not arq_admin_lido or not arq_unknown_lido:
                print("Erro no carregamento das linhas. Verifique o conteúdo dos arquivos!")
                continue
        elif len(a) == 2:
            print(f"Somente carregando o arquivo '{a[1]}' pois só existe ele...", end='', flush=True)
            arq_sozinho_lido, codificacao = carregar_arquivo(a[1])

            if not arq_sozinho_lido:
                print(f"Erro no carregamento das linhas. Verifique o conteúdo do arquivo!")
                continue

        linhas_ordenadas = []

        if arq_admin_lido:
            linhas_ordenadas = concatenar_ordenar_linhas(arq_admin_lido, arq_unknown_lido)
        elif arq_sozinho_lido:
            linhas_ordenadas = arq_sozinho_lido

        if linhas_ordenadas:
            caminho_arq_concatenado = os.path.join(a[0], "concatenado.jsonl")
            arq_json_concatenado = None

            try:
                arq_json_concatenado = open(caminho_arq_concatenado, 'w', encoding=codificacao)
            except PermissionError:
                print(f"Erro ao criar o arquivo '{caminho_arq_concatenado}'. Permissão de escrita negada!\n")
                exit(PERMISSION_ERROR)
            except LookupError:
                print(f"Falhou: A Codificação '{codificacao}' não é suportada!")
                continue

            arq_json_concatenado.writelines(linhas_ordenadas)
            arq_json_concatenado.close()
            print(" OK!")


def carregar_jsonl(caminho):
    """
    Carrega os dados de um arquivo no formato JSONL (Arquivo com sentenças anotadas e exportadas através do Doccano)
        :param caminho: Caminho do aquivo que será carregado
        :return: Lista com tuplas com número da linha da sentença e dicionário contendo a sentença, marcação das
        entidades e tags, de cada uma das sentenças do arquivo
    """
    # Verifica qual a codificação do arquivo
    try:
        if platform.system().lower() == 'windows':
            codificacao = magic.Magic(mime_encoding=True,
                                      magic_file="C:\\Windows\\System32\\magic.mgc").from_file(caminho)
        else:
            codificacao = magic.Magic(mime_encoding=True).from_file(caminho)

    except PermissionError:
        codificacao = 'utf-8'  # Assume que a codificação será 'utf-8'

    print(f"Carregando o arquivo '{caminho}' (Codificação='{codificacao}')", end='')

    arq_json = None

    try:
        arq_json = open(caminho, 'r', encoding=codificacao)
    except PermissionError:
        print(f"(Erro ao ler o arquivo '{caminho}'. Permissão de leitura negada!", end='')
        return []
    except FileNotFoundError:
        print(f"\nErro ao ler o arquivo '{caminho}'. Arquivo não encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except LookupError:
        print(f"(Falhou: A Codificação '{codificacao}' não é suportada!", end='')
        return []

    sentencas = []
    linhas = []

    try:
        linhas = arq_json.readlines()
    except UnicodeDecodeError as e:
        print(f"Falhou: {e}", end='')

    for i in range(len(linhas)):
        try:
            sentencas.append((i+1, json.loads(linhas[i].strip('\n'))))  # Guarda também o número da linha
        except json.decoder.JSONDecodeError as e:
            print(f"Falhou. JSONL mal formado: {e}", end='')

    if arq_json:
        arq_json.close()

    print(" -> OK")

    return sentencas


def gerar_arquivo_conll(sentencas_com_tags, pasta_destino_dataset, tamanho_dataset_teste=0.0):
    """
    Gera um arquivo (ou mais, caso seja especificado o tamanho do dataset de teste) no formato CONLL
        :param sentencas_com_tags: Lista contendo listas de tuplas com tokens e suas respectivas tags. Cada uma dessas
                                   listas de tuplas representa uma sentença.
        :param pasta_destino_dataset: Pasta onde será gerado o arquivo CONLL
        :param tamanho_dataset_teste: Tamanho do dataset de teste. Obs.: O dataset de teste será subdivido em teste e
                                      validação: 50% teste e 50% validação
    """
    print("\n=> Gerando arquivo(s) no formato CONLL... ", end='')

    datasets = {}

    if tamanho_dataset_teste == 0.0:
        datasets = {"dataset_ner.conll": sentencas_com_tags}
    elif tamanho_dataset_teste > 0.0:
        # Divide e prepara os datasets para a geração dos arquivos CONLL
        treino = None
        teste = None
        validacao = None

        try:
            treino, teste = \
                train_test_split(sentencas_com_tags, test_size=tamanho_dataset_teste, shuffle=False, random_state=44)
            teste, validacao = train_test_split(teste, test_size=0.5, shuffle=False, random_state=44)
        except ValueError as e:
            print(f"-> ERRO: Arquivos CONLL não gerados. Não foi possível dividir o dataset. Mensagem do "
                  f"'train_test_split': {e}")
            exit(VALUE_ERROR)

        datasets = {"dataset_ner_train.conll": treino, "dataset_ner_test.conll": teste,
                    "dataset_ner_val.conll": validacao}

        print(f"\n\nATENÇÃO: O dataset foi dividido (tamanho_dataset_teste={tamanho_dataset_teste}) e as partes ficaram"
              f" com as seguintes quantidades de sentenças:\n\n - Treino = {len(treino)}\n - Teste = {len(teste)}"
              f"\n - Validação = {len(validacao)}\n")
    else:
        print(f"-> ERRO: Arquivos CONLL não gerados. O tamanho '{tamanho_dataset_teste}' não é válido para o dataset "
              f"de teste!\n")
        exit(INVALID_CONTENT)

    for nome_arq, sentencas_com_tags in datasets.items():
        caminho_destino_dataset = os.path.join(pasta_destino_dataset, nome_arq)
        arq_dataset = None

        try:
            arq_dataset = open(caminho_destino_dataset, 'w')
        except PermissionError:
            print(f"\nErro ao criar o arquivo de dataset na pasta '{pasta_destino_dataset}'. Permissão de gravação "
                  f"negada!\n")
            exit(PERMISSION_ERROR)

        for sentenca in sentencas_com_tags:
            for token in sentenca:
                arq_dataset.write(f"{token[0]} {token[1]}\n")

            arq_dataset.write("\n")

        if arq_dataset:
            arq_dataset.close()

    print("-> OK")


def gerar_estatisticas(qtd_arquivos_processados, sentencas_com_tags):
    """
    Gera as estatísticas do processo de conversão dos arquivos anotados para o formato CONLL
        :param qtd_arquivos_processados: Quantidade de arquivos processados
        :param sentencas_com_tags: Lista contendo listas de tuplas com tokens e suas respectivas tags. Cada uma dessas
                                   listas de tuplas representa uma sentença.
    """
    qtd_sentencas = len(sentencas_com_tags)
    total_tokens = 0
    qtd_entidades = 0

    for sentenca in sentencas_com_tags:
        total_tokens += len(sentenca)

        # Contabiliza só as entidades que tem tags começadas com 'B-'
        for token in sentenca:
            if "B-" in token[1]:
                qtd_entidades += 1

    # Para evitar a divisão por zero
    if total_tokens == 0:
        print("\nNão foi possível gerar as estatísticas porque não há tokens!")
        return

    print("\n\n => Estatísticas do processo de conversão dos arquivos anotados\n")
    print("\tQuantidade de arquivos processados..................:", qtd_arquivos_processados)
    print("\tQuantidade de sentenças.............................:", qtd_sentencas)
    print("\tTotal de tokens.....................................:", total_tokens)
    print("\tQuantidade de entidades (exceto tag 'O')............:", qtd_entidades)
    print(f"\tMédia de sentenças por arquivo......................: {(qtd_sentencas/qtd_arquivos_processados):.2f}")
    print(f"\tMédia de tokens por arquivo.........................: {(total_tokens/qtd_arquivos_processados):.2f}")
    print(f"\tMédia de tokens por sentença........................: {(total_tokens/qtd_sentencas):.2f}")
    print(f"\tMédia de entidades (exceto tag 'O') por arquivo.....: {(qtd_entidades/qtd_arquivos_processados):.2f}")
    print(f"\tMédia de entidades (exceto tag 'O') por sentença....: {(qtd_entidades/qtd_sentencas):.2f}")
    print(f"\t% de tokens que são entidades (exceto tag 'O')......: {((qtd_entidades/total_tokens) * 100):.2f}%")


def contabilizar_entidades(caminho, entidades_por_arquivo):
    """
    Contabiliza as entidades constantes nos arquivos. Mostra sumário na tela, com o total de tokens por entidade,
    grava um arquivo com o total de cada tipo de tag encontrada nos arquivos e grava um outro arquivo com os exemplos
    de entidades organizados por tag
        :param caminho: Caminho onde o arquivo com os detalhes será gravado
        :param entidades_por_arquivo: Dicionário cuja chave é o nome do arquivo e o conteúdo é outro dicionário cuja
                                      chave é a linha+id e o conteúdo uma lista de tuplas de tokens e suas respectivas
                                      tags
    """
    tokens_por_arquivo = {}  # Guarda os tokens diferentes de 'O' encontrados em cada arquivo. Organiza por arquivo.
    total_tags = {}  # Guarda o total de cada tipo de tag encontrada nos arquivos. Organiza por nome da tag.
    exemplos_entidades_por_tag = {}  # Guarda os exemplos de entidades por tag

    for a, entidades_por_linha in entidades_por_arquivo.items():
        tokens_por_arquivo[a] = []
        tokens_por_tag_linha = {}

        for linha_id, entidades in entidades_por_linha.items():
            for e in entidades:
                inicio_tag = e[1][:2]
                chave = e[1][2:]  # Pega o nome da tag sem o B-

                if inicio_tag == 'B-' or inicio_tag == 'I-':
                    # Guarda os tokens marcados para o arquivo e a referida linha onde eles se encontram
                    if chave in tokens_por_tag_linha:
                        tokens_por_tag_linha[chave].append((linha_id, e))
                    else:
                        tokens_por_tag_linha[chave] = [(linha_id, e)]

                    # Guarda os exemplos por tag
                    if chave in exemplos_entidades_por_tag:
                        exemplos_entidades_por_tag[chave].append((e[0], inicio_tag))
                    else:
                        exemplos_entidades_por_tag[chave] = [(e[0], inicio_tag)]

                # Contabiliza o total de cada tipo de tag
                if inicio_tag == 'B-':
                    if chave in total_tags:
                        total_tags[chave] += 1
                    else:
                        total_tags[chave] = 1

        tokens_por_arquivo[a].append(tokens_por_tag_linha)

    # Gera o arquivo com os dados de tokens por arquivo
    arq = None
    caminho_arq = os.path.join(caminho, "tokens_anotados_por_arquivo.txt")

    try:
        arq = open(caminho_arq, 'w')
    except PermissionError:
        print(f"\nErro ao salvar os tokens anotados por arquivo no caminho '{caminho}'. Permissão de escrita negada!\n")
        exit(PERMISSION_ERROR)

    for a, lst_tokens_por_tag_linha in tokens_por_arquivo.items():
        arq.write(f"# Arquivo: {a}")

        for tokens_por_tag_linha in lst_tokens_por_tag_linha:
            for tag, tokens in tokens_por_tag_linha.items():
                arq.write(f"\n\n - Tag {tag}:\n")

                for t in tokens:
                    if t[1][1][:2] == "B-":
                        arq.write(f"\n   {t[0]} -> {t[1][0]}")
                    else:
                        arq.write(f" {t[1][0]}")

            arq.write("\n\n")

    arq.close()

    # Gera o arquivo com os exemplos de entidades por tag
    arq = None
    caminho_arq = os.path.join(caminho, "exemplos_de_entidades_por_tag.txt")

    try:
        arq = open(caminho_arq, 'w')
    except PermissionError:
        print(f"\nErro ao salvar os exemplos de entidades no caminho '{caminho}'. Permissão de escrita negada!\n")
        exit(PERMISSION_ERROR)

    for tag, lst_entidades_por_tag in exemplos_entidades_por_tag.items():
        arq.write(f"- Label {tag}:\n\n")

        entidades_aninhadas = []
        ent_aninhada = ''

        for e in lst_entidades_por_tag:
            if e[1] == "B-":
                if ent_aninhada != '':
                    entidades_aninhadas.append(ent_aninhada)

                ent_aninhada = e[0]
            else:
                ent_aninhada += f" {e[0]}"

        # Inclui a última entidade aninhada apurada
        if ent_aninhada != '':
            entidades_aninhadas.append(ent_aninhada)

        entidades_aninhadas = list(set(entidades_aninhadas))
        entidades_aninhadas.sort()

        for e in entidades_aninhadas:
            arq.write(f"{e}\n")

        arq.write("\n\n")

    arq.close()

    print("\n\n **** Sumarização dos tipos de tags e total de entidades de cada uma ****\n")
    for tag, total in total_tags.items():
        print(f"\t                 {tag} = {total}")


def converter_jsonl_conll(retirar_sentencas_semelhantes=False, escopo_global_sentencas=True, tamanho_dataset_teste=0.0,
                          concatenar_arquivos=False):
    """
    Converte as sentenças anotadas no formato JSONL para o formato CONLL e grava num arquivo de dataset
        :param retirar_sentencas_semelhantes: Indica se as sentenças semelhantes devem ser retiradas no momento de
                                              geração dos datasets
        :param escopo_global_sentencas: Escopo para a análise de sentenças. Se True, fará a comparação com todos os
                                        documentos, caso contrário a comparação será somente no próprio documento
        :param tamanho_dataset_teste: Tamanho do dataset de teste. Obs.: O dataset de teste será subdivido em teste e
                                      validação: 50% teste e 50% validação
        :param concatenar_arquivos: Indica se os arquivos JSONL serão concatenados e ordenados
    """
    # Obtém o caminho do arquivo de configuração para montar o caminho completo
    caminho_arquivo_configuracao = REN_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao = 'param_ren.conf'
    arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

    conf = inicializar_parametros('ren', arq_conf)

    # Obtém os parâmetros de configuração do módulo
    parametros = {'caminho_arq_conf': arq_conf,
                  'p_caminho_arq_sentencas': conf.obter_valor_parametro('p_caminho_arq_sentencas'),
                  'p_caminho_sentencas_base': conf.obter_valor_parametro('p_caminho_sentencas_base')}

    validar_pastas(parametros)

    caminho = parametros['p_caminho_arq_sentencas']
    sentencas_com_tags = []
    entidades_por_arquivo = {}  # Guarda as entidades por arquivo. Objetivo: de fazer uma contabilidade das entidades

    if concatenar_arquivos:
        concatenar_arquivos_jsonl(caminho)
        chave_busca = "concatenado.jsonl"
    else:
        chave_busca = "admin.jsonl"

    # obtém os caminhos dos arquivos recursivamente e os ordena
    arquivos = [os.path.join(pasta, a) for pasta, subpastas, arquivos in os.walk(caminho) for a in arquivos]
    arquivos.sort()

    qtd_arquivos_encontrados = 0
    qtd_arquivos_processados = 0

    print("\n                  ********* Convertendo sentenças anotadas para o formato CONLL *********\n")

    # Guarda as sentenças por arquivo, utilizando o nome do arquivo como chave
    arquivos_sentencas = {}

    print("=> Carga dos arquivos:\n")

    for a in arquivos:
        if chave_busca in a:
            qtd_arquivos_encontrados += 1
            arquivos_sentencas[a] = carregar_jsonl(a)

    if retirar_sentencas_semelhantes:
        arquivos_sentencas = \
            retirar_sentencas_similares(arquivos_sentencas, parametros['p_caminho_sentencas_base'],
                                        "SentencasBaseCONLL.pkl", parametros['p_caminho_arq_sentencas'],
                                        reprocessar=True, escopo_global_sentencas=escopo_global_sentencas, limiar=0.90)

    print("\n=> Processamento dos arquivos:\n")

    for a, sentencas_json in arquivos_sentencas.items():
        encontrou_campos = False
        print(f"Processando o arquivo '{a}' ", end='')

        if sentencas_json:
            entidades_por_arquivo_linha = {}  # Guarda as entidades do arquivo organizadas por linha
            qtd_sentencas_validas = 0

            for sj in sentencas_json:
                if 'data' in sj[1] and 'label' in sj[1] and 'id' in sj[1]:
                    encontrou_campos = True
                    qtd_sentencas_validas += 1
                    sentenca_fatiada = fatiar_sentenca(sj[1]['data'], sj[1]['label'])
                    entidades = distribuir_tags(sentenca_fatiada)
                    sentencas_com_tags.append(entidades)
                    chave = f"Linha: {sj[0]}; ID: {sj[1]['id']}"
                    entidades_por_arquivo_linha[chave] = entidades

            if encontrou_campos:
                entidades_por_arquivo[a] = entidades_por_arquivo_linha
                qtd_arquivos_processados += 1
                print(f"(Qtd. sentenças com anotações válidas = {qtd_sentencas_validas}) -> OK!")
            else:
                print(f"Falhou: Alguma(s) das chaves 'id', data' e 'label' não foram encontradas no arquivo!) -> "
                      f"ERRO!")
        else:
            print(") -> ERRO!")

    if qtd_arquivos_processados > 0:
        gerar_arquivo_conll(sentencas_com_tags, caminho, tamanho_dataset_teste=tamanho_dataset_teste)
        gerar_estatisticas(qtd_arquivos_processados, sentencas_com_tags)
        contabilizar_entidades(caminho, entidades_por_arquivo)

        # Gera um arquivo com os parâmetros de processamento que foram utilizados na geração dos datasets
        arq_parametros_utilizados = None
        nome_arq_parametros_utilizados = os.path.join(caminho, 'parametros_utilizados.txt')

        try:
            arq_parametros_utilizados = open(nome_arq_parametros_utilizados, 'w')
        except PermissionError:
            print(f"\nErro ao criar o arquivo com os parâmetros utilizados na geração dos arquivos CONLL. Permissão de "
                  f"gravação negada na pasta '{caminho}'!\nProcessamento abortado.")
            exit(PERMISSION_ERROR)

        arq_parametros_utilizados.write(f"# Parâmetros utilizados para geração dos arquivos CONLL:\n"
                                        f"\nPasta destino: '{caminho}'"
                                        f"\nRetirar sentenças semelhantes: {retirar_sentencas_semelhantes}"
                                        f"\nEscopo global de sentenças: {escopo_global_sentencas}"
                                        f"\nLimiar para definição de sentenças similares: 0.9"
                                        f"\nTamanho do dataset de teste: {tamanho_dataset_teste}"
                                        f"\nConcatenar arquivos: {concatenar_arquivos}")
        arq_parametros_utilizados.close()
        print(f"\n - Os arquivos foram gerados na pasta '{caminho}'\n")

    if qtd_arquivos_encontrados > 0:
        if qtd_arquivos_encontrados != qtd_arquivos_processados:
            print("\n\n                 *** ATENÇÃO ***\n")
            print("-> Nem todos os arquivos encontrados foram processados. Favor verificar!\n")
            print(f"   Qtd. de arquivos encontrados..: {qtd_arquivos_encontrados}")
            print(f"   Qtd. de arquivos processados..: {qtd_arquivos_processados}")
            print(f"   Qtd. de arquivos com erro.....: {qtd_arquivos_encontrados - qtd_arquivos_processados}")
    else:
        print(f"\nNão foram encontrados arquivos '{chave_busca}' no caminho '{caminho}'!")


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    converter_jsonl_conll(retirar_sentencas_semelhantes=False, escopo_global_sentencas=True, tamanho_dataset_teste=0.0,
                          concatenar_arquivos=False)
