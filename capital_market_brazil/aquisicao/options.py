from enum import Enum


class EnumETL(Enum):
    ibge = 'IBGE'
    cvm = 'CVM'
    bacen = 'BACEN'
    b_tres = 'B3'


# chave = Enum
# valor = Classe de objeto ETL
ETL_DICT = {}
