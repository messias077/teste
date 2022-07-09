# ----------------------------------------------------------------
# Funções para a impressão/descarga do conteúdo de objetos em
# arquivos texto
# ----------------------------------------------------------------
from src.ambiente.parametros_globais import PERMISSION_ERROR


def descarregar_conteudo(obj, tipo_dump, nome_arq, cabecalho=None):
    """
    Descarrega o conteúdo de um objeto num arquivo
        :param obj: Objeto com o conteúdo que será descarregado
        :param tipo_dump: Tipo do dump (EDITAL, SECOES, CONTEUDO, etc.)
        :param nome_arq: Nome do arquivo que será criado para receber o conteúdo
        :param cabecalho: Dicionário contendo um cabeçalho para ser gravado no arquivo criado para receber o conteúdo
    """

    if obj:
        arq = None

        # Cria o arquivo para descarregar o conteúdo do objeto
        try:
            arq = open(nome_arq, 'w')
        except PermissionError:
            arq.write(f"\nErro ao criar o arquivo {nome_arq} . Permissão de gravação negada!\n")
            exit(PERMISSION_ERROR)

        if cabecalho:
            for c, v in cabecalho.items():
                arq.write(f"{c}{v}\n")

        # Faz o dump do conteúdo completo do edital e das seções que foram extraidas
        if tipo_dump == 'EDITAL':
            arq.write(f"\n> Nome do arquivo: {obj.nome}\n")
            arq.write(f"\n> Código do lote: {obj.codigo_lote}\n")
            arq.write(f"\n> Dump do conteúdo:\n\n")

            if obj.dumpconteudo:
                for pag, cont in enumerate(obj.dumpconteudo):
                    arq.write(f"  - Pag. {pag + 1}: {cont}\n")

            # Descarrega as seções e subseções
            if obj.secoes:
                for s in obj.secoes:
                    arq.write(f"\n# Seção: {s.numero} - Pág(s) {s.paginas}: {s.titulo} ")

                    if s.subsecoes:
                        for sb in s.subsecoes:
                            arq.write(f"{sb.numero}: {sb.descricao} ")

        # Faz o dump somente das seções e subseções extraídas do edital
        elif tipo_dump == 'SECOES':
            if hasattr(obj, "secoes"):
                # Descarrega as seções e subseções
                if obj.secoes:
                    for s in obj.secoes:
                        arq.write(f"# Seção: {s.numero} - Pág(s) {s.paginas}: {s.titulo} ")

                        if s.subsecoes:
                            for sb in s.subsecoes:
                                arq.write(f"{sb.numero}: {sb.descricao} ")

                        arq.write(f"\n")

        # Faz o dump somente do conteúdo completo
        elif tipo_dump == 'CONTEUDO':
            if obj.dumpconteudo:
                for pag, cont in enumerate(obj.dumpconteudo):
                    arq.write(f"Pag {pag + 1}: {cont}\n")

        arq.close()
