"""Ponto de entrada da aplicação AgroPedidos.

Execução local:   python run.py
Criar o banco:    flask --app run init-db
Dados de exemplo: flask --app run seed
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
