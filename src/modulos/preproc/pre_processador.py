# ----------------------------------------------------------------
# Funções para processamento dos arquivos e persistência
# ----------------------------------------------------------------
import time
import src.utils.pdf as pdf
import src.modulos.preproc.extrator as ext
import src.utils.geradores as ger
import src.classes.persistencia.serializacao as ser
import os
import shutil
from src.classes.documentos import Edital
from src.classes.metadados import Lote, Resultado
from src.classes.persistencia.cliente import ClienteGenerico
from src.classes.persistencia.dump_arq import descarregar_conteudo
from src.ambiente.parametros_globais import FILE_NOT_FOUND_ERROR, PERMISSION_ERROR, CREATE_METADATA_ERROR, TIMEOUT_ERROR


def preparar_arquivo(caminho_entrada, nome, url_web, usuario, data_cadastro):
    """
    Prepara o arquivo para ser pré-processado pelo sistema
        :param caminho_entrada: Caminho onde o arquivo foi salvo
        :param nome: Nome do arquivo
        :param url_web: URL de onde o arquivo foi baixado
        :param usuario: Usuário que enviou ou baixou o arquivo para o sistema
        :param data_cadastro: Data do cadastro do arquivo no sistema
    """
    arq_metadado_aux = None  # Guardará o nome do arquivo de metadados

    caminho_nome_velho = os.path.join(caminho_entrada, nome)

    # Retira (), [] e {}, etc. para evitar erro nas pesquisas nas bases de dados
    nome_limpo = nome.replace('(', '')

    for carac in ")[]{},":
        nome_limpo = nome_limpo.replace(carac, '')

    # Gera um novo nome (baseado no código do arquivo) para renomear o arquivo e evitar sobrescrição de arquivos
    nome_novo = ger.gerar_codigo_arquivo(nome_limpo)
    caminho_nome_novo = os.path.join(caminho_entrada, nome_novo)

    try:
        os.rename(caminho_nome_velho, caminho_nome_novo)
    except FileNotFoundError:
        print(f"\nErro ao renomear o arquivo '{caminho_nome_velho}'. O arquivo não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao renomear o arquivo '{caminho_nome_velho}'. Permissão negada!\n")
        exit(PERMISSION_ERROR)

    # Gera um arquivo com alguns dados para geração dos metadados posteriormente
    try:
        arq_metadado_aux = open(caminho_nome_novo + '.metadados', 'w')
    except PermissionError:
        print(f"\nErro ao criar o arquivo auxiliar de metadados. Permissão de gravação negada!\n")
        exit(PERMISSION_ERROR)

    arq_metadado_aux.write(f"nome_arq_original = {nome}\n"
                           f"codigo_arq = {nome_novo}\n"
                           f"url_web = {url_web}\n"
                           f"usuario_cadastrou = {usuario}\n"
                           f"data_cadastro = {data_cadastro}\n")

    arq_metadado_aux.close()


def ler_arquivo(caminho, nome, codigo_arq, codigo_lote, tipo):
    """
    Lê um arquivo e processa seu conteúdo. Obs.: Se for um edital separa em seções.
        :param caminho: Caminho do arquivo
        :param nome: Nome do arquivo
        :param codigo_arq: Código do arquivo
        :param codigo_lote: Código do lote onde o arquivo está sendo processado
        :param tipo: Tipo do documento que será lido ('EDITAL', etc.)
        :return: Objeto contendo os dados do arquivo separados por seções e um dump do seu conteúdo; 
        se o documento foi extraido e validado; resultado da validação
    """
    documento_lido = None
    doc, validado, relatorio = pdf.ler_pdf(caminho)

    if doc:
        dump_conteudo = list(doc.values())  # Faz um dump do conteúdo do edital sem separação por seções

        if tipo == 'EDITAL':
            # Extrai as seções e subseções do edital
            termos_no_doc = ext.separar_em_termos(doc)
            sec_cand = ext.encontrar_secoes_candidatas(termos_no_doc)
            sec_extraidas = ext.extrair_secoes(sec_cand)
            ext.preencher_descricao(sec_extraidas, termos_no_doc)
            secoes_agrupadas = ext.agrupar_secoes(sec_extraidas)

            # Cria o objeto com os dados do documento lido
            documento_lido = Edital(nome, codigo_arq, codigo_lote, secoes_agrupadas, dump_conteudo)

    return documento_lido, validado, relatorio


def obter_metadados_aux(caminho_metadados_aux):
    """
    Obtém os metadados auxiliares do arquivo lido para realizar o pré-processamento
        :param caminho_metadados_aux: Caminho do arquivo auxiliar de metadados
        :return: Dicionário contendo os metadados do arquivo lido
    """
    arq_metadados_aux = None  # Guardará o arquivo de metadados aberto

    try:
        arq_metadados_aux = open(caminho_metadados_aux, 'r')
    except FileNotFoundError:
        print(f"\nErro ao abrir o aquivo auxiliar de metadados '{caminho_metadados_aux}'. "
              f"O arquivo não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao abrir o aquivo auxiliar de metadados '{caminho_metadados_aux}'. "
              f"Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    # Cria um dicionário com os metadados do arquivo
    linhas = arq_metadados_aux.readlines()
    arq_metadados_aux.close()

    metadados = {}

    for linha in linhas:
        l_split = linha.rstrip('\n').split('=')

        # Obtém o nome e o valor do metadado
        if len(l_split) == 2:
            metadados[l_split[0].strip()] = l_split[1].strip()

    return metadados


def mover_arq_ok(caminho_base, caminho_relativo, codigo_lote, nome_arq, caminho_arq, caminho_arq_metadados):
    """
    Move um arquivo pré-processado com êxito e seu respectivo metadado para a pasta de arquivos pré-processados
        :param caminho_base: Caminho base da pasta para onde os arquivos serão transferidos após o pré-processamento
        :param caminho_relativo: Caminho relativo da pasta para onde os arquivos serão transferidos após o
                                 pré-processamento
        :param codigo_lote: Código do lote onde o arquivo está sendo pré-processado
        :param nome_arq: Nome do arquivo que será movido
        :param caminho_arq: Caminho do arquivo que será movido
        :param caminho_arq_metadados: Caminho do metadado do arquivo que será movido
    """
    # Caminho da pasta do lote para onde o arquivo pré-processado será movido
    caminho_destino_lote = os.path.join(caminho_base, caminho_relativo, codigo_lote)

    try:
        os.makedirs(caminho_destino_lote, exist_ok=True)
    except PermissionError:
        print(f"\nErro ao criar a pasta de lote '{caminho_destino_lote}'. "
              f"Permissão de escrita negada!\n")
        exit(PERMISSION_ERROR)

    # Caminho para onde o arquivo pré-processado será movido
    caminho_destino = os.path.join(caminho_destino_lote, nome_arq)

    try:
        shutil.move(caminho_arq, caminho_destino)
    except PermissionError:
        print(f"\nErro ao mover o arquivo '{caminho_arq}'. Permissão negada!\n")
        exit(PERMISSION_ERROR)
    except FileNotFoundError:
        print(f"\nErro ao mover o arquivo '{caminho_arq}'. O arquivo não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)

    try:
        os.remove(caminho_arq_metadados)
    except PermissionError:
        print(f"\nErro ao apagar o arquivo de metadados '{caminho_arq_metadados}'. "
              f"Permissão negada!\n")
        exit(PERMISSION_ERROR)


def mover_arq_erro(codigo_lote, caminho_entrada, caminho_erro, nome_arq, caminho_arq,  nome_arq_metadados,
                   caminho_arq_metadados, msg=''):
    """
    Move um arquivo com erro no pré-processamento e seu respectivo metadado para a pasta de arquivos com erro
        :param codigo_lote: Código do lote no qual o arquivo está sendo pré-processado
        :param caminho_entrada: Caminho de entrada onde o arquivos está sendo pré-processado
        :param caminho_erro: Caminho para onde o arquivo com erro no pré-processamento será movido
        :param nome_arq: Nome do arquivo com erro que será movido
        :param caminho_arq: Caminho do arquivo com erro que foi pré-processado
        :param nome_arq_metadados: Nome do arquivo de metadados do arquivo com erro que será movido
        :param caminho_arq_metadados: Caminho do metadado do arquivo com erro que será movido
        :param msg: Se fornecida, gerará um arquivo '<caminho_erro_arq>.erro' e colocará a mensagem dentro
        :return: caminho_erro_arq: Caminho para onde o arquivo com erro foi movido
    """
    # Define os caminhos para onde o aquivo com erro e seu respectivo metadado serão movidos
    caminho_erro_lote = os.path.join(caminho_entrada, caminho_erro, codigo_lote)
    caminho_erro_arq = os.path.join(caminho_erro_lote, nome_arq)
    caminho_erro_metadados = os.path.join(caminho_erro_lote, nome_arq_metadados)

    # Prepara o destino dos arquivos
    try:
        os.makedirs(caminho_erro_lote, exist_ok=True)
    except PermissionError:
        print(f"\nErro ao criar a pasta de lote '{caminho_erro_lote}'. Permissão de escrita negada!\n")
        exit(PERMISSION_ERROR)

    # Faz a movimentação dos arquivos
    try:
        shutil.move(caminho_arq, caminho_erro_arq)
    except PermissionError:
        print(f"\nErro ao mover o arquivo '{caminho_arq}'. Permissão negada!\n")
        exit(PERMISSION_ERROR)
    except FileNotFoundError:
        print(f"\nErro ao mover o arquivo '{caminho_arq}'. O arquivo não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)

    try:
        shutil.move(caminho_arq_metadados, caminho_erro_metadados)
    except PermissionError:
        print(f"\nErro ao mover o arquivo '{caminho_arq_metadados}'. Permissão negada!\n")
        exit(PERMISSION_ERROR)
    except FileNotFoundError:
        print(f"\nErro ao mover o arquivo '{caminho_arq_metadados}'. O arquivo não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)

    # Se fornecida, gera o arquivo com a mensagem
    if msg != '':
        arq_msg = None
        caminho_arq_erro_msg = caminho_erro_arq + '.erro'

        try:
            arq_msg = open(caminho_arq_erro_msg, 'w')
        except PermissionError:
            print(f"\nErro ao criar o arquivo de erro '{caminho_arq_erro_msg}'. Permissão de gravação negada!\n")
            exit(PERMISSION_ERROR)

        arq_msg.write(f"{msg}\n")

        arq_msg.close()

    return caminho_erro_arq


def pre_processar_arquivos(tipo, caminho_entrada, caminho_base, caminho_relativo, caminho_erro, timeout_preproc):
    """
    Lê os arquivos da pasta de entrada, gera a versão em formato texto plano e persiste no banco de dados.
    Obs.: Posteriormente os arquivos serão processados pelo sistema
        :param tipo: Tipo do documento (EDITAL, etc.)
        :param caminho_entrada: Caminho da pasta de entrada dos arquivos que serão pré-processados
        :param caminho_base: Caminho base da pasta para onde os arquivos serão transferidos após o pré-processamento
        :param caminho_relativo: Caminho relativo da pasta para onde os arquivos serão transferidos após o
                                 pré-processamento
        :param caminho_erro: Caminho onde os arquivos com erro de processamento serão guardados
        :param timeout_preproc: Timeout caso o arquivo de lock não seja apagado da pasta de entrada
    """
    arquivos = None

    try:
        arquivos = os.listdir(caminho_entrada)
    except FileNotFoundError:
        print(f"\nErro ao listar os arquivos. O caminho '{caminho_entrada}' não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao listar os aquivos da pasta '{caminho_entrada}'. Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    # O Caminho do arquivo de lock foi definido aqui por conta do escopo, pois ele é utilizado também no else
    # do "if arquivos_pre_processar and not bloqueado"
    caminho_arq_lock = os.path.join(caminho_entrada, 'preproc.lock')
    arq_lock = None

    # Verifica se a pasta está bloqueada para pré-processamento
    bloqueado = True if 'preproc.lock' in arquivos else False

    # Verifica se tem algum arquivo com metadados para pré-processar e filtra os arquivos
    arquivos_pre_processar = []

    for a in arquivos:
        if a + ".metadados" in arquivos:
            arquivos_pre_processar.append(a)

    # Se tiver algum arquivo para pré-processar e se a pasta não estiver bloqueada
    if arquivos_pre_processar and not bloqueado:
        # Gera um arquivo de lock para evitar que dois processos pré-processem os arquivos ao mesmo tempo
        try:
            arq_lock = open(caminho_arq_lock, 'w')
        except PermissionError:
            print(f"\nErro ao criar o arquivo de lock. Permissão de gravação negada!\n")
            exit(PERMISSION_ERROR)

        codigo_lote = ger.gerar_codigo_lote()

        # Bloqueia a pasta
        arq_lock.write(f"{time.time()}\n\n*** LOCK *** NÃO EDITE!!!\nPré-processamento do lote {codigo_lote}\n\n"
                       f"Nota: Se este arquivo de lock não estiver sendo apagado automaticamente, o módulo de "
                       f"pré-processamento está com problemas para executar. Verifique os logs do módulo!")

        arq_lock.close()

        # O MongoDB roda em uma

        # Cria a conexão com o banco de dados
        c_mongo_doc = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_documentos')
        c_mongo_meta = ClienteGenerico('MongoDB', 'localhost', 27017, 'db_metadados')

        # Avalia em quais coleções/índices irá persistir os dados
        colecao_mongo = None

        if tipo == 'EDITAL':
            colecao_mongo = 'col_editais'

        # Gera um lote para o pré-processamento
        lote = Lote(codigo_lote, tipo, time.time())

        print(f"\n#------- Iniciando o pré-processamento do lote {codigo_lote} -------#")
        print(f"\n# Tipo do Lote: {tipo}")
        print(f"\n# Lista de arquivos a serem pré-processados: \n{arquivos_pre_processar}")

        # contador para os arquivos
        total = len(arquivos_pre_processar)
        cont = 1

        for a in arquivos_pre_processar:
            caminho_arq = os.path.join(caminho_entrada, a)
            nome_arq_metadados = a + ".metadados"
            print(f"\nArquivo ({cont}/{total}): {a}", end='')
            cont += 1

            caminho_arq_metadados = os.path.join(caminho_entrada, nome_arq_metadados)
            metadados = obter_metadados_aux(caminho_arq_metadados)

            # Complementa os metadados com parâmetros do sistema
            metadados['tipo'] = tipo
            metadados['caminho_base'] = caminho_base
            metadados['caminho_relativo'] = caminho_relativo

            # Guardará o resultado do pré-processamento
            resultado = Resultado(tipo='PREPROC', codigo_lote=codigo_lote, data_resultado=ger.gerar_epoch())
            resultado.nome_arq_original = metadados['nome_arq_original']
            resultado.tipo_arq = metadados['tipo']
            resultado.codigo_arq = metadados['codigo_arq']
            resultado.url_web = metadados['url_web']
            resultado.usuario_cadastrou = metadados['usuario_cadastrou']
            resultado.data_cadastro = metadados['data_cadastro']

            doc, validado, relatorio = ler_arquivo(caminho_arq, a, metadados['codigo_arq'], codigo_lote,
                                                   metadados['tipo'])

            if validado:
                doc_meta = ger.gerar_metadados_doc(codigo_lote, metadados, doc)

                if doc_meta:
                    # Verifica se o documento já existe no banco de dados
                    doc_mongo_teste_js = c_mongo_meta.buscar_um('col_metadados_docs', 'Documento__hash_md5',
                                                                doc_meta.hash_md5)

                    # Só continua se o documento não existir no banco
                    if doc_mongo_teste_js is None:
                        mover_arq_ok(doc_meta.caminho_base, doc_meta.caminho_relativo, doc_meta.codigo_lote, a,
                                     caminho_arq, caminho_arq_metadados)

                        doc_json_mongo = ser.serializar(doc)
                        c_mongo_doc.inserir(colecao_mongo, doc_json_mongo)

                        # Grava os metadados
                        doc_meta_json = ser.serializar(doc_meta)
                        c_mongo_meta.inserir('col_metadados_docs', doc_meta_json)

                        resultado.status = 'OK'

                        # Atualiza a lista de documentos ok
                        lote.inserir_documento(doc_meta.codigo_arq)

                        # Imprime no final da impressão do nome arquivo para facilitar buscas no log
                        print(" -> OK", end='')

                    else:
                        resultado.status = 'FALHOU'

                        # Atualiza a lista de documentos com erro
                        lote.inserir_documento(metadados['codigo_arq'], 0)

                        msg_erro = "  *> Erro ao inserir. Este documento já consta na base de dados!"
                        msg_erro_hash = f"  *> Hash do arquivo: {doc_meta.hash_md5}"
                        resultado.inserir_mensagem(msg_erro)
                        resultado.inserir_mensagem("  *> Não é permitida a inclusão de documentos em duplicidade.")

                        mover_arq_erro(codigo_lote, caminho_entrada, caminho_erro, a, caminho_arq,
                                       nome_arq_metadados, caminho_arq_metadados, msg_erro + "\n" + msg_erro_hash)

                        print(f"\n{msg_erro}\n{msg_erro_hash}")

                else:
                    print(f"\nErro ao gerar os metadados do arquivo '{caminho_arq}'!\n")
                    exit(CREATE_METADATA_ERROR)
            else:
                msg_erro = f"  *> Erro ao processar o arquivo '{caminho_arq}'. Falha ao extrair o texto!"
                print(f"\n{msg_erro}")

                caminho_erro_arq = mover_arq_erro(codigo_lote, caminho_entrada, caminho_erro, a, caminho_arq,
                                                  nome_arq_metadados, caminho_arq_metadados, msg_erro)

                # Se o documento tiver conteúdo (mesmo que seja incompleto), descarrega num arquivo
                # para que a causa seja investigada manualmente
                if doc:
                    descarregar_conteudo(doc, tipo, caminho_erro_arq + '.erro_dump', relatorio)

                # Atualiza a lista de documentos com erro
                lote.inserir_documento(metadados['codigo_arq'], 0)

                # Informa o resultado
                resultado.status = 'FALHOU'
                resultado.inserir_mensagem("  *> Erro ao processar o arquivo. Falha ao extrair o texto!")
                resultado.inserir_mensagem("  *> O arquivo cadastrado está corrompido ou o conteúdo possui uma "
                                           "codificação inválida.")

            # Salva o resultado no banco
            resultado_meta_json = ser.serializar(resultado)
            c_mongo_meta.inserir('col_metadados_resultados', resultado_meta_json)

        # Finaliza o lote
        lote.tempo_fim = time.time()

        # Obtém as estatísticas do lote
        estatisticas = lote.obter_estatisticas()

        # Grava o lote somente se houve pré-processamento
        if estatisticas['total_docs'] > 0:
            lote_json = ser.serializar(lote)
            c_mongo_meta.inserir('col_metadados_lotes', lote_json)

        c_mongo_doc.fechar_conexao()
        c_mongo_meta.fechar_conexao()

        # Libera para o próximo pré-processamento
        try:
            os.remove(caminho_arq_lock)
        except PermissionError:
            print(f"\nErro ao apagar o arquivo de lock. Permissão negada!\n")
            exit(PERMISSION_ERROR)

        print(f"\nEstatísticas do lote: {estatisticas}")
        print(f"\n#------- FIM do pré-processamento do lote {codigo_lote} -------#\n")

    # É para pré-processar, mas a pasta está bloqueada
    elif arquivos_pre_processar:
        # Recupera o tempo que arquivo de lock foi criado e calcula sua idade. Se for maior que o parâmetro
        # 'timeout_preproc' aborta o módulo
        try:
            arq_lock = open(caminho_arq_lock, 'r')
        except PermissionError:
            print(f"\nErro ao ler o arquivo de lock. Permissão de leitura negada!\n")
            exit(PERMISSION_ERROR)

        # Calcula a idade e transforma em minutos, por conta do parâmetro 'timeout_preproc'
        idade = (time.time() - float(arq_lock.readline().rstrip('\n'))) / 60

        arq_lock.close()

        if idade <= timeout_preproc:
            print(f"\nA pasta '{caminho_entrada}' está bloqueada para pré-processamento neste momento!\n")
        else:
            print(f"\nA pasta '{caminho_entrada}' está bloqueada para pré-processamento há cerca de {int(idade)} "
                  f"minutos.\nEste valor ultrapassou o tempo máximo ({timeout_preproc} minutos) e por isso o módulo"
                  f" será ** ABORTADO **. Verifique os logs!\n")
            exit(TIMEOUT_ERROR)
    else:
        print(f"\nNenhum arquivo para pré-processar na pasta '{caminho_entrada}'")
