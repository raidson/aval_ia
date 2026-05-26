"""
Módulo: models/usuario.py
Representa um usuário do sistema com perfil e permissões de acesso.
"""

from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import hashlib
import secrets


class PerfilUsuario(Enum):
    """Perfis de acesso disponíveis no sistema."""
    ADMIN = "admin"
    PROFESSOR = "professor"
    COORDENADOR = "coordenador"
    VISUALIZADOR = "visualizador"


PERMISSOES_POR_PERFIL = {
    PerfilUsuario.ADMIN: ["leitura", "escrita", "exclusao", "relatorios", "usuarios"],
    PerfilUsuario.COORDENADOR: ["leitura", "escrita", "relatorios"],
    PerfilUsuario.PROFESSOR: ["leitura", "escrita"],
    PerfilUsuario.VISUALIZADOR: ["leitura"],
}


@dataclass
class Usuario:
    """Representa um usuário autenticado no Nexus."""

    id: str
    nome: str
    matricula: str
    perfil: PerfilUsuario
    _senha_hash: str = ""
    _token: str = ""
    ativo: bool = True
    criado_em: str = ""

    def __post_init__(self):
        if not self.criado_em:
            self.criado_em = datetime.now().isoformat()

    # ------------------------------------------------------------------ #
    # Autenticação
    # ------------------------------------------------------------------ #

    def definir_senha(self, senha: str) -> None:
        """Armazena a senha como hash SHA-256 (simplificado para fins didáticos)."""
        self._senha_hash = hashlib.sha256(senha.encode()).hexdigest()

    def verificar_senha(self, senha: str) -> bool:
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return self._senha_hash == hashlib.sha256(senha.encode()).hexdigest()

    def gerar_token(self) -> str:
        """Gera um token simples de sessão."""
        self._token = secrets.token_hex(32)
        return self._token

    def token_valido(self, token: str) -> bool:
        """Verifica se o token fornecido é válido."""
        return self._token != "" and self._token == token

    # ------------------------------------------------------------------ #
    # Permissões
    # ------------------------------------------------------------------ #

    def tem_permissao(self, acao: str) -> bool:
        """Verifica se o usuário tem permissão para realizar uma ação."""
        return acao in PERMISSOES_POR_PERFIL.get(self.perfil, [])

    def get_permissoes(self) -> list:
        """Retorna a lista de permissões do perfil do usuário."""
        return PERMISSOES_POR_PERFIL.get(self.perfil, [])

    # ------------------------------------------------------------------ #
    # Serialização
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nome": self.nome,
            "matricula": self.matricula,
            "perfil": self.perfil.value,
            "ativo": self.ativo,
            "criado_em": self.criado_em,
        }

    def __repr__(self) -> str:
        return f"Usuario(matricula={self.matricula!r}, perfil={self.perfil.value!r})"
