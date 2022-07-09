# ----------------------------------------------------------------
# Funções para preparação do ambiente de execução do módulo
# ----------------------------------------------------------------

import os
import src.utils.geradores as ger
from src.classes.configs import Config, Parametro
from src.ambiente.parametros_globais import FILE_NOT_FOUND_ERROR, PERMISSION_ERROR, UNDEFINED_CONFIGURATION, \
    PARAMETER_ERROR


def criar_template_conf(conf):
    """
    Cria um template de arquivo de configuração com os nomes de parâmetros definidos no sistema
        :param conf: Objeto contendo as configurações/parâmetros do sistema
    """
    nome_template = conf.caminho_arq_conf + '.template'

    if not os.path.exists(nome_template):
        arq_conf_template = None

        try:
            arq_conf_template = open(nome_template, 'w')
        except FileNotFoundError:
            print(f'\nErro ao criar o arquivo de template "{nome_template}". O caminho está incorreto!\n')
            exit(FILE_NOT_FOUND_ERROR)
        except PermissionError:
            print(f'\nErro ao criar o arquivo de template "{nome_template}". Permissão de escrita negada!\n')
            exit(PERMISSION_ERROR)

        conteudo = f'# ------------- Template gerado automaticamente pelo sistema -------------\n' \
                   f'#\n' \
                   f'# >> Se não souber preencher os valores dos parâmetros peça ajuda!\n' \
                   f'# >> Não esqueça de renomear o arquivo e tirar o ".template" do nome\n' \
                   f'# ------------------------------------------------------------------------\n' \
                   f'#\n' \
                   f'# Parâmetros para o módulo de <informe o nome do módulo aqui!>\n' \
                   f'#\n' \
                   f'# Obs.: Não utilize \'\' ou  "" (aspas simples ou duplas) nos nomes nem nos valores dos ' \
                   'parâmetros' \
                   '\n#' \
                   '\n# Uso: nome_do_parametro = valor\n\n'

        for p in conf.parametros:
            if p.persistido:
                linha = f'# {p.descricao}\n{p.nome} = coloque aqui o valor do parâmetro\n\n'
                conteudo += linha

        arq_conf_template.write(conteudo)

        if arq_conf_template:
            arq_conf_template.close()

        print(f'\nFoi criado automaticamente um arquivo de template no caminho "{nome_template}"...\n'
              f'Edite este arquivo, configure os parâmetros necessários, renomeie-o retirando o ".template" do nome '
              f'e execute o módulo novamente.\n')

    else:
        print(f'\nExiste um arquivo de template no caminho "{nome_template}".\n'
              f'Edite este arquivo, configure os parâmetros necessários, renomeie-o retirando o ".template" do nome '
              f'e execute o módulo novamente.\n')


def obter_valor_parametros(conf):
    """
    Obtém os parâmetros de configuração para o módulo rodar
        :param conf: Objeto contendo as configurações/parâmetros do sistema
    """
    arq_conf = None  # Guardará o arquivo de configuração aberto

    try:
        arq_conf = open(conf.caminho_arq_conf, 'r')
    except FileNotFoundError:
        print(f"\nErro ao abrir o arquivo de configuração '{conf.caminho_arq_conf}'. O arquivo não foi encontrado!")
        criar_template_conf(conf)
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f'\nErro ao abrir o aquivo "{conf.caminho_arq_conf}". Permissão de leitura negada!\n')
        exit(PERMISSION_ERROR)

    linhas = arq_conf.readlines()
    parametros_lidos = {}

    for linha in linhas:
        # Ignora as linhas de comentário
        if '#' not in linha:
            l_split = linha.rstrip('\n').split('=')

            # Obtém o nome e o valor do parâmetro
            if len(l_split) == 2:
                parametros_lidos[l_split[0].strip()] = l_split[1].strip()

    # Preenche os valores dos parâmetros encontrados no arquivo de configuração
    if parametros_lidos:
        for p in conf.parametros:
            if parametros_lidos.__contains__(p.nome) and p.persistido:
                erro_conversao = False
                tipo_esperado = ''

                # Verifica o tipo do parâmetro e converte se necessário
                if p.tipo == 'str':
                    p.valor = parametros_lidos[p.nome]
                elif p.tipo == 'int':
                    try:
                        p.valor = int(parametros_lidos[p.nome])
                    except ValueError:
                        erro_conversao = True
                        tipo_esperado = 'inteiro'
                elif p.tipo == 'float':
                    try:
                        p.valor = float(parametros_lidos[p.nome])
                    except ValueError:
                        erro_conversao = True
                        tipo_esperado = 'ponto flutuante'

                if erro_conversao:
                    print(f'\nErro ao ler o parâmetro "{p.nome}" do arquivo de configuração {conf.caminho_arq_conf}.'
                          f'O valor "{parametros_lidos[p.nome]}" não é um número {tipo_esperado}!\n')
                    exit(PARAMETER_ERROR)

    if arq_conf:
        arq_conf.close()


def inicializar_parametros(modulo, caminho_config):
    """
    Inicializa os parâmetros de configuração para o módulo rodar
        :param modulo: Módulo que terá os parâmetros configurados
        :param caminho_config: Caminho do arquivo de configuração
        :return: Objeto contendo parâmetros inicializados
    """
    conf = Config(caminho_config)

    if modulo == 'preproc':
        param1 = Parametro(nome='p_caminho_downloader',
                           descricao='Pasta para guardar os arquivos CSVs auxiliares utilizados no download dos '
                                     'editais',
                           persistido=True)
        conf.inserir_parametro(param1)

        param2 = Parametro(nome='p_caminho_entrada',
                           descricao='Pasta onde os arquivos são colocados para sofrerem o pré-processamento',
                           persistido=True)
        conf.inserir_parametro(param2)

        param3 = Parametro(nome='p_caminho_base',
                           descricao='Pasta base para onde os arquivos pré-processados são movidos',
                           persistido=True)
        conf.inserir_parametro(param3)

        param4 = Parametro(nome='p_caminho_dumps',
                           descricao='Pasta para gerar os dumps de impressão dos editais',
                           persistido=True)
        conf.inserir_parametro(param4)

        # Para o caminho relativo (param3) foi escolhido utilizar o ano corrente do processamento
        ano = ger.gerar_data(ger.gerar_epoch(), '%Y')

        param5 = Parametro(nome='p_caminho_relativo',
                           valor=ano,
                           descricao='Ajuda a organizar os arquivos por ano ou de outra forma que for necessária',
                           persistido=False)
        conf.inserir_parametro(param5)

        param6 = Parametro(nome='nome_pasta_erros',
                           valor='erro',
                           descricao='Nome da pasta onde serão guardados os arquivos com erro de processamento',
                           persistido=False)
        conf.inserir_parametro(param6)

        param7 = Parametro(nome='timeout_lock',
                           tipo='int',
                           descricao='Timeout caso o arquivo de lock não seja apagado da pasta de entrada. Este '
                                     'arquivo impede que dois processos leiam a pasta ao mesmo tempo. Valor em minutos',
                           persistido=True)
        conf.inserir_parametro(param7)
    elif modulo == 'ren':
        param1 = Parametro(nome='p_caminho_datasets',
                           descricao='Pasta para geração dos datasets',
                           persistido=True)
        conf.inserir_parametro(param1)

        param2 = Parametro(nome='p_tamanho_minimo_sentenca',
                           tipo='int',
                           descricao='Não considera as sentenças menores que este valor',
                           persistido=True)
        conf.inserir_parametro(param2)

        param3 = Parametro(nome='p_caminho_arq_sentencas',
                           descricao='Pasta para processamento dos arquivos com sentenças anotadas',
                           persistido=True)
        conf.inserir_parametro(param3)

        param4 = Parametro(nome='p_caminho_sentencas_base',
                           descricao='Pasta contendo arquivo pickle com as sentenças base para verificação de '
                                     'similaridade entre sentenças',
                           persistido=True)
        conf.inserir_parametro(param4)
    elif modulo == 'ml':
        param1 = Parametro(nome='p_caminho_modelos_prod',
                           descricao='Pasta onde os modelos de produção serão salvos',
                           persistido=True)
        conf.inserir_parametro(param1)

        param2 = Parametro(nome='p_caminho_modelos_testes',
                           descricao='Pasta onde os modelos de testes serão salvos',
                           persistido=True)
        conf.inserir_parametro(param2)

        param3 = Parametro(nome='p_caminho_relatorio_metricas',
                           descricao='Pasta onde os relatórios de métricas de execução dos modelos serão salvos',
                           persistido=True)
        conf.inserir_parametro(param3)
    else:
        print(f"Não existe configuração definida para o módulo '{modulo}'!\n")
        exit(UNDEFINED_CONFIGURATION)

    obter_valor_parametros(conf)

    return conf


def validar_parametros(p):
    """
    Valida os parâmetros e aborta o sistema caso algum parâmetro esteja inválido
        :param p: Dicionário contendo as configurações/parâmetros do sistema
    """
    vazio = False

    # Verifica se os parâmetros foram todos preenchidos
    for chave in p.keys():
        if p[chave] == '':
            vazio = True
            print(f"\nO valor do parâmetro '{chave}' está vazio!", end='')

    if vazio:
        print(f"\n\nEdite o arquivo de configuração ('{p['caminho_arq_conf']}') e corrija este erro.\n")
        exit(PARAMETER_ERROR)


def validar_pastas(p):
    """
    Valida os nomes das pastas
        :param p: Dicionário contendo as configurações/parâmetros do sistema
    """
    validar_parametros(p)

    # Evita pegar o nome do arquivo de configuração
    testar_caminhos = list(p.values())[1:]

    # Todos os caminhos tem que existir
    for t in testar_caminhos:
        t_aux = str(t)  # Para evitar erro em parâmetros que não são strings
        if '/' in t_aux or '\\' in t_aux:  # Evita testar parâmetros que não sejam caminhos
            if not os.path.exists(t):
                print(f"\nO caminho '{t}' não foi encontrado. Favor criar todas as pastas que constam nesse caminho!\n")
                exit(FILE_NOT_FOUND_ERROR)
