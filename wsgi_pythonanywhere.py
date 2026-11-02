# Copie este conteúdo para o arquivo WSGI do PythonAnywhere
# (aba Web > "WSGI configuration file") e ajuste USUARIO e SENHA.
import os
import sys

USUARIO = "seuusuario"           # seu usuário do PythonAnywhere
SENHA_MYSQL = "sua-senha-mysql"  # definida na aba Databases

projeto = f"/home/{USUARIO}/agropedidos"
if projeto not in sys.path:
    sys.path.insert(0, projeto)

os.environ["SECRET_KEY"] = "troque-por-um-texto-longo-e-aleatorio"
os.environ["DATABASE_URL"] = (
    f"mysql+pymysql://{USUARIO}:{SENHA_MYSQL}"
    f"@{USUARIO}.mysql.pythonanywhere-services.com/{USUARIO}$agropedidos?charset=utf8mb4"
)

from run import app as application  # noqa: E402
