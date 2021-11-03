import re
import logging
import requests
from lxml import html
from typing import Tuple
from flask import Response
from bs4 import BeautifulSoup
from flask_restful import Resource
from requests.structures import CaseInsensitiveDict

LOGGER = logging.getLogger(__name__)

BASE_URL = 'https://nfse.campinas.sp.gov.br/NotaFiscal'
VERIFY_NFSE_URL = f'{BASE_URL}/action/notaFiscal/verificarAutenticidade.php'
XPATH_PATTERN = '//table[@class="impressaoTabela"]/tr/td[@class="impressaoLabel"]/span'


class Bill(Resource):
    def __init__(self) -> None:
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        self.headers = headers

    def get(self) -> dict:
        return self.get_bill_general_info()

    def get_data(self) -> str:
        cnpj = 'rPrest=10.831.692/0001-73'
        note_number = 'rNumNota=1886'
        municipal_registration = 'rInsMun=1628534'
        verification_code =  'rCodigoVerificacao=8eb34d2809793d1d8aabdcb4fb7488d9bd2cfe58'
        verification_button = 'btnVerificar=Verificar'
        cid_code = 'rCodCid=6291'

        data = f'{cnpj}&{note_number}&{municipal_registration}&{verification_code}&{cid_code}&{verification_button}'

        return data

    def get_bill_url_and_cookies(self) -> Tuple:
        try:
            LOGGER.debug(f'Posting data on {VERIFY_NFSE_URL}...')
            resp = requests.post(VERIFY_NFSE_URL, headers=self.headers, data=self.get_data())

            soup = BeautifulSoup(resp.text, features="lxml")
            script_text = soup.find('script').string
            url_regex = re.search("'(.*?)'", script_text)
            url_query = url_regex.group(0)[6:-1]
            url = BASE_URL + url_query

            return (url, resp.cookies)
        except requests.exceptions.HTTPError as error:
            LOGGER.error(f'An error has occurred: {error}')
            return Response(f"{{'error':'{error}'}}", status=error, mimetype='application/json')
        except requests.exceptions.RequestException as error:
            LOGGER.critical(f'A critical error has occurred: {error}')

    def get_bill_general_info(self) -> dict:
        url, cookies = self.get_bill_url_and_cookies()

        try:
            LOGGER.debug(f'Getting infos from {url}...')
            resp = requests.get(url, cookies=cookies)

            tree = html.fromstring(resp.text)
            info_from_url = tree.xpath(XPATH_PATTERN)

            provider_info = {}
            provider_info['razao_social'] = info_from_url[0].text
            provider_info['cnpj'] = info_from_url[1].text
            provider_info['inscricao_municipal'] = info_from_url[2].text
            provider_info['endereco'] = info_from_url[3].text
            provider_info['municipio'] = info_from_url[4].text
            provider_info['uf'] = info_from_url[5].text
            provider_info['telefone'] = info_from_url[6].text

            taker_info = {}
            taker_info['razao_social'] = info_from_url[7].text
            taker_info['cnpj'] = info_from_url[8].text
            taker_info['inscricao_municipal'] = info_from_url[9].text
            taker_info['endereco'] = info_from_url[10].text
            taker_info['municipio'] = info_from_url[11].text
            taker_info['uf'] = info_from_url[12].text
            taker_info['email'] = info_from_url[13].text
            taker_info['telefone'] = info_from_url[14].text

            return {
                'info' : {
                    'provider_info': provider_info,
                    'taker_info': taker_info
                }
            }
        except requests.exceptions.HTTPError as error:
            LOGGER.error(f'An error has occurred: {error}')
            return Response(f"{{'error':'{error}'}}", status=error, mimetype='application/json')
        except Exception as error:
            LOGGER.warning(f'Information not found: {error}')
            return Response(f"{{'error':'information not found'}}", status=400, mimetype='application/json')
        except requests.exceptions.RequestException as error:
            LOGGER.critical(f'A critical error has occurred: {error}')
