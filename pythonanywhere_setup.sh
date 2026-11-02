#!/bin/bash
# Instala o AgroPedidos no PythonAnywhere. Uso:
#   git clone https://github.com/aanjelaa/agropedidos.git && bash agropedidos/pythonanywhere_setup.sh
set -e
cd "$(dirname "$0")"
PY=python3.10
command -v $PY >/dev/null || PY=python3
VERSAO=$($PY -c "import sys;print(f'{sys.version_info.major}.{sys.version_info.minor}')")

echo "== AgroPedidos: instalação no PythonAnywhere (usuário: $USER) =="
# Plano gratuito do PythonAnywhere não tem MySQL: usa SQLite (arquivo agropedidos.db).
# Em conta paga, rode com USAR_MYSQL=1 para gravar a senha do MySQL.
if [ "$USAR_MYSQL" = "1" ] && [ ! -s ~/.agropedidos_senha ]; then
  read -r -s -p "Digite a senha do MySQL que você criou na aba Databases: " SENHA; echo
  printf '%s' "$SENHA" > ~/.agropedidos_senha
  chmod 600 ~/.agropedidos_senha
fi
[ -s ~/.agropedidos_chave ] || { $PY -c "import secrets;print(secrets.token_hex(32))" > ~/.agropedidos_chave; chmod 600 ~/.agropedidos_chave; }

echo "== Instalando bibliotecas (pode levar 1-2 minutos) =="
$PY -m pip install --user -q -r requirements.txt

echo "== Criando tabelas e dados de exemplo =="
$PY -c "
import wsgi_pythonanywhere as w
from app.comandos import popular_exemplo
with w.application.app_context():
    print('Dados de exemplo inseridos.' if popular_exemplo() else 'O banco já tinha dados; nada foi alterado.')
"

cat <<FIM

== Pronto! Falta só criar o site na aba Web ==
1) Aba "Web" > "Add a new web app" > Next > "Manual configuration" > "Python $VERSAO" > Next
2) Clique no link do "WSGI configuration file", APAGUE tudo e cole estas 3 linhas:

import sys, os
sys.path.insert(0, os.path.expanduser('~/agropedidos'))
from wsgi_pythonanywhere import application

3) Clique em "Save" e depois, na aba Web, no botão verde "Reload".
Seu sistema: https://$USER.pythonanywhere.com
Login: admin@agropedidos.com / admin123
FIM
