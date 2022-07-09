# ----------------------------------------------------------------
# Funções para leitura de documentos no formato PDF
# ----------------------------------------------------------------

import re
import PyPDF2
from PyPDF2.utils import PdfReadError
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from pdfminer.pdfparser import PDFSyntaxError
from zlib import error
from src.ambiente.parametros_globais import PERCENTUAL_PERMITIDO_PAGINAS_EM_BRANCO, \
    PERCENTUAL_PERMITIDO_PAGINAS_QTD_MINIMA_TERMOS, PERCENTUAL_PERMITIDO_PAGINAS_TERMOS_ESTRANHOS, \
    PERCENTUAL_PERMITIDO_TERMOS_ESTRANHOS, QUANTIDADE_MINIMA_TERMOS_POR_PAGINA, TAMANHO_MAXIMO_PALAVRA, \
    QUANTIDADE_MAXIMA_NAO_ALFANUM


def filtrar_documento(doc, filtro):
    """
    Filtra o conteúdo de um documento e retira caracteres sozinhos e/ou palavras especificados no filtro
        :param doc: Dicionário com o documento que será filtrado
        :param filtro: Filtro que será aplicado no documento
    """
    for pag in doc.keys():
        conteudo_lst = doc[pag].split()
        conteudo_filtrado = [c for c in conteudo_lst if c not in filtro]
        doc[pag] = ' '.join(conteudo_filtrado)


def remover_caracteres_estranhos(doc):
    """
    Remove caracteres estranhos de um documento, com base numa lista de caracteres que devem ser mantidos
        :param doc: Dicionário com o documento que será analisado
    """
    caracteres_manter = 'ªº°§áÁãÃâÂàÀéÉêÊíÍóÓõÕôÔúÚçÇ0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!' \
                        '"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~ \n\r\x0b\x0c'

    for pag in doc.keys():
        conteudo_limpo = ''.join([str(c) for c in doc[pag] if c in caracteres_manter])
        doc[pag] = conteudo_limpo


def validar_conteudo(doc):
    """
    Valida o conteúdo de um documento
        :param doc: Dicionário com o documento que será validado
        :return: True ou False, relatório da validação
    """
    qtd_paginas = 0

    if doc:
        qtd_paginas = len(doc)

    # Trata quantidade de páginas zerada para evitar erro de divisão por zero
    if qtd_paginas == 0:
        return False, {"# Erro = ": "Não foi possível extrair o texto do documento!"}

    validado = True
    vogais = re.compile(r'[aáãâàéeiíoóõúu]')
    nao_alfanum = re.compile(r'[\W]')

    # Contadores para validação
    paginas_em_branco = 0
    paginas_menor_qtd_minima_termos = 0
    paginas_termos_estranhos = 0

    for pagina in doc.values():
        if pagina != '':
            termos_estranhos = 0

            # Para facilitar a busca por caracteres especiais:
            # - Limpa pontos em sumários (substitui por ' '), pois não estava validando.
            #   Exs.: Introdução...........5; Conlusão......40.
            #
            #   *** NOTA ***: Essa limpeza é apena para validação. A página lida do PDF não sofrerá alterações
            #
            #   >> Efeitos colaterais:
            #         * Limpa pontos no final das palavras, entretanto não prejudica a validação
            #         * Limpa pontos em números. Exs.: 1.0; 2.2.2; também não prejudica a validação
            termos = pagina.replace('.', ' ').split()

            qtd_termos = len(termos)

            # Uma página com poucos termos, em se tratando de editais, pode ser considerada
            # uma página em branco!
            if qtd_termos < QUANTIDADE_MINIMA_TERMOS_POR_PAGINA:
                paginas_menor_qtd_minima_termos += 1

            for t in termos:
                t_minusculo = t.lower()

                # Regras para definir se um termo é estranho
                if len(t) > TAMANHO_MAXIMO_PALAVRA:
                    # Maior palavra em português: pneumoultramicroscopicossilicovulcanoconiótico (46 letras)
                    # Fonte: https://www.bbc.com/portuguese/curiosidades-43938059
                    # É um bom parâmetro! :)
                    termos_estranhos += 1

                elif len(vogais.findall(t_minusculo)) == 0:
                    # Busca por vogais nas palavras.
                    # Numa página com vários termos, se este termo for uma palavra,
                    # ela tem que ter pelo menos uma vogal (Obs.: linguas portuguesa e inglesa)

                    # Se não tem vogal, considera a possibilidade de ser uma sigla ou número. Exs.: SMTP, 99, D2 ou
                    # caracteres especiais, tais como $, @, %, &, etc., que podem estar sendo utilizados no texto
                    if len(nao_alfanum.findall(t_minusculo)) > QUANTIDADE_MAXIMA_NAO_ALFANUM:
                        termos_estranhos += 1

            if termos_estranhos > qtd_termos * PERCENTUAL_PERMITIDO_TERMOS_ESTRANHOS:
                paginas_termos_estranhos += 1

        else:
            paginas_em_branco += 1
            paginas_menor_qtd_minima_termos += 1

    # verifica se não ultrapassou os limites percentuais

    # Para deixar o if menos confuso...
    p1 = paginas_em_branco > qtd_paginas * PERCENTUAL_PERMITIDO_PAGINAS_EM_BRANCO
    p2 = paginas_menor_qtd_minima_termos > qtd_paginas * PERCENTUAL_PERMITIDO_PAGINAS_QTD_MINIMA_TERMOS
    p3 = paginas_termos_estranhos > qtd_paginas * PERCENTUAL_PERMITIDO_PAGINAS_TERMOS_ESTRANHOS

    if p1 or p2 or p3:
        validado = False

    # Apura os resultados e gera a mensagem de status
    r1 = f"{str(paginas_em_branco / qtd_paginas * 100)}%"
    r1 += " - PASSOU" if not p1 else f" - FALHOU => Ultrapassou o máximo permitido " \
                                     f"({PERCENTUAL_PERMITIDO_PAGINAS_EM_BRANCO * 100}%)"

    r2 = f"{str(paginas_menor_qtd_minima_termos / qtd_paginas * 100)}%"
    r2 += " - PASSOU" if not p2 else f" - FALHOU => Ultrapassou o máximo permitido " \
                                     f"({PERCENTUAL_PERMITIDO_PAGINAS_QTD_MINIMA_TERMOS * 100}%)"

    r3 = f"{str(paginas_termos_estranhos / qtd_paginas * 100)}%"
    r3 += " - PASSOU" if not p3 else f" - FALHOU => Ultrapassou o máximo permitido " \
                                     f"({PERCENTUAL_PERMITIDO_PAGINAS_TERMOS_ESTRANHOS * 100}%)"
    
    # Cria um relatório da validação
    relatorio = {"# Qtd total de páginas = ": qtd_paginas,
                 "  - Páginas em branco = ": paginas_em_branco,
                 "  - Percentual de Páginas em branco = ": r1,
                 f"  - Páginas com menos de {QUANTIDADE_MINIMA_TERMOS_POR_PAGINA} termos = ":
                     paginas_menor_qtd_minima_termos,
                 f"  - Percentual de Páginas com menos de {QUANTIDADE_MINIMA_TERMOS_POR_PAGINA} termos = ": r2,
                 "  - Páginas com termos estranhos = ": paginas_termos_estranhos,
                 "  - Percentual de Páginas com termos estranhos = ": r3,
                 }

    return validado, relatorio


def ler_pypdf2(arq_pdf, caminho_arquivo):
    """
    Lê um arquivo no formato PDF com o PyPDF2
        :param arq_pdf: Arquivo PDF aberto
        :param caminho_arquivo: Caminho relativo ou caminho absoluto do arquivo
        :return: Dicionário contendo como chave a página do arquivo e como valor o conteúdo da página e se extraiu tudo
    """
    numero_paginas = 0
    pdf_lido = None
    extraiu_tudo = True
    documento = {}
    corrompido = False  # Improvisando..., o tratamento de exceção do pdfminer não funcionou para arquivo corrompido

    try:
        pdf_lido = PyPDF2.PdfFileReader(arq_pdf, strict=False)
        numero_paginas = pdf_lido.getNumPages()
    except PdfReadError:
        print(f"\n  *> Erro ao ler o arquivo PDF. O arquivo '{caminho_arquivo}' está corrompido ou mal formado!",
              end='')
        extraiu_tudo = False
        corrompido = True
    except ValueError:
        print(f"\n  *> Erro ao ler o arquivo PDF. O arquivo '{caminho_arquivo}' contém valores inválidos!", end='')
        extraiu_tudo = False

    # Obtêm as páginas do documento PDF lido e as formata
    for i in range(numero_paginas):
        pagina = pdf_lido.getPage(i)

        try:
            conteudo_pagina = pagina.extractText()
        except (error, KeyError):
            print(f"\n  *> Erro ao extrair a página {i + 1} do arquivo '{caminho_arquivo}'!", end='')
            extraiu_tudo = False
            continue

        # Transforma a página numa string e retira as tabulações e quebras de linhas
        pag_string = ''.join(conteudo_pagina)
        pag_string_formatada = re.sub('\t', ' ', pag_string)
        pag_string_formatada = re.sub('\n', '', pag_string_formatada)

        # Adiciona o número da página como chave e o conteúdo como valor
        documento[i + 1] = pag_string_formatada

    return documento, extraiu_tudo, corrompido


def ler_pdfminer(arq_pdf, caminho_arquivo):
    """
    Lê um arquivo no formato PDF com o pdfminer
        :param arq_pdf: Arquivo PDF aberto
        :param caminho_arquivo: Caminho relativo ou caminho absoluto do arquivo
        :return: Dicionário contendo como chave a página do arquivo e como valor o conteúdo da página e se extraiu tudo
    """
    pdf_lido = None
    extraiu_tudo = True
    documento = {}

    try:
        pdf_lido = extract_pages(arq_pdf)
    except PDFSyntaxError:
        print(f"\n  *> Erro ao ler o arquivo PDF. O arquivo '{caminho_arquivo}' está corrompido ou mal formado!",
              end='')
        extraiu_tudo = False
    except ValueError:
        print(f"\n  *> Erro ao ler o arquivo PDF. O arquivo '{caminho_arquivo}' contém valores inválidos!", end='')
        extraiu_tudo = False

    # Obtêm as páginas do documento PDF lido e as formata
    if pdf_lido:
        num_pagina = 1

        try:
            for layout_pagina in pdf_lido:
                texto_pagina = ""

                for elemento in layout_pagina:
                    if isinstance(elemento, LTTextContainer):
                        texto_pagina += elemento.get_text()

                # Transforma a página numa string e retira as tabulações e quebras de linhas
                pag_string = ''.join(texto_pagina)
                pag_string_formatada = re.sub('\t', ' ', pag_string)
                pag_string_formatada = re.sub('\n', ' ', pag_string_formatada)

                # Adiciona o número da página como chave e o conteúdo como valor
                documento[num_pagina] = pag_string_formatada
                num_pagina += 1
        except TypeError:
            print(f"\n  *> Erro ao ler o arquivo PDF. Não foi possível extrair as páginas do arquivo "
                  f"'{caminho_arquivo}'.", end='')
            extraiu_tudo = False

    return documento, extraiu_tudo


def ler_pdf(caminho_arquivo):
    """
    Lê um arquivo no formato PDF
        :param caminho_arquivo: Caminho relativo ou caminho absoluto do arquivo
        :return: Dicionário contendo como chave a página do arquivo e como valor o conteúdo da página;
        se extraiu tudo e validou o documento; relatório da validação
    """
    arq_pdf = None
    relatorio = None
    documento = {}
    extraiu_tudo = True
    validado = False

    # Filtro utilizado para filtrar o conteúdo de um documento e retirar caracteres sozinhos e/ou palavras
    filtro = ['-', '_']

    try:
        arq_pdf = open(caminho_arquivo, 'rb')
    except FileNotFoundError:
        print(f"\n  *> Erro ao abrir o arquivo. O arquivo '{caminho_arquivo}' não foi encontrado!", end='')
    except PermissionError:
        print(f"\n  *> Erro ao abrir o arquivo. Permissão de leitura negada!", end='')
    except IsADirectoryError:
        print(f"\n  *> Erro ao abrir o arquivo. '{caminho_arquivo}' é um diretório!", end='')

    if arq_pdf:
        documento, extraiu_tudo, corrompido = ler_pypdf2(arq_pdf, caminho_arquivo)

        if extraiu_tudo:
            filtrar_documento(documento, filtro)
            remover_caracteres_estranhos(documento)
            validado, relatorio = validar_conteudo(documento)

        # Caso não tenha extraido o PDF ou não validado, tenta com outro leitor. Obs.: Fiz dessa forma pois o PyPDF2 é
        # mais rápido que o pdfminer, entretando não consegue ler alguns PDFs que o pdfminer consegue!
        # Veja: https://stackoverflow.com/questions/26494211/extracting-text-from-a-pdf-file-using-pdfminer-in-python
        if (not extraiu_tudo or not validado) and not corrompido:
            print("\n                 Não conseguiu extrair com o PyPDF2! Tentando extrair com o pdfminer...", end='')
            documento, extraiu_tudo = ler_pdfminer(arq_pdf, caminho_arquivo)

            if extraiu_tudo:
                filtrar_documento(documento, filtro)
                remover_caracteres_estranhos(documento)
                validado, relatorio = validar_conteudo(documento)
            else:
                relatorio = {"# Erro = ": "Não foi possível extrair completamente o texto do documento!"}

        arq_pdf.close()

    return documento, extraiu_tudo and validado, relatorio
