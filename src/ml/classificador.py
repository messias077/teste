# ----------------------------------------------------------------
# Funções para prover a classificação de subseções dos documentos
# ----------------------------------------------------------------

import pandas as pd
import numpy as np
import os
import fileinput
import pickle
from unicodedata import normalize
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import cross_val_score
from sklearn.metrics import confusion_matrix
from src.ambiente.parametros_globais import FILE_NOT_FOUND_ERROR, PERMISSION_ERROR, REN_CAMINHO_ARQ_CONF, \
    ML_CAMINHO_ARQ_CONF
from src.ambiente.preparar_ambiente import inicializar_parametros, validar_pastas
from src.classes.modelos_ml.modelos import ModeloClassificacao
from src.utils.geradores import gerar_data, gerar_epoch


def concatenar_datasets(caminho_datasets, caminho_arq_saida):
    """
    Concatena vários datasets num único arquivo
        :param caminho_datasets: Caminho onde estão os datasets que serão concatenados
        :param caminho_arq_saida: Caminho do arquivo que será gerado com os datasets concatenados
    """
    datasets = None

    try:
        datasets = os.listdir(caminho_datasets)
    except FileNotFoundError:
        print(f"\nErro ao listar os arquivos. O caminho '{caminho_datasets}' não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao listar os aquivos da pasta '{caminho_datasets}'. Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    # Monta os caminhos dos arquivos de datasets
    datasets = [os.path.join(caminho_datasets, d) for d in datasets]

    # Grava o cabeçalho do arquivo de saída
    with open(caminho_arq_saida, 'w') as fout:
        fout.write("Subseção\tTipo\n")

    # Concatena os arquivos de datasets
    with open(caminho_arq_saida, 'a') as fout, fileinput.input(datasets) as fin:
        for line in fin:
            fout.write(line)


def tratar_strings(x, remover_stop_words=False):
    """
    Trata as strings do dataset, retirando caracteres especiais e stopwords
        :param x: dataset a ser tratado
        :param remover_stop_words: Indica se as stopwords serão removidas
        :return: Dataset tratado
    """
    algumas_stop_words = ['a', 'ao', 'aos', 'as', 'com', 'da', 'das', 'de', 'do', 'dos', 'e', 'em', 'lhe', 'mas', 'me',
                          'na', 'nas', 'nem', 'no', 'nos', 'num', 'o', 'os', 'ou', 'por', 'que', 'se', 'te', 'teu',
                          'tu', 'tua', 'um', 'uma', 'vos']
    strings_tratadas = []

    for i in range(len(x)):
        # Retira acentuação
        aux = normalize('NFKD', str(x[i][0])).encode('ASCII', 'ignore').decode('ASCII')

        # Se for o caso, remove as stopwords
        if remover_stop_words:
            split_aux = aux.split()
            aux = [w for w in split_aux if w.lower() not in algumas_stop_words]
            aux = ' '.join(aux)

        strings_tratadas.append(aux)

    return np.array(strings_tratadas)


def salvar_modelo(modelo, nome_modelo, caminho):
    """
    Salva um modelo num arquivo
        :param modelo: Objeto com o modelo que será salvo
        :param nome_modelo: Nome do modelo. O arquivo criado terá o nome do modelo
        :param caminho: Caminho onde o modelo será salvo
    """
    arquivos = None

    try:
        arquivos = os.listdir(caminho)
    except FileNotFoundError:
        print(f"\nErro ao verificar a pasta de destino dos modelos. O caminho '{caminho}' não foi encontrado!\n")
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f"\nErro ao listar os aquivos da pasta '{caminho}'. Permissão de leitura negada!\n")
        exit(PERMISSION_ERROR)

    nome_arq_modelo = nome_modelo + '.pkl'
    resp = 's'

    if nome_arq_modelo in arquivos:
        resp = 'perguntar'
        print(f"\nO arquivo contendo o modelo do classificador '{nome_arq_modelo}' já existe! "
              f"Deseja sobrescrevê-lo? (S/N): ", end='')

        while resp != 's' and resp != 'n':
            resp = input().lower()

            if resp != 's' and resp != 'n':
                print("Resposta incorreta! Digite S ou N: ", end='')

    if resp == 's':
        arq = None
        caminho_arq_modelo = os.path.join(caminho, nome_arq_modelo)

        try:
            arq = open(caminho_arq_modelo, 'wb')
        except FileNotFoundError:
            print(f'\nErro ao salvar o modelo. O caminho "{caminho_arq_modelo}" está incorreto!\n')
            exit(FILE_NOT_FOUND_ERROR)
        except PermissionError:
            print(f'\nErro ao salvar o modelo no caminho "{caminho_arq_modelo}". Permissão de escrita negada!\n')
            exit(PERMISSION_ERROR)

        pickle.dump(modelo, arq)
        arq.close()


def carregar_modelo(nome_modelo, caminho=''):
    """
    Carrega um modelo lido de um arquivo
        :param nome_modelo: Nome do modelo. O arquivo criado terá o nome do modelo
        :param caminho: Caminho onde o modelo será salvo
        :return: modelo que foi carregado do arquivo
    """
    arq = None
    caminho_arq_modelo = os.path.join(caminho, nome_modelo + '.pkl')

    try:
        arq = open(caminho_arq_modelo, 'rb')
    except FileNotFoundError:
        print(f'\nErro ao carregar o modelo. O caminho "{caminho_arq_modelo}" não foi encontrado!\n')
        exit(FILE_NOT_FOUND_ERROR)
    except PermissionError:
        print(f'\nErro ao carregar o modelo do caminho "{caminho_arq_modelo}". Permissão de leitura negada!\n')
        exit(PERMISSION_ERROR)

    modelo = pickle.load(arq)
    arq.close()
    return modelo


def salvar_relatorio(relatorio, caminho, nome_modelo):
    """
    Salva um relatório (no formato csv) com as métricas no drive
        :param relatorio: Dicionário com o relatório a ser salvo
        :param caminho: Caminho onde o relatório será salvo
        :param nome_modelo: Nome do modelo que gerou o relatório
    """
    if not relatorio:
        print(f"\nO relatório do modelo '{nome_modelo}' está vazio!")
        return

    arq_saida = None
    caminho_arquivo_saida = os.path.join(caminho, f"metricas_{nome_modelo}_"
                                                  f"{gerar_data(gerar_epoch(), '%Y-%m-%d_%H%M%Shs')}.csv")

    try:
        arq_saida = open(caminho_arquivo_saida, 'w')
    except PermissionError:
        print(f'\nErro ao criar o aquivo "{caminho_arquivo_saida}". Permissão de escrita negada!\n')
        exit(PERMISSION_ERROR)

    print(f"Salvando o relatório de métricas em '{caminho_arquivo_saida}'...OK!")
    arq_saida.write('label,precision,recall,f1-score\n')

    for label in relatorio.keys():
        if label != 'accuracy':
            arq_saida.write(f"{label},{relatorio[label]['precision']},{relatorio[label]['recall']},"
                            f"{relatorio[label]['f1-score']}\n")
        else:
            arq_saida.write(f"{label},,,{relatorio[label]}\n")

    arq_saida.close()


# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    # Obtém o caminho do arquivo de configuração ren para montar o caminho completo
    caminho_arquivo_configuracao_ren = REN_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao_ren = 'param_ren.conf'
    arq_conf_ren = os.path.join(caminho_arquivo_configuracao_ren, nome_arquivo_configuracao_ren)

    conf_ren = inicializar_parametros('ren', arq_conf_ren)

    # Obtém os parâmetros de configuração
    parametros1 = {'caminho_arq_conf': arq_conf_ren,
                   'p_caminho_datasets': conf_ren.obter_valor_parametro('p_caminho_datasets')}

    # Valida os parâmetros lidos dos arquivos de configuração
    validar_pastas(parametros1)

    # Obtém o caminho do arquivo de configuração ml para montar o caminho completo
    caminho_arquivo_configuracao_ml = ML_CAMINHO_ARQ_CONF
    nome_arquivo_configuracao_ml = 'param_ml.conf'
    arq_conf_ml = os.path.join(caminho_arquivo_configuracao_ml, nome_arquivo_configuracao_ml)

    conf_ml = inicializar_parametros('ml', arq_conf_ml)

    # Obtém os parâmetros de configuração
    parametros2 = {'caminho_arq_conf': arq_conf_ml,
                   'p_caminho_modelos_testes': conf_ml.obter_valor_parametro('p_caminho_modelos_testes'),
                   'p_caminho_relatorio_metricas': conf_ml.obter_valor_parametro('p_caminho_relatorio_metricas')}

    validar_pastas(parametros2)

    # Parâmetros para leitura dos datasets e tratamento das strings
    separador = '\t'  # Separador dos campos do arquivo de dados CSV
    nome_subpasta = 'etiquetados'  # Local dos datasets que já foram etiquetados manualmente
    nome_arq_saida = 'dataset_concatenado.csv'
    colunas_selecionadas_x = ['Subseção']  # features (características utilizadas para inferir o target)
    colunas_selecionadas_y = ['Tipo']  # target (alvo pretendido para cada linha do arquivo de dados CSV)
    seed_randomica = 1
    remover_stop_words = True

    # Quantidade de folds utilizadas no cross validation para cada treinamento.
    folds = 2

    # Seleciona os modelos que serão rodados:
    # 1=SGDClassifier, 2=DecisionTreeClassifier, 3=RandomForestClassifier, 4=GradientBoostingClassifier
    # 5=MultinomialNB, 6=SVC, 7=MLPClassifier, 8=xgboost
    numeros_modelos = [1, 2, 3, 4, 5, 6, 7, 8]

    caminho_datasets = os.path.join(parametros1['p_caminho_datasets'], nome_subpasta)
    caminho_dataset_concatenado = os.path.join(parametros1['p_caminho_datasets'], nome_arq_saida)

    concatenar_datasets(caminho_datasets, caminho_dataset_concatenado)

    dados = pd.read_csv(caminho_dataset_concatenado, dtype=str, sep=separador)

    # Separa em features e targets
    X = dados[colunas_selecionadas_x]
    y = dados[colunas_selecionadas_y]
    dados = None  # Não vai mais precisar deste dataframe

    # Transforma o dataframe num array
    X = np.array(X)
    y = np.array(y).reshape(-1)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.4, shuffle=True, random_state=seed_randomica)

    # Não vai mais precisar deles
    X = None
    y = None

    print(f"\n\n==> Dimensões dos datasets depois do split:\n")
    print(f"X Treino.....: {X_train.shape}")
    print(f"y Treino.....: {y_train.shape}\n")
    print(f"X Teste......: {X_test.shape}")
    print(f"y Teste......: {y_test.shape}\n")

    # Trata as strings
    X_train = tratar_strings(X_train, remover_stop_words=remover_stop_words)
    X_test = tratar_strings(X_test, remover_stop_words=remover_stop_words)

    for numero_modelo in numeros_modelos:
        # Escolhe o modelo
        clf = ModeloClassificacao(numero_modelo)

        print(f"\n==> Rodando o modelo número {numero_modelo}: '{clf.nome}'...")

        # Treina o modelo
        clf.fit(X_train, y_train)

        # Faz predição no treino
        ypred = clf.predict(X_test)

        # Avalia os resultados
        resultado = accuracy_score(y_test, ypred)

        print(f"\n*************** RESULTADOS DO TREINO (Modelo: {clf.nome}) ***************")
        print(f"\n - Acurácia:\n {resultado}")

        print("\n - Matriz de confusão:\n", confusion_matrix(ypred, y_test))

        relatorio_str = classification_report(y_test, ypred)

        print("\n - Relatório de métricas:")
        print(relatorio_str)

        relatorio_dict = classification_report(y_test, ypred, output_dict=True)
        salvar_relatorio(relatorio_dict, parametros2['p_caminho_relatorio_metricas'], clf.nome)

        salvar_modelo(clf, clf.nome, parametros2['p_caminho_modelos_testes'])

        if folds > 0:
            print(f"\n==> Treino adicional utilizando validação cruzada (Modelo: {clf.nome})...")
            scores = cross_val_score(clf, X_train, y_train, cv=folds, n_jobs=-1)
            print("\n - Cross validation:")
            print(" Scores............:", list(scores))
            print(" Acurácia média....:", np.mean(scores))
