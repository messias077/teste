# ----------------------------------------------------------------
# Funções para serializar e desserializar os objetos para
# persistir no banco de dados
# ----------------------------------------------------------------

import json
import datetime
from src.classes.documentos import Edital, Secao, Subsecao
from src.classes.metadados import Documento, Lote, Resultado
from src.ambiente.parametros_globais import INVALID_CONTENT, KEY_ERROR


# Função obtida em https://ajudantedeprogramador.wordpress.com/tag/simplejson/
def default_parser(obj):
    """
    Parser padrão para conversão de objetos complexos em JSON
        :param obj: Objeto a ser convertido
        :return: Objeto convertido
    """
    if hasattr(obj, "__mydict__"):
        return obj.__mydict__  # Utilizando uma propriedade criada na classe e não o __dict__ padrão da classe Object
    elif type(obj) == datetime:
        return obj.isoformat()
    else:
        return str(obj)


def serializar(obj):
    """
    Recebe o objeto e transforma em JSON
        :param obj: Objeto a ser serializado
        :return: Objeto convertido em JSON
    """
    if not obj:
        print('\nO objeto não contém informação válida!\n')
        exit(INVALID_CONTENT)

    # Transforma primeiro para string
    obj_js_str = json.dumps(obj, default=default_parser)

    # Transforma num dicionário
    obj_js = json.loads(obj_js_str)

    return obj_js


def desserializar(result_dict):
    """
    Recebe o objeto do tipo dicionário que foi extraido do formato JSON, instancia um objeto da classe correspondente
    e preenche com os dados obtidos do dicionário
        :param result_dict: Dicionário contendo os dados
        :return: Objeto desserializado
    """
    if not result_dict:
        print("\nO parâmetro 'result_dict' não contém informação válida!\n")
        exit(INVALID_CONTENT)

    doc = None

    # Escolhe de qual classe o objeto será instanciado e preenche com os dados obtidos do dicionário
    if result_dict.__contains__('Edital__nome'):
        # Cria os novos objetos e preenche com os dados obtidos do dicionário
        doc = Edital()
        secoes_js = None  # Seções no formato Json

        try:
            doc.nome = result_dict['Edital__nome']
            doc.codigo_arq = result_dict['Edital__codigo_arq']
            doc.codigo_lote = result_dict['Edital__codigo_lote']
            doc.dumpconteudo = result_dict['Edital__dumpconteudo']
            secoes_js = result_dict['Edital__secoes']
        except KeyError as ke:
            print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
            exit(KEY_ERROR)

        secoes_obj = []  # Seções no formato de objeto

        # Percorre o encadeamento de objetos e obtém os dados
        for s in secoes_js:
            secao = Secao()
            subsecoes_js = None

            try:
                secao.numero = s['Secao__numero']
                secao.titulo = s['Secao__titulo']
                secao.paginas = s['Secao__paginas']
                subsecoes_js = s['Secao__subsecoes']
            except KeyError as ke:
                print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
                exit(KEY_ERROR)

            subsecoes_obj = []

            for sub in subsecoes_js:
                subsecao = Subsecao()

                try:
                    subsecao.numero = sub['Subsecao__numero']
                    subsecao.descricao = sub['Subsecao__descricao']
                    subsecao.pagina = sub['Subsecao__pagina']
                except KeyError as ke:
                    print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
                    exit(KEY_ERROR)

                subsecoes_obj.append(subsecao)

            secao.subsecoes = subsecoes_obj
            secoes_obj.append(secao)

        doc.secoes = secoes_obj

    elif result_dict.__contains__('Documento__nome'):
        doc = Documento()

        try:
            doc.nome = result_dict['Documento__nome']
            doc.codigo_arq = result_dict['Documento__codigo_arq']
            doc.hash_md5 = result_dict['Documento__hash_md5']
            doc.tipo_arq = result_dict['Documento__tipo_arq']
            doc.extensao = result_dict['Documento__extensao']
            doc.data_cadastro = int(result_dict['Documento__data_cadastro'])
            doc.usuario_cadastrou = result_dict['Documento__usuario_cadastrou']
            doc.codigo_lote = result_dict['Documento__codigo_lote']
            doc.cod_processamento = result_dict['Documento__cod_processamento']
            doc.nome_arq_original = result_dict['Documento__nome_arq_original']
            doc.url_web = result_dict['Documento__url_web']
            doc.caminho_base = result_dict['Documento__caminho_base']
            doc.caminho_relativo = result_dict['Documento__caminho_relativo']
            doc.head = result_dict['Documento__head']
        except KeyError as ke:
            print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
            exit(KEY_ERROR)

    elif result_dict.__contains__('Lote__codigo_lote'):
        doc = Lote()

        try:
            doc.codigo_lote = result_dict['Lote__codigo_lote']
            doc.tipo = result_dict['Lote__tipo']
            doc.tempo_inicio = float(result_dict['Lote__tempo_inicio'])
            doc.tempo_fim = float(result_dict['Lote__tempo_fim'])
            doc.documentos_ok = result_dict['Lote__documentos_ok']
            doc.documentos_erro = result_dict['Lote__documentos_erro']
        except KeyError as ke:
            print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
            exit(KEY_ERROR)

    elif result_dict.__contains__('Resultado__tipo'):
        doc = Resultado()

        try:
            doc.tipo = result_dict['Resultado__tipo']
            doc.codigo_lote = result_dict['Resultado__codigo_lote']
            doc.data_resultado = int(result_dict['Resultado__data_resultado'])
            doc.status = result_dict['Resultado__status']
            doc.nome_arq_original = result_dict['Resultado__nome_arq_original']
            doc.tipo_arq = result_dict['Resultado__tipo_arq']
            doc.codigo_arq = result_dict['Resultado__codigo_arq']
            doc.url_web = result_dict['Resultado__url_web']
            doc.usuario_cadastrou = result_dict['Resultado__usuario_cadastrou']
            doc.data_cadastro = int(result_dict['Resultado__data_cadastro'])
            doc.mensagens = result_dict['Resultado__mensagens']
        except KeyError as ke:
            print(f"\nA chave {ke} não foi encontrada. Revise a persistência de dados!\n")
            exit(KEY_ERROR)

    return doc
