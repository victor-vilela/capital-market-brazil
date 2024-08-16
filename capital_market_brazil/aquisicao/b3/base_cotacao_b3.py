import abc
import typing
from datetime import datetime, timedelta
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait 
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd

from capital_market_brazil.aquisicao.base_etl import BaseETL


class BaseCotacaoB3ETL(BaseETL, abc.ABC):
    """
    Estrutura que qualquer objeto de ETL deve funcionar
    para baixar dados do Cotacao B3
    """

    caminho_entrada: Path
    caminho_saida: Path
    _dados_entrada: typing.Dict[str, pd.DataFrame]
    _dados_saida: typing.Dict[str, pd.DataFrame]

    @property
    def dados_entrada(self) -> typing.Dict[str, pd.DataFrame]:
        """
        Acessa o dicionario de dados de entrada

        :return: dicionário com o nome do arquivo e um dataframe com os dados
        """
        if self._dados_entrada is None:
            self.extract()
        return self._dados_entrada

    @property
    def dados_saida(self) -> typing.Dict[str, pd.DataFrame]:
        """
        Acessa o dicionario de dados de saida

        :return: dicionário com o nome do arquivo e um dataframe com os dados
        """
        if self._dados_saida is None:
            self.extract()
        return self._dados_saida

    def __init__(
        self, entrada: str, saida: str, url: str, criar_caminho: bool = True
    ) -> None:
        """
        Instancia o objeto de ETL Base

        :param entrada: string com caminho para a pasta de entrada
        :param saida: string com caminho para a pasta de saida
        :param url: URL para a pagina de dados do IBGE
        :param criar_caminho: flag indicando se devemos criar os caminhos
        """
        self.caminho_entrada = Path(entrada)
        self.caminho_saida = Path(saida)

        if criar_caminho:
            self.caminho_entrada.mkdir(parents=True, exist_ok=True)
            self.caminho_saida.mkdir(parents=True, exist_ok=True)

        self._dados_entrada = None
        self._dados_saida = None
    
    def connect_browser(
        self, url: str = 'https://www.b3.com.br/pt_br/market-data-e-indices/servicos-de-dados/market-data/cotacoes/cotacoes/'
        ) -> webdriver:
        chrome_driver_version = '126.0.6478.126'

        options = webdriver.ChromeOptions()
        options.binary_location = "/usr/bin/chromium"
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument('--remote-debugging-port=9222')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version=chrome_driver_version).install()), options=options)
        
        driver.get(url)

        driver.implicitly_wait(3)
        WebDriverWait(driver, 5).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'bvmf_iframe')),
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'iFrameResizer0'))
        )
        return driver
    
    def dict_to_download(self) -> typing.List[webdriver]: # type: ignore
        """
        Realiza um dicionario de cada item a ser baixado no site da B3

        :return: dicionario com o nome da pasta a ser criada e o elemento para ser baixado
        """
        driver = self.connect_browser()

        dias_mes = [
            datetime.strftime(
                datetime.now() - timedelta(days=dt), format="%d/%m/%Y"
            )
            for dt in range(30)
        ]
        dias_uteis = [dia for dia in dias_mes if datetime.strptime(dia, '%d/%m/%Y').isoweekday() not in [6, 7]]

        elements = []
        for dia in dias_uteis:
            try:
                elements.append(driver.find_element(By.LINK_TEXT, f'{dia}'))
            except:
                pass

        return elements
    
    def download_content(self) -> None:
        """
        Realiza o download de cada arquivo em sua respectiva pasta
        """
        driver = self.connect_browser()
        for link in self.dict_to_download():
            caminho_arq = self.caminho_saida
            with open(caminho_arq, 'wb') as arq:
                arq.write(driver.execute_script('arguments[0].click();', link))
        
    @abc.abstractmethod
    def extract(self) -> None:
        """
        Extrai os dados do objeto
        """
        pass

    def transform(self) -> None:
        """
        Transforma os dados e os adequa para os formatos de saída
        """
        pass

    def load(self) -> None:
        """
        Carrega para a saída desejada
        """
        for arq, df in self.dados_saida.items():
            df.to_parquet(self.caminho_saida / arq, index=False)

    def pipeline(self) -> None:
        """
        Executa o pipeline completo do ETL
        """
        self.extract()
        self.transform()
        self.load()
