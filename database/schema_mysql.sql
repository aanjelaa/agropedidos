-- =====================================================================
-- AgroPedidos - Controle de Pedidos e Faturamento de Insumos Agrícolas
-- Projeto Físico do Banco de Dados - SGBD: MySQL 8.x
-- =====================================================================

CREATE DATABASE IF NOT EXISTS agropedidos
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;

USE agropedidos;

-- ---------------------------------------------------------------------
-- Tabela: usuario  (quem opera o sistema)
-- ---------------------------------------------------------------------
CREATE TABLE usuario (
  id            INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  nome          VARCHAR(100)  NOT NULL,
  email         VARCHAR(120)  NOT NULL,
  senha_hash    VARCHAR(255)  NOT NULL,
  perfil        ENUM('ADMIN','VENDEDOR','FATURISTA') NOT NULL DEFAULT 'VENDEDOR',
  ativo         TINYINT(1)    NOT NULL DEFAULT 1,
  criado_em     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_usuario PRIMARY KEY (id),
  CONSTRAINT uq_usuario_email UNIQUE (email)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabela: cliente  (produtor rural / empresa compradora)
-- ---------------------------------------------------------------------
CREATE TABLE cliente (
  id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome                VARCHAR(120) NOT NULL,
  tipo_pessoa         ENUM('F','J') NOT NULL,
  cpf_cnpj            VARCHAR(14)  NOT NULL,          -- só dígitos
  inscricao_estadual  VARCHAR(20)  NULL,
  propriedade         VARCHAR(120) NULL,              -- nome da fazenda/sítio
  cidade              VARCHAR(80)  NOT NULL,
  uf                  CHAR(2)      NOT NULL,
  telefone            VARCHAR(20)  NULL,
  email               VARCHAR(120) NULL,
  ativo               TINYINT(1)   NOT NULL DEFAULT 1,
  criado_em           DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT pk_cliente PRIMARY KEY (id),
  CONSTRAINT uq_cliente_cpf_cnpj UNIQUE (cpf_cnpj),
  CONSTRAINT ck_cliente_doc CHECK (
    (tipo_pessoa = 'F' AND CHAR_LENGTH(cpf_cnpj) = 11) OR
    (tipo_pessoa = 'J' AND CHAR_LENGTH(cpf_cnpj) = 14))
) ENGINE=InnoDB;

CREATE INDEX ix_cliente_nome ON cliente (nome);

-- ---------------------------------------------------------------------
-- Tabela: categoria  (Sementes, Defensivos, Fertilizantes...)
-- ---------------------------------------------------------------------
CREATE TABLE categoria (
  id    INT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome  VARCHAR(60)  NOT NULL,
  CONSTRAINT pk_categoria PRIMARY KEY (id),
  CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabela: produto
-- ---------------------------------------------------------------------
CREATE TABLE produto (
  id              INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  codigo          VARCHAR(20)   NOT NULL,
  descricao       VARCHAR(150)  NOT NULL,
  categoria_id    INT UNSIGNED  NOT NULL,
  unidade         ENUM('SC','KG','L','TON','UN') NOT NULL,
  preco_unitario  DECIMAL(12,2) NOT NULL,
  ativo           TINYINT(1)    NOT NULL DEFAULT 1,
  CONSTRAINT pk_produto PRIMARY KEY (id),
  CONSTRAINT uq_produto_codigo UNIQUE (codigo),
  CONSTRAINT fk_produto_categoria FOREIGN KEY (categoria_id)
    REFERENCES categoria (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_produto_preco CHECK (preco_unitario > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabela: pedido  (cabeçalho do pedido de venda)
-- ---------------------------------------------------------------------
CREATE TABLE pedido (
  id                     INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  cliente_id             INT UNSIGNED  NOT NULL,
  vendedor_id            INT UNSIGNED  NOT NULL,
  data_pedido            DATE          NOT NULL,
  data_prevista_entrega  DATE          NOT NULL,
  status                 ENUM('PENDENTE','FATURADO','ENTREGUE','CANCELADO')
                                       NOT NULL DEFAULT 'PENDENTE',
  valor_total            DECIMAL(14,2) NOT NULL DEFAULT 0,
  observacao             VARCHAR(500)  NULL,
  numero_nf              VARCHAR(20)   NULL,
  data_faturamento       DATE          NULL,
  data_entrega           DATE          NULL,
  CONSTRAINT pk_pedido PRIMARY KEY (id),
  CONSTRAINT fk_pedido_cliente  FOREIGN KEY (cliente_id)
    REFERENCES cliente (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT fk_pedido_vendedor FOREIGN KEY (vendedor_id)
    REFERENCES usuario (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT uq_pedido_nf UNIQUE (numero_nf),
  CONSTRAINT ck_pedido_datas CHECK (data_prevista_entrega >= data_pedido)
) ENGINE=InnoDB;

CREATE INDEX ix_pedido_status_prev ON pedido (status, data_prevista_entrega);

-- ---------------------------------------------------------------------
-- Tabela: item_pedido  (produtos de cada pedido)
-- ---------------------------------------------------------------------
CREATE TABLE item_pedido (
  id              INT UNSIGNED  NOT NULL AUTO_INCREMENT,
  pedido_id       INT UNSIGNED  NOT NULL,
  produto_id      INT UNSIGNED  NOT NULL,
  quantidade      DECIMAL(12,3) NOT NULL,
  preco_unitario  DECIMAL(12,2) NOT NULL,   -- preço "congelado" na venda
  subtotal        DECIMAL(14,2) NOT NULL,
  CONSTRAINT pk_item_pedido PRIMARY KEY (id),
  CONSTRAINT fk_item_pedido  FOREIGN KEY (pedido_id)
    REFERENCES pedido (id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_item_produto FOREIGN KEY (produto_id)
    REFERENCES produto (id) ON UPDATE CASCADE ON DELETE RESTRICT,
  CONSTRAINT ck_item_qtd CHECK (quantidade > 0)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Tabela: historico_status  (rastreabilidade de cada mudança de status)
-- ---------------------------------------------------------------------
CREATE TABLE historico_status (
  id               INT UNSIGNED NOT NULL AUTO_INCREMENT,
  pedido_id        INT UNSIGNED NOT NULL,
  usuario_id       INT UNSIGNED NOT NULL,
  status_anterior  VARCHAR(20)  NULL,
  status_novo      VARCHAR(20)  NOT NULL,
  data_hora        DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  observacao       VARCHAR(255) NULL,
  CONSTRAINT pk_historico PRIMARY KEY (id),
  CONSTRAINT fk_hist_pedido  FOREIGN KEY (pedido_id)
    REFERENCES pedido (id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT fk_hist_usuario FOREIGN KEY (usuario_id)
    REFERENCES usuario (id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- Visão: pedidos atrasados (usada no painel)
-- Atrasado = ainda não entregue/cancelado e data prevista já passou
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW vw_pedidos_atrasados AS
SELECT p.id,
       c.nome            AS cliente,
       p.data_prevista_entrega,
       p.status,
       p.valor_total,
       DATEDIFF(CURDATE(), p.data_prevista_entrega) AS dias_atraso
  FROM pedido p
  JOIN cliente c ON c.id = p.cliente_id
 WHERE p.status IN ('PENDENTE','FATURADO')
   AND p.data_prevista_entrega < CURDATE();

-- ---------------------------------------------------------------------
-- Dados iniciais
-- ---------------------------------------------------------------------
INSERT INTO categoria (nome) VALUES ('Sementes'), ('Defensivos'), ('Fertilizantes');
