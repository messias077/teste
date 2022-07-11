# -----------------------------------------------------------------------------
# Suprime as mensagens do módulo tensorflow reclamando que não tem CUDA e
# desativa o uso de GPU
# -----------------------------------------------------------------------------
import os
import logging

# Desativa os warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.FATAL)

# Desativa o uso de GPU
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
