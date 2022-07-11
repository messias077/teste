# ----------------------------------------------------------------
# Funções para construção de datasets, com base nos documentos
# persistidos no banco, para tarefas de PLN.
# ----------------------------------------------------------------
import spacy
import os
import pickle
import numpy as np
import src.classes.persistencia.serializacao as ser
from unicodedata import normalize
from src.classes.persistencia.cliente import ClienteGenerico
from src.ambiente.parametros_globais import PERMISSION_ERROR, SPACY_MODEL_NOT_FOUND_ERROR, \
    FILE_NOT_FOUND_ERROR, INVALID_CONTENT
from src.ml.classificador import carregar_modelo, tratar_strings


def obter_metadados_documentos(c_mongo_meta, codproc, reprocessar=False):
    """
    Obtém os metadados dos documentos que precisam ser processados
        :param c_mongo_meta: Base de dados onde estão os metadados dos documentos
        :param codproc: Código de processamento para realização do filtro na busca
        :param reprocessar: Indica se deve fazer o reprocessamento dos documentos, caso já tenha sido gerado o dataset
        :return: Metadados dos documentos que ainda não foram processados. Se for para reprocessar, retorna todos os
                 que atendam ao filtro 'codproc'
    """
    # Obtém os metadados dos documentos que serão processados
    if not reprocessar:
        # Traz todos os documentos que não tem o 'codproc'
        doc_metadados_js = c_mongo_meta.buscar_todos('col_metadados_docs', 'Documento__cod_processamento',
                                                     f"^((?!{codproc}).)*$")
    else:
        doc_metadados_js = c_mongo_meta.buscar_todos('col_metadados_docs', 'Documento__cod_processamento', codproc)

    return list(doc_metadados_js)


def obter_subsecoes_documentos(doc_metadados_js):
    """
    Obtém as subseções dos documentos que precisam ser processados para criação do dataset
        :param doc_metadados_js: Metadados dos documentos que serão processados
        :return: Dicionário cuja chave é o código do arquivo e o valor é uma lista contendo as subseções do documento
    """
    print(f"\n=> Etapa: Obtendo subseções...", end='', flush=True)

    c_mongo_doc = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_documentos')
    documentos_subsecoes = {}  # A chave é o código do arquivo e o valor é uma lista contendo as subseções do documento

    # Obtém os documentos (através dos metadados) que serão processados
    for doc_meta in doc_metadados_js:
        doc = c_mongo_doc.buscar_um('col_editais', 'Edital__codigo_arq', doc_meta['Documento__codigo_arq'])
        subsecoes = []

        if doc:
            doc_desserializado = ser.desserializar(doc)

            for s in doc_desserializado.secoes:
                for sb in s.subsecoes:
                    subsecoes.append(sb.descricao)

            documentos_subsecoes[doc_meta['Documento__codigo_arq']] = subsecoes

    c_mongo_doc.fechar_conexao()
    print(" -> Pronto!")
    return documentos_subsecoes


def classificar_subsecoes(documentos_subsecoes, filtro_retorno=None):
    """
    Classifica as subseções em dois tipos: Jurídica (JUR) ou técnica (TEC)
        :param documentos_subsecoes: Dicionário contendo os documentos como chave e uma lista se subseções como valor
        :param filtro_retorno: Filtra o retorno da função por um rótulo específico
        :return: nome do modelo e (Se filtro_retorno for None, dicionário com o código do arquivo como chave e como
                 valor lista de tuplas contendo a subseção e a classificação dela, caso contrário, dicionário com o
                 código do arquivo como chave e como valor lista com as subseções classificadas e filtradas)
    """
    documentos_subsecoes_classificadas = {}
    remover_stop_words = True

    # Escolhe o modelo de classificador para classificar as seções
    modelo = carregar_modelo('RandomForestClassifier', 'modelos')

    print("\n=> Etapa: Classificar subseções.\n")
    total = len(documentos_subsecoes)
    cont = 1
    qtd_caracteres_limpar = 0  # Ajuda na limpeza dos códigos dos arquivos que já foram impressos na tela

    for cod_arq, subsecoes in documentos_subsecoes.items():
        print(f" - Arquivo: {cont}/{total} => {cod_arq + qtd_caracteres_limpar * ' '}", end='\r', flush=True)

        # Garante que não vai ficar lixo na tela, pois no mínimo vai limpar o tamanho do último código de arquivo
        qtd_caracteres_limpar = len(cod_arq)

        # Prepara as subseções e faz a predição dos rótulos
        subsecoes_aux = np.array(subsecoes)
        subsecoes_aux = subsecoes_aux.reshape((len(subsecoes_aux), 1))
        subsecoes_aux = tratar_strings(subsecoes_aux, remover_stop_words=remover_stop_words)
        rotulos = modelo.predict(subsecoes_aux)

        if rotulos:
            subsecoes_classificadas = []

            if filtro_retorno:
                for i in range(len(subsecoes)):
                    if rotulos[i] == filtro_retorno:
                        subsecoes_classificadas.append(subsecoes[i])
            else:
                for i in range(len(subsecoes)):
                    subsecoes_classificadas.append((subsecoes[i], rotulos[i]))

            documentos_subsecoes_classificadas[cod_arq] = subsecoes_classificadas

        cont += 1
    print("\n -> Pronto!")
    return modelo.nome, documentos_subsecoes_classificadas


def dividir_em_sentencas(documentos_subsecoes, tamanho_minimo_sentenca):
    """
    Divide as subseções em sentenças
        :param documentos_subsecoes: Dicionário cuja chave é o código do arquivo e o valor lista de subseções que serão
                                     divididas em sentenças
        :param tamanho_minimo_sentenca: Sentenças com tamanho menor que este parâmetro serão descartadas
        :return: Dicionário cuja chave é o código do arquivo e o valor é uma lista de sentenças
    """
    print("\n=> Etapa: Dividir em sentenças.\n")

    nlp = None

    modelo_spacy = 'pt_core_news_lg'
    print(f" - Carregando o modelo '{modelo_spacy}' do Spacy... ", end='', flush=True)

    try:
        nlp = spacy.load(modelo_spacy)
    except OSError:
        print(f"\n\n    ERRO: Não foi possível encontrar o modelo '{modelo_spacy}'. Confira o nome do modelo. Caso "
              f"esteja correto, faça o download dele utilizando o comando 'python -m spacy download {modelo_spacy}' "
              f"num terminal.\n")
        exit(SPACY_MODEL_NOT_FOUND_ERROR)

    print("-> Pronto!")

    documentos_sentencas = {}
    cont = 1
    total = len(documentos_subsecoes)

    print("\n - Preparando para gerar os arquivos:\n")

    for cod_arq, subsecoes in documentos_subsecoes.items():
        sentencas = []
        print(f"   Documento ({cont}/{total}): {cod_arq} ", end='', flush=True)

        for sub in subsecoes:
            nlp_doc = nlp(sub)

            for sent in nlp_doc.sents:
                lst_tokens = [t.text for t in sent]

                if len(lst_tokens) >= tamanho_minimo_sentenca:
                    sentencas.append(" ".join(lst_tokens))

        documentos_sentencas[cod_arq] = sentencas
        print("-> OK")
        cont += 1

    return documentos_sentencas


def marcar_documentos_processados(c_mongo_meta, doc_metadados_js, codproc, reprocessado=False):
    """
    Marca os documentos que foram processados
        :param c_mongo_meta: Base de dados onde estão os metadados dos documentos
        :param doc_metadados_js: Lista com os documentos que foram processados
        :param codproc: Código de processamento
        :param reprocessado: Indica se foi feito o reprocessamento dos documentos
        :return: Lista com códigos de arquivos que tiveram erro na marcação. Se tudo ocorrer bem, esta lista será vazia
    """
    doc_erros = []  # Guarda os códigos dos documentos caso haja erro na marcação do processamento

    # Se não for reprocessamento, atualiza os códigos de processamento. Se for reprocessamento, não atualiza a lista,
    # pois o código já se encontra nela.
    if not reprocessado:
        for doc_meta in doc_metadados_js:
            doc_cod_processamento = doc_meta['Documento__cod_processamento']

            # Se o documento ainda não foi processado com algum código de processamento, retira o código 'a processar'
            # e grava o 'codproc'
            if 'a processar' in doc_cod_processamento:
                doc_cod_processamento = codproc
            else:  # Se já foi processado com algum código, acrescenta o 'codproc' na string de códigos de processamento
                doc_cod_processamento += f", {codproc}"

            resultado = c_mongo_meta.alterar('col_metadados_docs', 'Documento__codigo_arq',
                                             doc_meta['Documento__codigo_arq'], 'Documento__cod_processamento',
                                             doc_cod_processamento)

            if not resultado:
                doc_erros.append(doc_meta['Documento__codigo_arq'])

    return doc_erros


def salvar_sentencas_base(caminho, nome_arquivo, sentencas_base):
    """
    Salva as sentenças base para auxiliar na verificação de documentos futuros
        :param caminho: Caminho onde as sentenças base serão salvas
        :param nome_arquivo: Nome do arquivo onde as sentenças base serão salvas
        :param sentencas_base: Lista contendo as sentenças base que serão salvas
    """
    arq = None
    caminho_arq_sentencas_base = os.path.join(caminho, nome_arquivo)

    try:
        arq = open(caminho_arq_sentencas_base, 'wb')
    except FileNotFoundError:
        print(f"\nErro ao salvar as sentenças base. O caminho '{caminho}' não existe!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao salvar as sentenças base no caminho '{caminho}'. Permissão de escrita negada!\n")
        exit(PERMISSION_ERROR)

    pickle.dump(sentencas_base, arq)
    arq.close()


def carregar_sentencas_base(caminho, nome_arquivo):
    """
    Carrega as sentenças base para auxiliar na verificação de documentos
        :param caminho: Caminho onde as sentenças base foram salvas
        :param nome_arquivo: Nome do arquivo contendo as sentenças base
        :return: Lista contendo as sentenças base que foram carregadas, ou, caso o arquivo não exista, uma lista vazia
    """
    arq = None
    caminho_arq_sentencas_base = os.path.join(caminho, nome_arquivo)

    try:
        arq = open(caminho_arq_sentencas_base, 'rb')
    except FileNotFoundError:
        print(f"\nErro ao carregar as sentenças base. O arquivo '{caminho_arq_sentencas_base}' não foi encontrado! "
              f"Retornando uma base vazia...\n")
        return []
    except PermissionError:
        print(f"\nErro ao carregar as sentenças base do caminho '{caminho_arq_sentencas_base}'. Permissão de leitura "
              f"negada!\n")
        exit(PERMISSION_ERROR)

    sentencas_base = pickle.load(arq)
    arq.close()
    return sentencas_base


def retirar_sentencas_similares(documentos_sentencas, caminho_sentencas_base, nome_arq_sents_base, caminho_relatorio,
                                reprocessar=False, escopo_global_sentencas=True, limiar=0.90):
    """
    Retira sentenças similares de documentos, com base no Índice de Jaccart e um limiar.
        :param documentos_sentencas: Dicionário onde a chave é o código do arquivo e o valor é uma lista de sentenças
        :param caminho_sentencas_base: Caminho para obtenção e/ou gravação das sentenças base
        :param nome_arq_sents_base: Nome do arquivo de sentenças base
        :param caminho_relatorio: Caminho onde será gerado o relatório com os detalhes das sentenças descartadas
        :param reprocessar: Indica se deve fazer o reprocessamento dos documentos, caso já tenha sido construido um
                            dataset antes
        :param escopo_global_sentencas: Escopo para a análise de sentenças. Se True, fará a comparação com todos os
                                        documentos, caso contrário a comparação será somente no próprio documento
        :param limiar: Limiar para o descarte. Caso o Índice de Jaccart fique acima do limiar a sentença é descartada
        :return: documentos_sentencas sem as sentenças similares, se houverem
    """
    print(f"\n=> Etapa: Retirando sentenças similares (escopo_global_sentencas={escopo_global_sentencas}; "
          f"limiar={limiar}).\n")

    # Guarda informações das sentenças de todos os documentos para avaliação da similaridade.
    # Estrutura de cada sentença base da lista: ("nome do arquivo", sentença, set da sentença tratada). Exemplo:
    # ("Edital_001.pdf", "O índice de reajuste não foi o maior de 2021",
    # {'2021', 'de', 'foi', 'maior', 'nao', 'o', 'reajuste', 'indice'})
    # Obs.: Não carrega o arquivo de sentenças base se for reprocessar, pois se carregar, todas as sentenças serão
    # descartadas!
    if escopo_global_sentencas and not reprocessar:
        sentencas_base = carregar_sentencas_base(caminho_sentencas_base, nome_arq_sents_base)
    else:
        sentencas_base = []

    cont = 1
    qtd_documentos = len(documentos_sentencas)
    sentencas_descartadas_por_arquivo = {}
    total_global_sentencas = 0
    total_global_sentencas_descartadas = 0

    for cod_arq, sentencas in documentos_sentencas.items():
        if not escopo_global_sentencas:
            sentencas_base = []

        print(f"   Documento ({cont}/{qtd_documentos}): {cod_arq} ", end='', flush=True)

        sentencas_a_inserir = []
        sentencas_descartadas = []

        for sent_aval in sentencas:
            tipo_sent_aval = type(sent_aval)

            if tipo_sent_aval is not str and tipo_sent_aval is not tuple:
                print(f"\n\nO Formato '{tipo_sent_aval}' não é aceito para as sentenças. Sentença errada: '{sent_aval}'"
                      f". Formatos aceitos: 'str' e 'tuple'.\n")
                exit(INVALID_CONTENT)

            sent_inserir = sent_aval

            # Trata o caso das sentenças no formato JSON vindas da rotina para conversão dos arquivos anotados no
            # Doccano para o formato CONLL. Neste caso, sent_aval será uma tupla contendo na posição 0 o número da linha
            # da sentença no arquivo de sentenças anotadas e na posição 1 a sentença no formato JSON
            if tipo_sent_aval is tuple:
                sent_aval = sent_aval[1]['data']

            if len(sent_aval) == 0:
                continue

            # Retira acentos, cedilhas, etc... (transforma em codificação ASCII) para considerar palavras acentuadas
            # corretamente iguais a outras que não foram
            sent_aval_aux = normalize('NFKD', sent_aval).encode('ASCII', 'ignore').decode('ASCII')

            sent_aval_aux = set(sent_aval_aux.lower().split())
            inserir = True

            # Estrutura da sent_base do for abaixo: ("nome do arquivo", sentença, set da sentença tratada). Exemplo:
            # ("Edital_001.pdf", "O índice de reajuste não foi o maior de 2021",
            # {'2021', 'de', 'foi', 'maior', 'nao', 'o', 'reajuste', 'indice'})

            sentenca_semelhante = None
            ind_jaccart_sentenca_descartada = None

            for sent_base in sentencas_base:
                ind_jaccart = len(sent_base[2].intersection(sent_aval_aux)) / len(sent_base[2].union(sent_aval_aux))

                if ind_jaccart > limiar:
                    inserir = False
                    sentenca_semelhante = sent_base
                    ind_jaccart_sentenca_descartada = ind_jaccart
                    break

            if inserir:
                sentencas_base.append((cod_arq, sent_aval, sent_aval_aux))
                sentencas_a_inserir.append(sent_inserir)
            else:
                sentencas_descartadas.append((sent_aval, sent_aval_aux, ind_jaccart_sentenca_descartada,
                                              sentenca_semelhante))

        total_sentencas = len(sentencas)
        qtd_sentencas_descartadas = len(sentencas_descartadas)
        total_global_sentencas += total_sentencas
        total_global_sentencas_descartadas += qtd_sentencas_descartadas

        print(f"(Sentenças descartadas/total: {qtd_sentencas_descartadas}/{total_sentencas} - "
              f"{(qtd_sentencas_descartadas / total_sentencas) * 100:.2f}%)-> OK")

        documentos_sentencas[cod_arq] = sentencas_a_inserir
        sentencas_descartadas_por_arquivo[cod_arq] = (sentencas_descartadas, total_sentencas)

        cont += 1

    total_sentencas_aproveitadas = total_global_sentencas - total_global_sentencas_descartadas

    if total_global_sentencas > 0:
        print(f"\n# Resultado: Das {total_global_sentencas} sentenças encontradas nos {qtd_documentos} documentos, "
              f"foram aproveitadas {total_sentencas_aproveitadas} "
              f"({(total_sentencas_aproveitadas / total_global_sentencas) * 100:.2f}%) e descartadas "
              f"{total_global_sentencas_descartadas} "
              f"({(total_global_sentencas_descartadas / total_global_sentencas) * 100:.2f}%)\n")

        # Gera um arquivo com o detalhamento das sentenças descartadas
        caminho_arq_detalhes_descarte = os.path.join(caminho_relatorio, "detalhamento_sentencas_descartadas.txt")

        with open(caminho_arq_detalhes_descarte, "w") as arq:
            for cod_arq, sent_descartadas in sentencas_descartadas_por_arquivo.items():
                qtd_sentencas_descartadas = len(sent_descartadas[0])
                qtd_total_sentencas = sent_descartadas[1]

                arq.write(f"# Documento: {cod_arq} - Qtd. sentenças descartadas/Qtd. sentenças: "
                          f"{qtd_sentencas_descartadas}/{qtd_total_sentencas} "
                          f"({(qtd_sentencas_descartadas / qtd_total_sentencas) * 100:.2f}%)\n\n")

                for sent_descartada in sent_descartadas[0]:
                    arq.write(f"   Sentença descartada...............: {sent_descartada[0]}\n")
                    arq.write(f"   Set sent. descartada..............: {sent_descartada[1]}\n")
                    arq.write(f"   Índice de Jaccart.................: {sent_descartada[2]}\n")
                    arq.write("   > Dados da sentença base semelhante\n")
                    arq.write(f"                - Nome do documento..: {sent_descartada[3][0]}\n")
                    arq.write(f"                - Sentença base......: {sent_descartada[3][1]}\n")
                    arq.write(f"                - Set sent. base.....: {sent_descartada[3][2]}\n\n")

                arq.write("\n\n")

    if escopo_global_sentencas:
        salvar_sentencas_base(caminho_sentencas_base, nome_arq_sents_base, sentencas_base)

    return documentos_sentencas


def construir_dataset(data_hora, codproc, caminho, caminho_sentencas_base, tamanho_minimo_sentenca, qtd_max_sent=5,
                      reprocessar=False, organizar_em_pastas=False, cabecalho=False,
                      retirar_sentencas_semelhantes=False, escopo_global_sentencas=True, limiar=0.90):
    """
    Constrói um dataset de acordo com o tipo de processamento e grava em arquivo(s)
        :param data_hora: Data e hora para compor o nome da pasta onde os datasets serão gerados
        :param codproc: Código do processamento a ser realizado (ner ou classificacao)
        :param caminho: Caminho onde o(s) arquivo(s) será(ão) gerados
        :param caminho_sentencas_base: Caminho para obtenção e/ou gravação das sentenças base
        :param tamanho_minimo_sentenca: Sentenças com tamanho menor que este parâmetro serão descartadas
        :param qtd_max_sent: Quantidade máxima de sentenças em cada arquivo. Sem efeito se o parâmetro
                             'organizar_em_pastas' for False
        :param reprocessar: Indica se deve fazer o reprocessamento dos documentos, caso já tenha sido construido um
                            dataset antes
        :param organizar_em_pastas: Indica se os editais serão organizados em pasta (uma pasta para cada edital)
        :param cabecalho: Se deve ou não inserir cabeçalho nos arquivos de dataset para classificação
        :param retirar_sentencas_semelhantes: Indica se as sentenças semelhantes devem ser retiradas no momento de
                                              geração dos datasets
        :param escopo_global_sentencas: Escopo para a análise de sentenças. Se True, fará a comparação com todos os
                                        documentos, caso contrário a comparação será somente no próprio documento
        :param limiar: Limiar para o descarte. Caso o Índice de Jaccart fique acima do limiar a sentença é descartada
        :return: Dicionário com os datasets construidos e caminho onde eles foram salvos
    """
    documentos_sentencas = {}  # A chave é o código do arquivo e o valor é uma lista de sentenças
    caminho_com_data = ""  # Guarda o caminho onde os datasets serão gerados

    c_mongo_meta = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_metadados')
    doc_metadados_js = obter_metadados_documentos(c_mongo_meta, codproc, reprocessar)

    if doc_metadados_js:
        print("\n                 #------- Processando documentos -------#\n")

        # Ajuda a organizar a pasta de datasets
        caminho_com_data = os.path.join(caminho, f"{codproc}_{data_hora}")

        documentos_subsecoes = obter_subsecoes_documentos(doc_metadados_js)
        tam_documentos_subsecoes = len(documentos_subsecoes)
        lst_documentos = list(documentos_subsecoes.keys())
        processado = False

        # Guardam esses dados para informar no arquivo de parâmetros utilizados
        filtro = ''
        nome_modelo = ''

        # Cria uma pasta para armazenar os datasets
        try:
            os.makedirs(caminho_com_data, exist_ok=True)
        except PermissionError:
            print(
                f"\nErro ao criar a pasta '{caminho_com_data}' para guardar os datasets. "
                f"Permissão de escrita negada!\n")
            exit(PERMISSION_ERROR)

        if codproc == 'ner':
            filtro = 'JUR'
            nome_modelo, documentos_subsecoes_classificadas = classificar_subsecoes(documentos_subsecoes,
                                                                                    filtro_retorno=filtro)
            del documentos_subsecoes
            documentos_sentencas = dividir_em_sentencas(documentos_subsecoes_classificadas, tamanho_minimo_sentenca)
            del documentos_subsecoes_classificadas

            if retirar_sentencas_semelhantes:
                documentos_sentencas = \
                    retirar_sentencas_similares(documentos_sentencas, caminho_sentencas_base, "SentencasBaseNER.pkl",
                                                caminho_com_data, reprocessar=reprocessar,
                                                escopo_global_sentencas=escopo_global_sentencas, limiar=limiar)
            arq_dataset = None

            print("\n=> Etapa: Gerando arquivos.\n")

            if organizar_em_pastas:
                # Trata a quantidade máxima de sentenças para evitar problemas
                if qtd_max_sent < 5:
                    qtd_max_sent = 5

                for cod_arq, sentencas in documentos_sentencas.items():
                    nome_pasta = cod_arq.split('.')[0]  # Retira a extensão do código do arquivo
                    nome_arquivo = '_'.join(nome_pasta.split('_')[1:])  # Retira a prefixo numérico único

                    if len(sentencas) == 0:
                        nome_pasta = "DOCUMENTO_SEM_SENTENÇAS_ÚNICAS_" + nome_pasta

                    # Cria uma pasta para cada documento (sem a extensão (ex: .pdf) do código do arquivo)
                    pasta_destino_dataset = os.path.join(caminho_com_data, nome_pasta)

                    try:
                        os.makedirs(pasta_destino_dataset, exist_ok=True)
                    except PermissionError:
                        print(
                            f"\nErro ao criar a pasta '{pasta_destino_dataset}' para guardar os datasets. "
                            f"Permissão de escrita negada!\n")
                        exit(PERMISSION_ERROR)

                    seq = 1  # Sequência numérica para compor os nomes dos datasets

                    for i in range(len(sentencas)):
                        # Gera um arquivo diferente a cada 'qtd_max_sent' sentenças
                        if (i % qtd_max_sent) == 0:
                            if arq_dataset:
                                arq_dataset.close()

                            caminho_destino_dataset = os.path.join(pasta_destino_dataset, f"{nome_arquivo}_{seq}.txt")

                            try:
                                arq_dataset = open(caminho_destino_dataset, 'w')
                            except PermissionError:
                                print(f"\nErro ao criar o arquivo de dataset na pasta '{pasta_destino_dataset}'. "
                                      f"Permissão de gravação negada!\n")
                                exit(PERMISSION_ERROR)

                            seq += 1

                        arq_dataset.write(f"{sentencas[i]}\n")
            else:
                # Não aplicável quando os documentos não forem organizados por pasta
                qtd_max_sent = 'n/a'

                for cod_arq, sentencas in documentos_sentencas.items():
                    nome_arquivo = cod_arq.split('.')[0] + '.txt'
                    caminho_destino_dataset = os.path.join(caminho_com_data, nome_arquivo)

                    try:
                        arq_dataset = open(caminho_destino_dataset, 'w')
                    except PermissionError:
                        print(f"\nErro ao criar o arquivo de dataset '{nome_arquivo}' na pasta '{caminho_com_data}'. "
                              f"Permissão de gravação negada!\n")
                        exit(PERMISSION_ERROR)

                    for i in range(len(sentencas)):
                        arq_dataset.write(f"{sentencas[i]}\n")

            if arq_dataset:
                arq_dataset.close()

            processado = True
        elif codproc == 'classificacao':
            arq_dataset = None

            # Não aplicável para classificação
            filtro = 'n/a'
            nome_modelo = 'n/a'

            cont = 1

            print("\n=> Etapa: Gerando datasets de classificação.\n")

            for cod_arq, subsecoes in documentos_subsecoes.items():
                print(f"   Documento ({cont}/{tam_documentos_subsecoes}): {cod_arq} ", end='', flush=True)

                caminho_destino_dataset = os.path.join(caminho_com_data, cod_arq.split('.')[0] + '.csv')

                try:
                    arq_dataset = open(caminho_destino_dataset, 'w')
                except PermissionError:
                    print(f"\nErro ao criar o arquivo de dataset na pasta '{caminho_com_data}'. "
                          f"Permissão de gravação negada!\n")
                    exit(PERMISSION_ERROR)

                if cabecalho:
                    arq_dataset.write("Subseção\tTipo\n")  # Adiciona um cabeçalho para facilitar a leitura do CSV

                for sub in subsecoes:
                    arq_dataset.write(f"{sub}\t' '\n")

                arq_dataset.close()
                print("-> OK")
                cont += 1

            processado = True
        elif codproc == 'classificacao_label':
            nome_modelo, documentos_subsecoes_classificadas = classificar_subsecoes(documentos_subsecoes)
            del documentos_subsecoes

            filtro = 'n/a'
            arq_dataset = None
            cont = 1

            print("\n=> Etapa: Gerando datasets de classificação com os possíveis labels.\n")

            for cod_arq, subsecoes in documentos_subsecoes_classificadas.items():
                print(f"   Documento ({cont}/{tam_documentos_subsecoes}): {cod_arq} ", end='', flush=True)

                caminho_destino_dataset = os.path.join(caminho_com_data, cod_arq.split('.')[0] + '.csv')

                try:
                    arq_dataset = open(caminho_destino_dataset, 'w')
                except PermissionError:
                    print(f"\nErro ao criar o arquivo de dataset na pasta '{caminho_com_data}'. "
                          f"Permissão de gravação negada!\n")
                    exit(PERMISSION_ERROR)

                if cabecalho:
                    arq_dataset.write("Subseção\tTipo\n")  # Adiciona um cabeçalho para facilitar a leitura do CSV

                for sub in subsecoes:
                    arq_dataset.write(f"{sub[0]}\t{sub[1]}\n")

                arq_dataset.close()
                print("-> OK")
                cont += 1

            processado = True

            print("\n ATENÇÃO: Os datasets foram gerados e cada seção recebeu um label, ENTRETANTO, estes labels "
                  "\n          precisam ser verificados, pois foram preditos por um modelo baseado em editais de \n"
                  "          informática e  portanto precisam de revisão ao utilizá-lo para classificar outros \n"
                  "          tipos de editais.\n")

        if processado:
            print(f"\n - Os datasets foram gerados na pasta '{caminho_com_data}'\n")

            # Gera um arquivo com os parâmetros de processamento que foram utilizados na geração dos datasets
            arq_parametros_utilizados = None
            nome_arq_parametros_utilizados = os.path.join(caminho_com_data, 'parametros_utilizados.txt')

            try:
                arq_parametros_utilizados = open(nome_arq_parametros_utilizados, 'w')
            except PermissionError:
                print(f"\nErro ao criar o arquivo com os parâmetros utilizados na construção dos datasets. "
                      f"Permissão de gravação negada na pasta '{caminho_com_data}'!\nProcessamento abortado.")
                exit(PERMISSION_ERROR)

            if codproc == 'classificacao' or codproc == 'classificacao_label':
                # reatribui alguns valores de parâmetros que não se aplicam à classificação para a geração do arquivo
                # de parâmetros utilizados
                tamanho_minimo_sentenca = 'n/a'
                qtd_max_sent = 'n/a'
                retirar_sentencas_semelhantes = 'n/a'
                escopo_global_sentencas = 'n/a'
                limiar = 'n/a'

            if not retirar_sentencas_semelhantes:
                escopo_global_sentencas = 'n/a'
                limiar = 'n/a'

            arq_parametros_utilizados.write(f"# Parâmetros utilizados para construção dos datasets:\n\n"
                                            f"Pasta destino: {caminho_com_data}\nCódigo de processamento: {codproc}\n"
                                            f"Tamanho mínimo de sentença: {tamanho_minimo_sentenca}\n"
                                            f"Quantidade de documentos: {tam_documentos_subsecoes}\nQuantidade máxima "
                                            f"de sentenças por arquivo: {qtd_max_sent}\nReprocessado: {reprocessar}\n"
                                            f"Organizar em pastas: {organizar_em_pastas}\n"
                                            f"Nome do modelo utilizado na classificação das sentenças: {nome_modelo}\n"
                                            f"Filtro: {filtro}\nRetirar sentenças semelhantes: "
                                            f"{retirar_sentencas_semelhantes}\nEscopo global de sentenças: "
                                            f"{escopo_global_sentencas}\nLimiar para definição de sentenças similares: "
                                            f"{limiar}\nDocumentos:\n{lst_documentos}")
            arq_parametros_utilizados.close()

            # Marca os documentos que foram processados
            doc_erros = marcar_documentos_processados(c_mongo_meta, doc_metadados_js, codproc, reprocessar)
            if doc_erros:
                print(f"ERRO: Os documentos a seguir foram processados mas não foram atualizados:\n{doc_erros}"
                      f"\nVerificar!")
    else:
        print("\nNão foi possível construir o(s) dataset(s). Nenhum documento atendeu ao filtro informado!")

    c_mongo_meta.fechar_conexao()

    return documentos_sentencas, caminho_com_data
