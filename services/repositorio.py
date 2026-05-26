"""
Módulo: services/repositorio.py
Camada de persistência simples usando JSON.
Cada repositório gerencia uma coleção de entidades em memória e persiste em arquivo.
"""

import json
import os
from typing import Optional


class Repositorio:
    """Repositório genérico com persistência em JSON."""

    def __init__(self, caminho_arquivo: str):
        self._caminho = caminho_arquivo
        self._dados: dict = {}
        self._carregar()

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #

    def salvar(self, id: str, entidade_dict: dict) -> None:
        """Salva ou atualiza uma entidade pelo ID."""
        self._dados[id] = entidade_dict
        self._persistir()

    def buscar(self, id: str) -> Optional[dict]:
        """Busca uma entidade pelo ID. Retorna None se não encontrada."""
        return self._dados.get(id)

    def listar(self) -> list:
        """Retorna todas as entidades armazenadas."""
        return list(self._dados.values())

    def deletar(self, id: str) -> bool:
        """Remove uma entidade pelo ID. Retorna True se removida."""
        if id in self._dados:
            del self._dados[id]
            self._persistir()
            return True
        return False

    def existe(self, id: str) -> bool:
        """Verifica se uma entidade com esse ID existe."""
        return id in self._dados

    def total(self) -> int:
        """Retorna o número de entidades armazenadas."""
        return len(self._dados)

    def filtrar(self, campo: str, valor) -> list:
        """Filtra entidades por um campo e valor específicos."""
        return [e for e in self._dados.values() if e.get(campo) == valor]

    # ------------------------------------------------------------------ #
    # Persistência
    # ------------------------------------------------------------------ #

    def _carregar(self) -> None:
        """Carrega os dados do arquivo JSON, se existir."""
        if os.path.exists(self._caminho):
            try:
                with open(self._caminho, "r", encoding="utf-8") as f:
                    self._dados = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._dados = {}
        else:
            os.makedirs(os.path.dirname(self._caminho), exist_ok=True)
            self._dados = {}

    def _persistir(self) -> None:
        """Salva os dados em disco no arquivo JSON."""
        with open(self._caminho, "w", encoding="utf-8") as f:
            json.dump(self._dados, f, ensure_ascii=False, indent=2)
