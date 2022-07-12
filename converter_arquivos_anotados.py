# -----------------------------------------------------------------------------
# Converte os arquivos que foram anotados e exportados, no formato JSONL,
# pela ferramenta Docanno para o formato CONLL
#
# Obs.: Utiliza os parâmetros padrões. Para escolher outros parâmetros
# utilizar a interface interativa do programa: 'python interface_prog.py'
# -----------------------------------------------------------------------------
from src.utils import suprimir_warning_tf
from src.modulos.ren.conversor_jsonl_conll import converter_jsonl_conll

# Obs.: para rodar este script diretamente no caminho dele, tem que configurar a variável PYTHONPATH com o caminho do
# projeto. Exemplo no Linux: export PYTHONPATH='/dados/develop/PycharmProjects/mestrado'
if __name__ == "__main__":
    # Converte os arquivos anotados para o formato CONLL
    converter_jsonl_conll(retirar_sentencas_semelhantes=True, escopo_global_sentencas=True, tamanho_dataset_teste=0.3,
                          concatenar_arquivos=True)
