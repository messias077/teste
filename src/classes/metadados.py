# ----------------------------------------------------------------------------------------------
# Algumas classes que representam metadados dos documentos processados pelo sistema
#
# ATENÇÃO: Se uma nova classe for criada ou modificada e houver a necessidade de persisti-la
# em banco de dados, implemente ou altere a sua entrada na rotina da função de desserialização
# no arquivo src.classes.persistencia.serializacao.py
# ----------------------------------------------------------------------------------------------

class Documento:
    """
    Metadados dos arquivos processados para facilitar a busca por algumas propriedades deles
    """
    def __init__(self, nome='', codigo_arq='', hash_md5='', tipo_arq='', extensao='', data_cadastro=0,
                 usuario_cadastrou='', codigo_lote='', nome_arq_original='', url_web='', caminho_base='',
                 caminho_relativo='', head=None):
        self.__nome = nome
        self.__codigo_arq = codigo_arq
        self.__hash_md5 = hash_md5
        self.__tipo_arq = tipo_arq  # Se é um edital ou outro tipo (valores: EDITAL; tipos futuros)
        self.__extensao = extensao
        self.__data_cadastro = data_cadastro
        self.__usuario_cadastrou = usuario_cadastrou
        self.__cod_processamento = 'a processar'  # Guardará os códigos dos processamentos já realizados
        self.__codigo_lote = codigo_lote
        self.__nome_arq_original = nome_arq_original
        self.__url_web = url_web
        self.__caminho_base = caminho_base
        self.__caminho_relativo = caminho_relativo
        self.__head = head  # Guarda as primeiras páginas do arquivo

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """
        return {'Documento__nome': self.__nome,
                'Documento__codigo_arq': self.__codigo_arq,
                'Documento__hash_md5': self.__hash_md5,
                'Documento__tipo_arq': self.__tipo_arq,
                'Documento__extensao': self.__extensao,
                'Documento__data_cadastro': self.__data_cadastro,
                'Documento__usuario_cadastrou': self.__usuario_cadastrou,
                'Documento__cod_processamento': self.__cod_processamento,
                'Documento__codigo_lote': self.__codigo_lote,
                'Documento__nome_arq_original': self.__nome_arq_original,
                'Documento__url_web': self.__url_web,
                'Documento__caminho_base': self.__caminho_base,
                'Documento__caminho_relativo': self.__caminho_relativo,
                'Documento__head': self.__head}

    @property
    def nome(self):
        return self.__nome

    @property
    def codigo_arq(self):
        return self.__codigo_arq

    @property
    def hash_md5(self):
        return self.__hash_md5

    @property
    def tipo_arq(self):
        return self.__tipo_arq

    @property
    def extensao(self):
        return self.__extensao

    @property
    def data_cadastro(self):
        return self.__data_cadastro

    @property
    def usuario_cadastrou(self):
        return self.__usuario_cadastrou

    @property
    def cod_processamento(self):
        return self.__cod_processamento

    @property
    def codigo_lote(self):
        return self.__codigo_lote

    @property
    def nome_arq_original(self):
        return self.__nome_arq_original

    @property
    def url_web(self):
        return self.__url_web

    @property
    def caminho_base(self):
        return self.__caminho_base

    @property
    def caminho_relativo(self):
        return self.__caminho_relativo

    @property
    def head(self):
        return self.__head

    @nome.setter
    def nome(self, nome):
        self.__nome = nome

    @codigo_arq.setter
    def codigo_arq(self, codigo_arq):
        self.__codigo_arq = codigo_arq

    @hash_md5.setter
    def hash_md5(self, hash_md5):
        self.__hash_md5 = hash_md5

    @tipo_arq.setter
    def tipo_arq(self, tipo_arq):
        self.__tipo_arq = tipo_arq

    @extensao.setter
    def extensao(self, extensao):
        self.__extensao = extensao

    @data_cadastro.setter
    def data_cadastro(self, data_cadastro):
        self.__data_cadastro = data_cadastro

    @usuario_cadastrou.setter
    def usuario_cadastrou(self, usuario_cadastrou):
        self.__usuario_cadastrou = usuario_cadastrou

    @cod_processamento.setter
    def cod_processamento(self, cod_processamento):
        self.__cod_processamento = cod_processamento

    @codigo_lote.setter
    def codigo_lote(self, codigo_lote):
        self.__codigo_lote = codigo_lote

    @nome_arq_original.setter
    def nome_arq_original(self, nome_arq_original):
        self.__nome_arq_original = nome_arq_original

    @url_web.setter
    def url_web(self, url_web):
        self.__url_web = url_web

    @caminho_base.setter
    def caminho_base(self, caminho_base):
        self.__caminho_base = caminho_base

    @caminho_relativo.setter
    def caminho_relativo(self, caminho_relativo):
        self.__caminho_relativo = caminho_relativo

    @head.setter
    def head(self, head):
        self.__head = head


class Lote:
    """
    Lote gerado no pré-processamento dos arquivos de editais
    """
    def __init__(self, codigo_lote='', tipo='', tempo_inicio=0.0, tempo_fim=0.0):
        self.__codigo_lote = codigo_lote
        self.__tipo = tipo  # Tipo do documento: EDITAL, etc.
        self.__tempo_inicio = tempo_inicio
        self.__tempo_fim = tempo_fim
        self.__documentos_ok = []  # Guarda os códigos dos documentos que foram pré-processados corretamente
        self.__documentos_erro = []  # Guarda os códigos dos documentos que não foram pré-processados por conta de erro

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """
        return {'Lote__codigo_lote': self.__codigo_lote,
                'Lote__tipo': self.__tipo,
                'Lote__tempo_inicio': self.__tempo_inicio,
                'Lote__tempo_fim': self.__tempo_fim,
                'Lote__documentos_ok': self.__documentos_ok,
                'Lote__documentos_erro': self.__documentos_erro}

    @property
    def codigo(self):
        return self.__codigo_lote

    @property
    def tipo(self):
        return self.__tipo

    @property
    def tempo_inicio(self):
        return self.__tempo_inicio

    @property
    def tempo_fim(self):
        return self.__tempo_fim

    @property
    def documentos_ok(self):
        return self.__documentos_ok

    @property
    def documentos_erro(self):
        return self.__documentos_erro

    @codigo.setter
    def codigo(self, codigo):
        self.__codigo_lote = codigo

    @tipo.setter
    def tipo(self, tipo):
        self.__tipo = tipo

    @tempo_inicio.setter
    def tempo_inicio(self, tempo_inicio):
        self.__tempo_inicio = tempo_inicio

    @tempo_fim.setter
    def tempo_fim(self, tempo_fim):
        self.__tempo_fim = tempo_fim

    @documentos_ok.setter
    def documentos_ok(self, documentos_ok):
        self.__documentos_ok = documentos_ok

    @documentos_erro.setter
    def documentos_erro(self, documentos_erro):
        self.__documentos_erro = documentos_erro

    def inserir_documento(self, codigo_arq, status=1):
        """
            Insere um documento na lista de documentos OK ou na lista de documentos com erro,
            dependendo do parâmetro 'status'
                :param codigo_arq: Código do documento
                :param status: Status do pré-processamento do documento (1 = OK, 0 = Erro; valor padrão 1)
        """
        if status == 1:
            self.__documentos_ok.append(codigo_arq)
        elif status == 0:
            self.__documentos_erro.append(codigo_arq)

    def obter_estatisticas(self):
        """
            Levanta as estatísticas do pré-processamento do lote
                :return: Dicionário com as estatísticas do pré-processamento do lote
        """
        # Calcula o tempo de pré-processamento
        tempo_preproc_float = self.__tempo_fim - self.__tempo_inicio

        # transforma o tempo em minutos ou deixa no formato original
        if tempo_preproc_float >= 60:
            tempo_preproc_min = int(tempo_preproc_float // 60)
            tempo_preproc_seg = int(tempo_preproc_float % 60)
            tempo_preproc = f'{tempo_preproc_min} minuto(s)'

            if tempo_preproc_seg > 0:
                tempo_preproc = tempo_preproc + f' e {tempo_preproc_seg} segundo(s)'
        else:
            tempo_preproc = f'{tempo_preproc_float} segundo(s)'

        # Calculas as quantidades, total e taxas
        qtd_docs_ok = len(self.__documentos_ok)
        qtd_docs_erro = len(self.__documentos_erro)
        total_docs = qtd_docs_ok + qtd_docs_erro
        taxa_ok = 0.0
        taxa_erro = 0.0

        # Evita a divisão por 0!
        if total_docs > 0:
            taxa_ok = qtd_docs_ok / total_docs
            taxa_erro = qtd_docs_erro / total_docs

        estatisticas = {'tempo_preproc': tempo_preproc, 'qtd_docs_ok': qtd_docs_ok, 'qtd_docs_erro': qtd_docs_erro,
                        'total_docs': total_docs, 'taxa_ok': taxa_ok, 'taxa_erro': taxa_erro}

        return estatisticas


class Resultado:
    """
    Resultado do pré-processamento/processamento dos arquivos de editais
    """
    def __init__(self, tipo='', codigo_lote='', data_resultado=0, status='', nome_arq_original='', tipo_arq='',
                 codigo_arq='', url_web='', usuario_cadastrou='', data_cadastro=0):
        self.__tipo = tipo  # Tipo do resultado (PREPROC = Pré-processamento, PROC = Processamento)
        self.__codigo_lote = codigo_lote
        self.__data_resultado = data_resultado  # Data em que o resultado foi gerado
        self.__status = status  # OK ou FALHOU
        self.__nome_arq_original = nome_arq_original
        self.__tipo_arq = tipo_arq  # Tipo do arquivo (EDITAL, etc.)
        self.__codigo_arq = codigo_arq
        self.__url_web = url_web
        self.__usuario_cadastrou = usuario_cadastrou
        self.__data_cadastro = data_cadastro  # Data de cadasto do arquivo no sistema
        self.__mensagens = []  # Mensagens diversas a cerca do pré-processamento/processamento

    # Obs.: Precisei criar esta propriedade para facilitar na serialização de objetos para gravação no Elasticsearch,
    #       pois se o nome da chave do dicionário começar com '_' (underscore), a mesma não é indexada para realização
    #       de buscas "full-text", ou seja, somente é possível buscar passando o nome da chave e o valor a ser buscado.
    @property
    def __mydict__(self):
        """
            Cria um dicionário com os atributos da classe como chave
                :return: dicionário sem o '_' (underscore) no início do nome da chave.
        """

        return {'Resultado__tipo': self.__tipo,
                'Resultado__codigo_lote': self.__codigo_lote,
                'Resultado__data_resultado': self.__data_resultado,
                'Resultado__status': self.__status,
                'Resultado__nome_arq_original': self.__nome_arq_original,
                'Resultado__tipo_arq': self.__tipo_arq,
                'Resultado__codigo_arq': self.__codigo_arq,
                'Resultado__url_web': self.__url_web,
                'Resultado__usuario_cadastrou': self.__usuario_cadastrou,
                'Resultado__data_cadastro': self.__data_cadastro,
                'Resultado__mensagens': self.__mensagens}

    @property
    def tipo(self):
        return self.__tipo

    @property
    def codigo_lote(self):
        return self.__codigo_lote

    @property
    def data_resultado(self):
        return self.__data_resultado

    @property
    def status(self):
        return self.__status

    @property
    def nome_arq_original(self):
        return self.__nome_arq_original

    @property
    def tipo_arq(self):
        return self.__tipo_arq

    @property
    def codigo_arq(self):
        return self.__codigo_arq

    @property
    def url_web(self):
        return self.__url_web

    @property
    def usuario_cadastrou(self):
        return self.__usuario_cadastrou

    @property
    def data_cadastro(self):
        return self.__data_cadastro

    @property
    def mensagens(self):
        return self.__mensagens

    @tipo.setter
    def tipo(self, tipo):
        self.__tipo = tipo

    @codigo_lote.setter
    def codigo_lote(self, codigo_lote):
        self.__codigo_lote = codigo_lote

    @data_resultado.setter
    def data_resultado(self, data_resultado):
        self.__data_resultado = data_resultado

    @status.setter
    def status(self, status):
        self.__status = status

    @nome_arq_original.setter
    def nome_arq_original(self, nome_arq_original):
        self.__nome_arq_original = nome_arq_original

    @tipo_arq.setter
    def tipo_arq(self, tipo_arq):
        self.__tipo_arq = tipo_arq

    @codigo_arq.setter
    def codigo_arq(self, codigo_arq):
        self.__codigo_arq = codigo_arq

    @url_web.setter
    def url_web(self, url_web):
        self.__url_web = url_web

    @usuario_cadastrou.setter
    def usuario_cadastrou(self, usuario_cadastrou):
        self.__usuario_cadastrou = usuario_cadastrou

    @data_cadastro.setter
    def data_cadastro(self, data_cadastro):
        self.__data_cadastro = data_cadastro

    @mensagens.setter
    def mensagens(self, mensagens):
        self.__mensagens = mensagens

    def inserir_mensagem(self, msg):
        self.__mensagens.append(msg)
