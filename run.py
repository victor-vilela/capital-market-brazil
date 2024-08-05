import click

import capital_market_brazil.configs as conf_geral
from capital_market_brazil.aquisicao.options import ETL_DICT, EnumETL


@click.group()
def cli():
    pass


@cli.group()
def aquisicao():
    """
    Grupo de comandos que executam as funcoes de aquisicao
    """
    pass


@aquisicao.command()
@click.option(
    '--etl',
    type=click.Choice([c.value for c in EnumETL]),
    help='Nome do ETL a ser executado',
)
@click.option(
    '--entrada',
    defaul=conf_geral.PASTA_DADOS,
    help='Caminho para a pasta de entrada',
)
@click.option(
    '--saida',
    defaul=conf_geral.PASTA_SAIDA_AQUISICAO,
    help='Caminho para a pasta de saida',
)
@click.option(
    '--criar_caminho',
    defaul=True,
    help='Flag indicando se deve criar os caminhos',
)
def processa_dado(
    etl: str, entrada: str, saida: str, criar_caminho: bool
) -> None:
    """
    Executa o pipeline de ETL de uma determinada fonte

    :param etl: nome do ETL a ser executado
    :param entrada: string com caminho para a pasta de entrada
    :param saida: string com caminho para a pasta de saida
    :param criar_caminho: flag indicando se devemos criar os caminhos
    """
    objeto = ETL_DICT[EnumETL(etl)](entrada, saida, criar_caminho)
    objeto.pipeline()


if __name__ == '__main__':
    cli()
