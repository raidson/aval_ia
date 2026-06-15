"""
Módulo: tests/test_api.py
Testes unitários para a API do SIMPA, utilizando o padrão Application Factory.
"""

import unittest
import sys
import os
import json
import uuid

# Adiciona o diretório raiz ao path para permitir importações de módulos da aplicação
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.app import create_app, _tokens_ativos
from services.database import get_connection, init_db, close_connection

class TestApi(unittest.TestCase):
    """Conjunto de testes para os endpoints da API Flask com isolamento de estado."""

    def setUp(self):
        """
        Configuração executada antes de cada teste.
        Cria uma nova instância da aplicação e um banco de dados limpo.
        """
        self.db_filename = f"test_database_{self._testMethodName}.db"
        self.app = create_app({"TESTING": True, "DATABASE_URL": self.db_filename})
        self.client = self.app.test_client()

        with self.app.app_context():
            self._populate_test_data()

        self.token = "test-token-for-setup"
        self.test_user_id = "user-test-admin-001"
        _tokens_ativos[self.token] = self.test_user_id
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def tearDown(self):
        """Limpeza executada após cada teste."""
        _tokens_ativos.clear()
        with self.app.app_context():
            close_connection()
        try:
            if os.path.exists(self.db_filename):
                os.remove(self.db_filename)
        except Exception as e:
            pass

    def _populate_test_data(self):
        """Popula o banco de dados em memória com dados de teste."""
        conn = get_connection()
        cursor = conn.cursor()

        self.aluno1_id = "aluno-test-001"
        self.aluno2_id = "aluno-test-002"

        cursor.execute("INSERT INTO usuarios (id, nome, matricula, perfil, senha_hash, ativo) VALUES (?, ?, ?, ?, ?, ?)",
                       ("user-test-admin-001", "Admin Teste", "admin01", "admin", "hashed_password", True))
        cursor.execute("INSERT INTO alunos (id, matricula, nome, curso, periodo, notas, frequencias) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (self.aluno1_id, "2024001", "Aluno A", "Engenharia de Software", 2, 
                        json.dumps([{"disciplina": "Cálculo I", "nota": 8.5, "periodo": 2}]), 
                        json.dumps([{"disciplina": "Cálculo I", "percentual": 90, "periodo": 2}])))
        cursor.execute("INSERT INTO alunos (id, matricula, nome, curso, periodo, notas, frequencias) VALUES (?, ?, ?, ?, ?, ?, ?)",
                       (self.aluno2_id, "2024002", "Aluno B", "Engenharia de Software", 2, 
                        json.dumps([{"disciplina": "Cálculo I", "nota": 4.5, "periodo": 2}]), 
                        json.dumps([{"disciplina": "Cálculo I", "percentual": 70, "periodo": 2}])))
        cursor.execute("INSERT OR IGNORE INTO disciplinas (cod_disciplina, nome) VALUES (?, ?)", (101, "Cálculo I"))
        cursor.execute("INSERT INTO registros_academicos (aluno_id, cod_disciplina, nome_disciplina, turma, serie, ano, semestre, media_final, situacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (self.aluno1_id, 101, "Cálculo I", "TURMA_A", 2, 2024, 1, 8.5, "Aprovado"))
        cursor.execute("INSERT INTO registros_academicos (aluno_id, cod_disciplina, nome_disciplina, turma, serie, ano, semestre, media_final, situacao) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (self.aluno2_id, 101, "Cálculo I", "TURMA_A", 2, 2024, 1, 4.5, "Rep_Nota"))
        
        conn.commit()

    def test_01_listar_turmas_endpoint(self):
        """Testa se o endpoint /turmas retorna uma lista de turmas com sucesso."""
        response = self.client.get("/turmas", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], "TURMA_A")

    def test_02_relatorio_detalhado_turma_endpoint(self):
        """Testa o endpoint de relatório detalhado da turma."""
        response = self.client.get("/turmas/TURMA_A/relatorio", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("turma", data)
        self.assertEqual(data["turma"]["id"], "TURMA_A")
        self.assertEqual(len(data["alunos"]), 2)

    def test_03_get_turma_charts_endpoint(self):
        """Testa o novo endpoint de gráficos Bokeh."""
        response = self.client.get("/api/charts/turma/TURMA_A", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("scatter", data)
        self.assertIn("script", data["scatter"])
        self.assertTrue(data["scatter"]["script"].strip().startswith("<script"))

if __name__ == "__main__":
    unittest.main()
