import abc
import os
import typing
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
import requests
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
        super().__init__(entrada, saida, criar_caminho)
        
        self._url = url
        
        self._driver = self.connect_browser()
    
    def connect_browser(self) -> webdriver:
        chrome_driver_version = '126.0.6478.126'

        options = webdriver.ChromeOptions()
        options.binary_location = "/usr/bin/chromium"
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--headless')
        options.add_argument('--remote-debugging-port=9222')

        driver = webdriver.Chrome(service=Service(ChromeDriverManager(driver_version=chrome_driver_version).install()), options=options)
        
        driver.get(self._url)

        driver.implicitly_wait(3)
        WebDriverWait(driver, 5).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'bvmf_iframe')),
            EC.frame_to_be_available_and_switch_to_it((By.ID, 'iFrameResizer0'))
        )
        return driver
    
    def dict_to_download(self) -> typing.Dict[str, webdriver]: # type: ignore
        """
        Realiza um dicionario de cada item a ser baixado no site da B3

        :return: dicionario com o nome da pasta a ser criada e o elemento para ser baixado
        """

        dias_mes = [
            datetime.strftime(
                datetime.now() - timedelta(days=dt), format="%d/%m/%Y"
            )
            for dt in range(30)
        ]
        
        html_element = self._driver.find_element(By.XPATH, '/html/body/div/div/div/div[2]').get_attribute('outerHTML')
        soup = BeautifulSoup(html_element, 'html.parser')

        elements = {}
        for dia in dias_mes:
            try:
                key_folder = datetime.strptime(dia, '%d/%m/%Y').strftime('%Y_%m') + '.zip'
                
                if key_folder not in elements:
                    elements[key_folder] = []
                
                # Captura o elemento e adiciona à lista correspondente
                element = soup.find('a').attrs['href']
                elements[key_folder].append(element)
            except:
                pass

        return elements
    
    def download_content(self) -> None:
        """
        Realiza o download de cada arquivo em sua respectiva pasta
        """
        
        for name_folder, list_link in self.dict_to_download().items():
            with open(self.caminho_entrada / name_folder, 'wb') as arq:
                for link in list_link:
                    r = requests.get(link, stream = True)
                    arq.write(r.content)
        
    # @abc.abstractmethod
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
