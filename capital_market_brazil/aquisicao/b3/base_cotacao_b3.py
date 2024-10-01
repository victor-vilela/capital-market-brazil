import abc
import os
import typing
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from pathlib import Path
import requests
import httplib2
import wget
import shutil
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
        self, 
        entrada: str, 
        saida: str, 
        url: str, 
        start: int = 30, 
        criar_caminho: bool = True
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
        
        self._start = datetime.now() - timedelta(days = start)
    
    def list_to_download(self):
        files = [
            file.replace('.zip','')
            for file in os.listdir(self.caminho_entrada) 
            if file.endswith('.zip')
        ]
        download_dates = pd.to_datetime(files)

        current_date = datetime.now().date()
        data_range = pd.date_range(self._start.date(), current_date)
        return data_range.difference(download_dates)

    def download_content(self) -> None:
        """
        Realiza o download de cada arquivo em sua respectiva pasta
        """
        data_range_to_download = self.list_to_download()
        http_client = httplib2.Http(str(self.caminho_entrada / '.cache'))

        for market_date in data_range_to_download:
            formatted_date = market_date.strftime('%Y-%m-%d')
            url = str(self._url) + formatted_date
            
            try:
                # Requisição HTTP
                response, content = http_client.request(
                    str(url), headers={'Connection': 'keep-alive'}
                )
                
                # Verifica se o conteúdo existe antes de baixar
                if response.status == 200 and len(content) > 0:
                    file_path = f'{formatted_date}.zip'
                    path_download = self.caminho_entrada / file_path
                    wget.download(url, str(path_download))
                    print(f"\nArquivo {file_path} baixado com sucesso.")
                else:
                    print(f"\nArquivo não encontrado para a data: {formatted_date}")
            
            except Exception as e:
                print(f"\nErro ao baixar arquivo para a data {formatted_date}: {e}")

        # Limpeza do cache
        shutil.rmtree(self.caminho_entrada / '.cache', ignore_errors=True)
        
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
