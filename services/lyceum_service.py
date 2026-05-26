"""
Módulo: services/lyceum_service.py
Responsável por realizar web scraping do portal acadêmico Lyceum.
"""

import requests
from bs4 import BeautifulSoup
import re

class LyceumService:
    """Serviço para extração de dados do portal Lyceum."""

    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def autenticar(self, base_url, usuario, senha):
        """
        Realiza o login no portal. 
        Nota: A estrutura de login do Lyceum costuma usar campos como 'login' e 'senha'.
        """
        # Exemplo genérico de URL de login (precisa ser validado com a URL real)
        login_url = f"{base_url.rstrip('/')}/login.asp"
        
        payload = {
            'login': usuario,
            'senha': senha,
            'OK': 'OK'
        }

        try:
            response = self.session.post(login_url, data=payload, headers=self.headers, timeout=10)
            # Verifica se o login foi bem sucedido (geralmente redireciona ou não contém erro 'inválido')
            if "inválid" in response.text.lower() or response.status_code != 200:
                return False, "Credenciais inválidas ou portal inacessível."
            return True, "Autenticação realizada com sucesso."
        except Exception as e:
            return False, f"Erro na conexão: {str(e)}"

    def extrair_notas(self, base_url):
        """
        Acessa a página de notas e extrai as informações.
        """
        # URL comum para notas no Lyceum
        notas_url = f"{base_url.rstrip('/')}/notas.asp"
        
        try:
            response = self.session.get(notas_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # TODO: Implementar lógica de parse baseada na estrutura HTML real do portal
            # Geralmente é uma tabela com as colunas: Disciplina, Média Final, Frequência
            dados_extraidos = []
            
            # Este é um exemplo hipotético do que seria o parse:
            # for row in soup.find_all('tr'):
            #     cols = row.find_all('td')
            #     if len(cols) > 3:
            #         dados_extraidos.append({
            #             'disciplina': cols[0].text.strip(),
            #             'nota': float(cols[1].text.replace(',', '.')),
            #             'frequencia': float(cols[2].text.replace('%', '').strip())
            #         })

            return dados_extraidos
        except Exception as e:
            print(f"Erro ao extrair notas: {e}")
            return []
