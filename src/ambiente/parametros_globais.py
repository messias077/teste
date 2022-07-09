# ----------------------------------------------------------------------------
# Parâmetros globais que podem ser importados para facilitar a execução dos 
# módulos
#
# Obs.: Estes parâmetros podem ser definidos apenas pelos desenvolvedores do
# sistema. Para parâmetros passíveis de serem configurados pelos usuários,
# serão utilizados arquivos de configuração específicos para cada módulo
#
# Uso: Crie o parâmetro aqui e importe no módulo ou arquivo .py
#
# Exemplo:
# from src.utils.parametros_globais import <nome do parâmetro>
# ----------------------------------------------------------------------------

"""
Parâmetro: Caminhos dos arquivos de configuração
"""
# Módulo preproc
PREPROC_CAMINHO_ARQ_CONF = './src/modulos/preproc'

# Módulo ren
REN_CAMINHO_ARQ_CONF = './src/modulos/ren'

# Módulo ml
ML_CAMINHO_ARQ_CONF = './src/ml'

"""
Parâmetros: Limites para aceitação de documentos na rotina de validação
"""
# Função "validar_conteudo" no arquivo pdf.py
PERCENTUAL_PERMITIDO_PAGINAS_EM_BRANCO = 0.3
PERCENTUAL_PERMITIDO_PAGINAS_QTD_MINIMA_TERMOS = 0.3
PERCENTUAL_PERMITIDO_PAGINAS_TERMOS_ESTRANHOS = 0.05
PERCENTUAL_PERMITIDO_TERMOS_ESTRANHOS = 0.05  # Por página
QUANTIDADE_MINIMA_TERMOS_POR_PAGINA = 20
TAMANHO_MAXIMO_PALAVRA = 46
QUANTIDADE_MAXIMA_NAO_ALFANUM = 10

"""
Parâmetro: Códigos de erros para o comando exit() no tratamento de exceções
"""
# FileNotFoundError
FILE_NOT_FOUND_ERROR = 5

# FileExistsError
FILE_EXISTS_ERROR = 6

# PermissionError
PERMISSION_ERROR = 7

# Erro de conexão com a base de dados
CONNECTION_ERROR = 8

# Tipo de banco de dados não definido
UNDEFINED_DATABASE_TYPE = 9

# Configuração não definida para o módulo
UNDEFINED_CONFIGURATION = 10

# Erro ao gerar metadados do arquivo
CREATE_METADATA_ERROR = 11

# Objeto ou variável não contém informação válida
INVALID_CONTENT = 12

# Tempo limite esgotado
TIMEOUT_ERROR = 13

# Erro na validação de parâmetro do arquivo de configuração
PARAMETER_ERROR = 14

# Erro de chave não encontrada
KEY_ERROR = 15

# Erro de modelo do Spacy não encontrado
SPACY_MODEL_NOT_FOUND_ERROR = 16

# Erro de valor
VALUE_ERROR = 17
