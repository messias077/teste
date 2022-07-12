# -----------------------------------------------------------------------------
# Interface interativa do sistema em modo texto
# Versão: 0.5.0
# -----------------------------------------------------------------------------

import os
from src.utils import suprimir_warning_tf
from src.utils.limpar_db import limpar_db_para_testes
from src.ambiente.parametros_globais import FILE_NOT_FOUND_ERROR, PERMISSION_ERROR, PREPROC_CAMINHO_ARQ_CONF
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from src.classes.persistencia.cliente import ClienteGenerico
from src.classes.persistencia.dump_arq import descarregar_conteudo
from src.classes.persistencia.serializacao import desserializar
from src.modulos.preproc.pre_processador import preparar_arquivo
from src.modulos.preproc.preproc import pre_processamento
from src.modulos.ren.conversor_jsonl_conll import converter_jsonl_conll
from src.modulos.ren.ren import ren
from src.utils.geradores import gerar_data, gerar_epoch


def imprimir_chaves(tipo_doc):
    """
    Imprime as chaves correspondentes à cada tipo de documento
        :param tipo_doc: Tipo do documento para imprimir as chaves correspondentes
    """
    print(
        """
        ----> Chaves para pesquisa <----

        Escolha uma chave, copie e cole no campo "Chave".
    """)

    tipo = tipo_doc.upper()

    if tipo == "EDITAL":
        print(
            """
            ## Edital:
                Edital__nome
                Edital__codigo_arq
                Edital__codigo_lote
                Edital__dumpconteudo
                Edital__secoes.Secao__numero
                Edital__secoes.Secao__titulo
                Edital__secoes.Secao__subsecoes.Subsecao__numero
                Edital__secoes.Secao__subsecoes.Subsecao__descricao
                """)
    elif tipo == "DOCUMENTO":
        print(
            """
            ## Documento:
                Documento__nome
                Documento__codigo_arq
                Documento__hash_md5
                Documento__tipo_arq
                Documento__extensao
                Documento__data_cadastro
                Documento__usuario_cadastrou
                Documento__cod_processamento
                Documento__codigo_lote
                Documento__nome_arq_original
                Documento__url_web
                Documento__caminho_base
                Documento__caminho_relativo
                Documento__head
                """)
    elif tipo == "LOTE":
        print(
            """
            ## Lote:
                Lote__codigo_lote
                Lote__tipo
                Lote__tempo_inicio
                Lote__tempo_fim
                Lote__documentos_ok
                Lote__documentos_erro
                """)
    elif tipo == "RESULTADO":
        print(
            """
            ## Resultado:
                Resultado__tipo
                Resultado__codigo_lote
                Resultado__data_resultado
                Resultado__status
                Resultado__nome_arq_original
                Resultado__tipo_arq
                Resultado__codigo_arq
                Resultado__url_web
                Resultado__usuario_cadastrou
                Resultado__data_cadastro
                Resultado__mensagens
            """
        )


def cadastrar_arquivos(tipo, usuario, caminho_entrada):
    """
        Faz o cadastro dos arquivos
            :param tipo: Tipo do arquivo (EDITAL, etc.)
            :param usuario: Usuário que está realizando o cadastro
            :param caminho_entrada: Caminho onde os documentos no formato PDF se encontram
    """
    caminho = None

    if tipo == 'EDITAL':
        caminho = os.path.join(caminho_entrada, 'editais')

    arquivos_cadastrar = []

    # Obtém a lista de todos os arquivos que serão cadastrados
    try:
        arquivos_cadastrar = os.listdir(caminho)
    except FileNotFoundError:
        print(f"\nO caminho '{caminho}' não existe!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao listar o caminho '{caminho}'. Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    arquivos_cadastrar.sort()

    if 'preproc.lock' not in arquivos_cadastrar:
        qtd_arquivos_cadastrados = 0
        print("\n=> Arquivos cadastrados:\n")

        for a in arquivos_cadastrar:
            if '.metadados' not in a and a + '.metadados' not in arquivos_cadastrar and a != 'erro':
                print(f"   {a}")
                qtd_arquivos_cadastrados += 1
                preparar_arquivo(caminho, a, "n/a", usuario, gerar_epoch())

        print(f"\nQuantidade de arquivos cadastrados: {qtd_arquivos_cadastrados}")
    else:
        print(f"\nERRO: A pasta '{caminho_entrada}' está bloqueada pela rotina de pre-processamento. Aguarde a rotina "
              f"terminar e tente novamente!")


def imprimir_documento(doc_obj, mensagem):
    """
    Imprime um documento
        :param doc_obj: Documento que será impresso
        :param mensagem: Mensagem referente ao documento que será impresso
    """
    print(mensagem)
    print(len(mensagem) * '-', end='')
    print('\n')

    if 'EDITAL' in mensagem:
        print(f' > Nome do documento.....: {doc_obj.nome}\n')
        print(f' > Código do arquivo.....: {doc_obj.codigo_arq}\n')
        print(f' > Código do lote........: {doc_obj.codigo_lote}\n')
        print(f' > Dump do conteúdo......:\n')
        for n, p in enumerate(doc_obj.dumpconteudo):
            print(f"  - Pag. {n+1}: {p}")

        for s in doc_obj.secoes:
            print(f'\n# Seção: {s.numero} - Pág(s) {s.paginas}: {s.titulo}')

            for sb in s.subsecoes:
                print(f'{sb.numero}: {sb.descricao}')
    elif 'DOCUMENTO' in mensagem:
        print(f"Nome do arquivo...........: {doc_obj.nome}")
        print(f"Código do arquivo.........: {doc_obj.codigo_arq}")
        print(f"Hash MD5..................: {doc_obj.hash_md5}")
        print(f"Tipo......................: {doc_obj.tipo_arq}")
        print(f"Extensao..................: {doc_obj.extensao}")
        print(f"Data Cadastro epoch.......: {doc_obj.data_cadastro}, tipo: {type(doc_obj.data_cadastro)}")
        print(f"Data Cadastro normal......: {gerar_data(doc_obj.data_cadastro, '%d/%m/%Y %H:%M:%Shs')}")
        print(f"Usuário que cadastrou.....: {doc_obj.usuario_cadastrou}")
        print(f"Código Processamento......: {doc_obj.cod_processamento}")
        print(f"Lote......................: {doc_obj.codigo_lote}")
        print(f"Nome do arquivo original..: {doc_obj.nome_arq_original}")
        print(f"URL WEB...................: {doc_obj.url_web}")
        print(f"Caminho Base..............: {doc_obj.caminho_base}")
        print(f"Caminho Relativo..........: {doc_obj.caminho_relativo}")
        print(f"Head......................: {len(doc_obj.head)} páginas")
        for p, h in enumerate(doc_obj.head):
            print(f"  - Pag. {p+1}: {h}")
    elif 'LOTE' in mensagem:
        print(f"codigo....................: {doc_obj.codigo_lote}")
        print(f"tipo......................: {doc_obj.tipo}")
        print(f"tempo_inicio..............: {doc_obj.tempo_inicio}")
        print(f"tempo_fim.................: {doc_obj.tempo_fim}")
        print(f"documentos_ok.............: {doc_obj.documentos_ok}")
        print(f"documentos_erro...........: {doc_obj.documentos_erro}")
        print(f"Estatísticas..............: {doc_obj.obter_estatisticas()}")
    elif 'RESULTADO' in mensagem:
        print(f"Tipo do resultado.........: {doc_obj.tipo}")
        print(f"Código do lote............: {doc_obj.codigo_lote}")
        print(f"Data epoch................: {doc_obj.data_resultado}, tipo: {type(doc_obj.data_resultado)}")
        print(f"Data normal...............: {gerar_data(doc_obj.data_resultado, '%d/%m/%Y %H:%M:%Shs')}")
        print(f"Status....................: {doc_obj.status}")
        print(f"Nome do arquivo original..: {doc_obj.nome_arq_original}")
        print(f"Tipo......................: {doc_obj.tipo_arq}")
        print(f"Código do arquivo.........: {doc_obj.codigo_arq}")
        print(f"URL WEB...................: {doc_obj.url_web}")
        print(f"Usuário que cadastrou.....: {doc_obj.usuario_cadastrou}")
        print(f"Data Cadastro normal......: {gerar_data(doc_obj.data_cadastro, '%d/%m/%Y %H:%M:%Shs')}")
        print(f"Mensagens.................: {len(doc_obj.mensagens)} mensagens")
        for n, m in enumerate(doc_obj.mensagens):
            print(f"  - Msg. {n+1}: {m}")


def listar_documentos_impressao(tipo, docs_json, caminho_dump):
    """
    Lista os documentos que poderão ser impressos
        :param tipo: Tipo do documento
        :param docs_json: Documento canditato à impressão
        :param caminho_dump: Caminho para geração do dump do edital, caso seja necessário
    """
    seq = 0
    tam = len(list(docs_json))
    ler_doc = True
    objeto_desserializado = None
    print(f"\n    ## Qtd de documentos retornados: {tam}")

    while seq < tam:
        if ler_doc:
            objeto_desserializado = desserializar(docs_json[seq])
            ler_doc = False  # Só voltará ser 'True' se a opção escolhida for válida
            seq += 1

        print(f"\n    >> Doc. {seq}/{tam}")

        if tipo == 'EDITAL' or tipo == 'DOCUMENTO':
            print(f"        -> Nome do documento: {objeto_desserializado.codigo_arq}")
        elif tipo == 'LOTE':
            print(f"        -> Código do lote: {objeto_desserializado.codigo}")
        elif tipo == 'RESULTADO':
            print(f"        -> Tipo do resultado: {objeto_desserializado.tipo}")

        r = input("   \n           Deseja imprimir (S=Sim / N=Não / V=Navegar / X=Sair)?: ").upper()

        if r == 'S':
            if tipo == 'EDITAL':
                ri = input("   \n           Imprimir onde (T=Tela / A=Arquivo)?: ").upper()

                if ri == 'T':
                    imprimir_documento(objeto_desserializado, f"\n\n ** Dados extraídos - {tipo} **")
                    ler_doc = True
                elif ri == 'A':
                    tipo_dump = ""

                    print(
                        """
                        > Tipos de dump:\n
                          EDITAL - Edital completo com as seções separadas
                          SECOES - Somenteas seções do edital
                          CONTEUDO - Edital completo sem as seções separadas
                          TODOS - Faz o dump de todos os tipos
                        """
                    )

                    while tipo_dump not in ['EDITAL', 'SECOES', 'CONTEUDO', 'TODOS', 'X']:
                        tipo_dump = input("           Escolha um tipo (X=Sair): ").upper()

                    if tipo_dump != 'X':
                        if tipo_dump != 'TODOS':
                            lst_tipo_dump = [tipo_dump]
                        else:
                            lst_tipo_dump = ['EDITAL', 'SECOES', 'CONTEUDO']

                        for t in lst_tipo_dump:
                            nome_arquivo = os.path.join(caminho_dump, objeto_desserializado.codigo_arq.split('.')[0] +
                                                        '_' + t + '.txt')

                            descarregar_conteudo(objeto_desserializado, t, nome_arquivo)
                            print(f"\n           Salvo como '{nome_arquivo}'")

                        ler_doc = True
                else:
                    print("\n           Opção inválida!")
            else:
                imprimir_documento(objeto_desserializado, f"\n\n ** Dados extraídos - {tipo} **")
                ler_doc = True
        elif r == 'N':
            ler_doc = True
        elif r == 'V':
            while True:
                ri = input(f"\n        - Digite o no. do documento (1-{tam} / 0=Voltar): ")

                try:
                    n = int(ri)
                except ValueError:
                    print("\n          Digite um número!")
                    continue

                if 1 <= n <= tam:
                    seq = n - 1
                    ler_doc = True
                    break
                elif n == 0:
                    break
                else:
                    print(f"\n          O número digitado está fora da faixa (1 a {tam})!")
        elif r == 'X':
            break
        else:
            print("\n       Opção incorreta!")

    if tam > 0 and (seq == tam):
        print("\n       *** Fim da lista! ***")


def ler_dados_bd(tipo, opcao, chave, valor, caminho_dump):
    """
    Ler os documentos no banco de dados
        :param tipo: Tipo do documento
        :param opcao: Opção de base de dados capturada do menu principal
        :param chave: Chave para a busca do documento
        :param valor: Valor da chave para busca do documento
        :param caminho_dump: Caminho para geração do dump do edital, caso seja necessário
    """
    docs_json = None

    if tipo == 'EDITAL':
        banco_mongo = 'db_documentos'
        colecao_mongo = 'col_editais'

        if opcao == '2':
            c_mongo = ClienteGenerico('MongoDB', 'localhost', 27017, banco_mongo)
            doc_mongo_js = c_mongo.buscar_todos(colecao_mongo, chave, valor)
            c_mongo.fechar_conexao()
            docs_json = list(doc_mongo_js)
    elif tipo == 'DOCUMENTO':
        c_mongo_meta = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_metadados')
        doc_metadados_js = c_mongo_meta.buscar_todos('col_metadados_docs', chave, valor)
        c_mongo_meta.fechar_conexao()
        docs_json = list(doc_metadados_js)
    elif tipo == 'LOTE':
        c_mongo_lote = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_metadados')
        doc_lotes_js = c_mongo_lote.buscar_todos('col_metadados_lotes', chave, valor)
        c_mongo_lote.fechar_conexao()
        docs_json = list(doc_lotes_js)
    elif tipo == 'RESULTADO':
        c_mongo_resultado = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_metadados')
        doc_resultados_js = c_mongo_resultado.buscar_todos('col_metadados_resultados', chave, valor)
        c_mongo_resultado.fechar_conexao()
        docs_json = list(doc_resultados_js)
    else:
        print(f"\nO tipo de documento '{tipo}' não está cadastrado!")
        return

    listar_documentos_impressao(tipo, docs_json, caminho_dump)


def menu():
    """
    Menu principal do sistema
    """
    # Obtém o caminho do arquivo de configuração para montar o caminho completo
    caminho_arquivo_configuracao = PREPROC_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao = 'param_preproc.conf'
    arq_conf = os.path.join(caminho_arquivo_configuracao, nome_arquivo_configuracao)

    conf = inicializar_parametros('preproc', arq_conf)

    # Obtém alguns parâmetros de configuração do módulo
    parametros = {'caminho_arq_conf': arq_conf,
                  'p_caminho_entrada': conf.obter_valor_parametro('p_caminho_entrada'),
                  'p_caminho_dumps': conf.obter_valor_parametro('p_caminho_dumps')}

    validar_pastas(parametros)

    while True:
        print('\n***************( INTERFACE DO PROTÓTIPO - MODO TEXTO )**************\n')
        print('                      >> MENU <<\n')
        print('             1 - Cadastrar Editais')
        print('             2 - Consultar Editais')
        print('             3 - Excluir Editais (para fins de testes)')
        print('             4 - Pré-Processar')
        print('             5 - Construir Dataset')
        print('             6 - Converter JSONL para CONLL')
        print('\n********************************************************************')
        op = input("Escolha a opção (Sair => 0): ")

        if op == '1':
            cadastrar_arquivos('EDITAL', 'SISTEMA', parametros['p_caminho_entrada'])
        elif op == '2':
            print("\nInforme os parâmetros abaixo:\n")
            tipo_doc = input("  --Tipo (EDITAL, DOCUMENTO, LOTE ou RESULTADO)...: ").upper()

            while tipo_doc not in ["EDITAL", "DOCUMENTO", "LOTE", "RESULTADO", "X"]:
                print(f"\n     O tipo de documento '{tipo_doc}' não existe!\n")
                tipo_doc = input("  --Tipo (EDITAL, DOCUMENTO, LOTE ou RESULTADO) |  X=Sair...: ").upper()

            if tipo_doc != 'X':
                chave_doc = '*'

                while chave_doc == '*':
                    chave_doc = input('  --Chave (* = Listas as opções)..................: ')

                    if chave_doc == '*':
                        imprimir_chaves(tipo_doc)
                    else:
                        break

                while True:
                    print(f"\n  ***  Pesquisando no 'MongoDB' pela chave: '{chave_doc}'  ***\n")

                    valor_chave = input('    --Valor (X=Sair)..: ')

                    if valor_chave.upper() == 'X':
                        break

                    ler_dados_bd(tipo_doc.upper(), op, chave_doc, valor_chave, parametros['p_caminho_dumps'])
        elif op == '3':
            limpar_db_para_testes(interativo=True)
        elif op == '4':
            pre_processamento()
        elif op == '5':
            gerar_estatisticas = False
            gerar_estatisticas_str = 'n'
            organizar_em_pastas = True
            organizar_em_pastas_str = 'n'
            qtd_sents = 0
            reprocessar = False
            retirar_sentencas_similares = False
            retirar_sentencas_similares_str = 'n'
            escopo_global_sentencas = True
            escopo_global_sentencas_str = 's'

            codproc = input("\nDigite o código de processamento (ner, classificacao ou classificacao_label): ")

            if codproc == 'ner':
                qtd_sents = int(input("Digite a quantidade de sentenças por arquivo: "))
                gerar_estatisticas_str = input("Gerar estatísticas dos documentos? (S/N): ")
                organizar_em_pastas_str = input("Organizar os documentos em pastas separadas? (S/N): ")
                retirar_sentencas_similares_str = input("Deseja retirar as sentenças similares na geração dos "
                                                        "datasets? (S/N): ")
                if retirar_sentencas_similares_str.lower() == 's':
                    escopo_global_sentencas_str = input("Considerar o escopo global dos documentos para retirada das "
                                                        "sentenças? (S/N): ")

            reprocessar_str = input("Reprocessar? (S/N): ")

            resp_stat = gerar_estatisticas_str.lower()
            resp_organizar = organizar_em_pastas_str.lower()
            resp_reproc = reprocessar_str.lower()
            resp_retirar_sentencas_similares = retirar_sentencas_similares_str.lower()
            resp_escopo_global_sentencas = escopo_global_sentencas_str.lower()

            if resp_stat == 's':
                gerar_estatisticas = True
            elif resp_stat == 'n':
                gerar_estatisticas = False
            else:
                print("\nParâmetro 'Gerar estatísticas' incorreto. Escolha (S ou N).")

            if resp_organizar == 's':
                organizar_em_pastas = True
            elif resp_organizar == 'n':
                organizar_em_pastas = False
            else:
                print("\nParâmetro 'organizar_em_pastas' incorreto. Escolha (S ou N).")

            if resp_retirar_sentencas_similares == 's':
                retirar_sentencas_similares = True
            elif resp_retirar_sentencas_similares == 'n':
                retirar_sentencas_similares = False
            else:
                print("\nParâmetro 'Retirar sentenças semelhantes' incorreto. Escolha (S ou N).")

            if resp_escopo_global_sentencas == 's':
                escopo_global_sentencas = True
            elif resp_escopo_global_sentencas == 'n':
                escopo_global_sentencas = False
            else:
                print("\nParâmetro 'Escopo global das sentenças' incorreto. Escolha (S ou N).")

            if resp_reproc == 's':
                reprocessar = True
            elif resp_reproc == 'n':
                reprocessar = False
            else:
                print("\nParâmetro 'Reprocessar' incorreto. Escolha (S ou N).")

            if (resp_reproc == 's' or resp_reproc == 'n') and (resp_stat == 's' or resp_stat == 'n') and \
                    (resp_organizar == 's' or resp_organizar == 'n') and \
                    (resp_retirar_sentencas_similares == 's' or resp_retirar_sentencas_similares == 'n') and \
                    (resp_escopo_global_sentencas == 's' or resp_escopo_global_sentencas == 'n'):
                ren(codproc, qtd_sents, reprocessar, gerar_estatisticas, organizar_em_pastas,
                    retirar_sentencas_similares, escopo_global_sentencas)
        elif op == '6':
            retirar_sentencas_similares_str = input("\nDeseja retirar as sentenças similares na geração dos arquivos "
                                                    "CONLL? (S/N): ")
            resp_retirar_sentencas_similares = retirar_sentencas_similares_str.lower()

            if resp_retirar_sentencas_similares == 's':
                retirar_sentencas_similares = True
            elif resp_retirar_sentencas_similares == 'n':
                retirar_sentencas_similares = False
            else:
                print("\nParâmetro 'Retirar sentenças semelhantes' incorreto. Escolha (S ou N).")
                continue

            dividir_dataset_str = input("Deseja dividir o dataset em treino, teste e validação? (S/N): ")
            resp_dividir_dataset_str = dividir_dataset_str.lower()

            if resp_dividir_dataset_str == 's':
                try:
                    tamanho_dataset_teste = float(input("Digite o tamanho do dataset de teste (tem que ser um número "
                                                        "decimal maior que 0.0 e menor que 1.0): "))
                except ValueError:
                    print("\nValor incorreto. Digite um número decimal!")
                    continue

                if tamanho_dataset_teste <= 0.0 or tamanho_dataset_teste >= 1.0:
                    print("\nValor incorreto. Digite um número decimal maior que 0.0 e menor que 1.0!")
                    continue
            elif resp_dividir_dataset_str == 'n':
                tamanho_dataset_teste = 0.0
            else:
                print("\nParâmetro 'Dividir dataset' incorreto. Escolha (S ou N).")
                continue

            if resp_retirar_sentencas_similares == 's' or resp_retirar_sentencas_similares == 'n':
                converter_jsonl_conll(retirar_sentencas_semelhantes=retirar_sentencas_similares,
                                      escopo_global_sentencas=True, tamanho_dataset_teste=tamanho_dataset_teste,
                                      concatenar_arquivos=True)
        elif op.upper() == '0':
            break


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    menu()
