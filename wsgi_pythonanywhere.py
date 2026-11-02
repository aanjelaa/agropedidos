"""Configuração para rodar o AgroPedidos no PythonAnywhere.

Não é preciso editar este arquivo: o usuário é detectado sozinho e a senha
do MySQL é lida do arquivo ~/.agropedidos_senha (criado pelo
pythonanywhere_setup.sh).
"""
import getpass
import os
import sys

PROJETO = os.path.dirname(os.path.abspath(__file__))
if PROJETO not in sys.path:
    sys.path.insert(0, PROJETO)

USUARIO = getpass.getuser()
ARQ_SENHA = os.path.expanduser("~/.agropedidos_senha")
ARQ_CHAVE = os.path.expanduser("~/.agropedidos_chave")

if "DATABASE_URL" not in os.environ and os.path.exists(ARQ_SENHA):
    from urllib.parse import quote_plus
    senha = open(ARQ_SENHA, encoding="utf-8").read().strip()
    os.environ["DATABASE_URL"] = (
        f"mysql+pymysql://{USUARIO}:{quote_plus(senha)}"
        f"@{USUARIO}.mysql.pythonanywhere-services.com/{USUARIO}$default?charset=utf8mb4"
    )
if "SECRET_KEY" not in os.environ and os.path.exists(ARQ_CHAVE):
    os.environ["SECRET_KEY"] = open(ARQ_CHAVE, encoding="utf-8").read().strip()

from run import app as application  # noqa: E402
