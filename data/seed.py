"""
Módulo: data/seed.py
Gera dados simulados para desenvolvimento e testes.
Execute: python data/seed.py
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import hashlib
import uuid
from services.database import init_db
from services.repositorio import Repositorio
from services.repositorio_sqlite import RepositorioSQLite
from services.aluno_service import AlunoService

ALUNOS_SEED = [
    {"nome": "Ana Silva",       "matricula": "2024001", "curso": "IA", "periodo": 2, "email": "ana@uni.edu"},
    {"nome": "Bruno Costa",     "matricula": "2024002", "curso": "IA", "periodo": 2, "email": "bruno@uni.edu"},
    {"nome": "Carla Mendes",    "matricula": "2024003", "curso": "IA", "periodo": 2, "email": "carla@uni.edu"},
    {"nome": "Diego Souza",     "matricula": "2024004", "curso": "IA", "periodo": 2, "email": "diego@uni.edu"},
    {"nome": "Elena Rocha",     "matricula": "2024005", "curso": "IA", "periodo": 2, "email": "elena@uni.edu"},
]

NOTAS_SEED = [
    # (disciplina, nota, periodo)
    ("POO",         8.5, 2), ("Estatística",  7.0, 2), ("Álgebra Linear", 9.0, 2),
    ("POO",         4.5, 2), ("Estatística",  3.0, 2), ("Álgebra Linear", 5.5, 2),
    ("POO",         9.0, 2), ("Estatística",  8.5, 2), ("Álgebra Linear", 9.5, 2),
    ("POO",         6.0, 2), ("Estatística",  5.5, 2), ("Álgebra Linear", 4.0, 2),
    ("POO",         7.5, 2), ("Estatística",  6.5, 2), ("Álgebra Linear", 7.0, 2),
]

FREQUENCIAS_SEED = [
    # (disciplina, percentual, periodo)
    ("POO", 90.0, 2), ("Estatística", 85.0, 2), ("Álgebra Linear", 88.0, 2),
    ("POO", 60.0, 2), ("Estatística", 55.0, 2), ("Álgebra Linear", 70.0, 2),
    ("POO", 95.0, 2), ("Estatística", 92.0, 2), ("Álgebra Linear", 98.0, 2),
    ("POO", 80.0, 2), ("Estatística", 75.0, 2), ("Álgebra Linear", 65.0, 2),
    ("POO", 78.0, 2), ("Estatística", 82.0, 2), ("Álgebra Linear", 80.0, 2),
]

def popular_banco():
    init_db()
    repo = RepositorioSQLite("alunos")
    repo_usuarios = RepositorioSQLite("usuarios")
    service = AlunoService(repo)

    print("Populando alunos e usuários de alunos...")
    alunos_criados = []
    
    # Gerar senhas hash para usuários alunos
    # Para o teste, usamos CPFs fictícios simples
    cpf_base = 11111111111
    
    for i, dados in enumerate(ALUNOS_SEED):
        try:
            aluno = service.cadastrar(**dados)
            # Notas e frequências (3 por aluno)
            for j in range(3):
                disc, nota, per = NOTAS_SEED[i * 3 + j]
                aluno = service.registrar_nota(aluno.id, disc, nota, per)
                disc, freq, per = FREQUENCIAS_SEED[i * 3 + j]
                aluno = service.registrar_frequencia(aluno.id, disc, freq, per)
            alunos_criados.append(aluno)
            
            # Criar usuário para o aluno
            usuario_id = str(uuid.uuid4())
            cpf_aluno = str(cpf_base + i)
            senha_hash = hashlib.sha256(cpf_aluno.encode()).hexdigest()
            
            repo_usuarios.salvar(usuario_id, {
                "id": usuario_id,
                "nome": aluno.nome,
                "matricula": aluno.matricula,
                "perfil": "visualizador",
                "senha_hash": senha_hash,
                "ativo": True,
            })
            
            print(f"  [OK] {aluno.nome} ({aluno.matricula} - Senha CPF: {cpf_aluno})")
        except ValueError as e:
            print(f"  - {dados['nome']} já existe, pulando.")

    # Usuário admin padrão
    admin_id = str(uuid.uuid4())
    senha_hash = hashlib.sha256("3558".encode()).hexdigest()
    repo_usuarios.salvar(admin_id, {
        "id": admin_id,
        "nome": "Administrador",
        "matricula": "admin",
        "perfil": "admin",
        "senha_hash": senha_hash,
        "ativo": True,
    })
    print("\n  [OK] Usuário admin criado")
    print("    Matrícula: admin")
    print("    Senha: 3558")
    print(f"\nTotal de alunos cadastrados: {repo.total()}")
    print("Seed concluído com sucesso!")

if __name__ == "__main__":
    popular_banco()
