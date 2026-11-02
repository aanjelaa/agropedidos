# AgroPedidos

Sistema web para **controle de pedidos de venda e faturamento** em revendas de insumos agrícolas (sementes, defensivos e fertilizantes).

Projeto Integrador Transdisciplinar em Sistemas de Informação II.

![Painel](docs/telas/02_painel.png)

## O que o sistema faz

- **Painel** com pedidos pendentes, faturados, entregues, **atrasados** e valor faturado no mês.
- **Clientes** (produtores rurais e empresas), com validação de CPF/CNPJ e bloqueio de duplicidade.
- **Produtos** por categoria (Sementes, Defensivos, Fertilizantes), unidade e preço.
- **Pedidos de venda** com vários itens e total calculado na hora. O preço fica registrado no momento do lançamento.
- **Fluxo de status**: Pendente → Faturado (exige nº da NF, que não pode se repetir) → Entregue. Um pedido pendente também pode ser Cancelado, informando o motivo.
- **Histórico** de cada mudança de status (quem mudou e quando).
- **Relatório de faturamento** por período, por cliente e por categoria, com exportação para CSV (Excel).
- **Perfis de acesso**: Administrador, Vendedor e Faturista.
- Layout responsivo (funciona no celular).

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.10+ |
| Framework / padrão | Flask 3, padrão **MVC** |
| Banco de dados | **MySQL 8** (produção) · SQLite (desenvolvimento local) |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Front-end | HTML5 + Jinja2, CSS3, JavaScript puro |
| Testes | pytest (31 testes automatizados) |
| Hospedagem | PythonAnywhere (plano gratuito, com MySQL) |

## Estrutura MVC

```
agropedidos/
├── app/
│   ├── models/        # MODEL: entidades e regras de negócio
│   │   ├── usuario.py  cliente.py  categoria.py  produto.py  pedido.py
│   ├── controllers/   # CONTROLLER: rotas (recebem a requisição e decidem a resposta)
│   │   ├── auth.py  painel.py  clientes.py  produtos.py  pedidos.py  usuarios.py  relatorios.py
│   ├── templates/     # VIEW: páginas HTML (Jinja2)
│   ├── static/        # VIEW: css/estilo.css e js/app.js
│   ├── utils/         # validadores (CPF/CNPJ), formatadores (R$, datas), segurança
│   ├── comandos.py    # comandos init-db e seed
│   └── config.py
├── database/schema_mysql.sql   # projeto físico do banco (MySQL)
├── docs/                       # diagramas, prints das telas e evidências de teste
├── tests/                      # testes automatizados (pytest)
├── run.py                      # ponto de entrada
└── requirements.txt
```

## Como rodar no seu computador

```bash
git clone https://github.com/SEU-USUARIO/agropedidos.git
cd agropedidos
python -m venv .venv
# Windows: .venv\Scripts\activate    |   Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
flask --app run seed     # cria o banco (SQLite) com dados de exemplo
python run.py            # abre em http://127.0.0.1:5000
```

Para usar MySQL localmente, rode `database/schema_mysql.sql` no MySQL e defina a variável de ambiente antes do `seed`:

```bash
set DATABASE_URL=mysql+pymysql://usuario:senha@localhost/agropedidos?charset=utf8mb4   # Windows
export DATABASE_URL=mysql+pymysql://usuario:senha@localhost/agropedidos?charset=utf8mb4  # Linux/Mac
```

### Usuários de demonstração

| Perfil | E-mail | Senha |
|---|---|---|
| Administrador | admin@agropedidos.com | admin123 |
| Vendedor | vendedor@agropedidos.com | vendedor123 |
| Faturista | faturista@agropedidos.com | faturista123 |

## Testes automatizados

```bash
python -m pytest -v
```

O resultado da última execução está em `docs/evidencias/resultado_pytest.txt`.

## Publicar no PythonAnywhere (gratuito)

1. Crie uma conta gratuita (Beginner) em https://www.pythonanywhere.com.
2. Na aba **Databases**, crie uma senha do MySQL (clique em *Initialize MySQL*).
3. Na aba **Consoles**, abra um **Bash** e cole:
   ```bash
   git clone https://github.com/aanjelaa/agropedidos.git && bash agropedidos/pythonanywhere_setup.sh
   ```
   O script pede a senha do MySQL, instala as bibliotecas e cria as tabelas com dados de exemplo.
4. Na aba **Web**: *Add a new web app* → *Manual configuration* → *Python 3.10*.
5. Abra o **WSGI configuration file**, apague tudo, cole as linhas abaixo e salve:
   ```python
   import sys, os
   sys.path.insert(0, os.path.expanduser('~/agropedidos'))
   from wsgi_pythonanywhere import application
   ```
6. Clique em **Reload**. O sistema fica em `https://SEU-USUARIO.pythonanywhere.com`.

Para atualizar depois de mudanças no GitHub: `cd ~/agropedidos && git pull` e **Reload** na aba Web.

---

# Manual de uso

### 1. Entrar no sistema
Informe e-mail e senha na tela de login. O menu mostra só o que o seu perfil pode usar.

### 2. Painel
Mostra quantos pedidos estão **pendentes de faturamento**, **faturados aguardando entrega**, **entregues** e **atrasados**, além do total faturado no mês. Clique em um quadro para ver a lista filtrada. A tabela "Pedidos atrasados" mostra os pedidos pendentes ou faturados cuja previsão de entrega já passou, com os dias de atraso.

### 3. Clientes (Administrador e Vendedor)
- **Novo cliente**: escolha Pessoa física (CPF) ou jurídica (CNPJ). O campo coloca a máscara sozinho e o sistema confere se o documento é válido e se já não está cadastrado.
- **Inativar**: clientes não são excluídos, para não perder o histórico de pedidos. Clientes inativos não aparecem para novos pedidos.
- Use a busca para procurar por nome, documento, cidade ou fazenda.

### 4. Produtos (cadastro: Administrador)
Cadastre código, descrição, categoria, unidade (SC, KG, L, TON, UN) e preço. Os outros perfis só consultam.

### 5. Lançar um pedido (Administrador e Vendedor)
1. Menu **Pedidos** → **+ Novo pedido**.
2. Escolha o cliente e a previsão de entrega (o sistema sugere 7 dias).
3. Em **Itens**, escolha o produto e a quantidade. Use **+ Adicionar item** para mais produtos. O subtotal e o total aparecem na hora.
4. Clique em **Salvar pedido**. O pedido nasce com status **Pendente**.

Enquanto estiver pendente, o pedido pode ser editado ou cancelado (o cancelamento exige motivo).

### 6. Faturar e entregar (Administrador e Faturista)
1. Abra o pedido. Em **Próxima etapa**, informe o **número da NF** e clique em **Faturar pedido**. Uma NF não pode ser usada em dois pedidos.
2. Quando a carga chegar ao cliente, abra o pedido e clique em **Confirmar entrega**.

Cada mudança fica registrada no **Histórico** do pedido.

### 7. Relatório de faturamento
Escolha o período e veja o total faturado, a quantidade de notas, o ticket médio, os totais por cliente e por categoria e a lista de notas. O botão **Exportar CSV** gera um arquivo que abre no Excel.

### 8. Usuários (Administrador)
Cadastre usuários e defina o perfil. A página também mostra a tabela de permissões de cada perfil.
