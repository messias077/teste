""" Desativa as mensagens de warning e info do TensorFlow """
import os
import logging

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.FATAL)

""" Desativa o uso de GPU """
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
