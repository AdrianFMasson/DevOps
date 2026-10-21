-- Sistema de Estacionamento
-- Requisitos: MySQL 8.0.16+ (CHECK efetivamente aplicado) ou MySQL 8.4.
-- Execute este arquivo com um usuário autorizado a criar banco, tabelas e triggers.
-- Em produção, prefira aplicar migrações com um usuário administrativo separado
-- e conceder ao usuário da aplicação somente as permissões necessárias.
CREATE TABLE IF NOT EXISTS users (
  id_usuario BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL,
  senha_hash VARCHAR(255) NOT NULL,
  perfil ENUM('ADMINISTRADOR','OPERADOR') NOT NULL DEFAULT 'OPERADOR',
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_usuario),
  CONSTRAINT uq_users_email UNIQUE (email),
  CONSTRAINT chk_users_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0),
  CONSTRAINT chk_users_email CHECK (email LIKE '%_@_%._%')
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS clients (
  id_clients BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome_completo VARCHAR(150) NOT NULL,
  documento VARCHAR(14) NULL,
  email VARCHAR(254) NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_clients),
  CONSTRAINT uq_clients_documento UNIQUE (documento),
  CONSTRAINT chk_clients_nome CHECK (CHAR_LENGTH(TRIM(nome_completo)) > 0),
  CONSTRAINT chk_clients_email CHECK (email IS NULL OR email LIKE '%_@_%._%')
) ENGINE=InnoDB;


CREATE TABLE IF NOT EXISTS telefones_clients (
  id_telefone BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_clients BIGINT UNSIGNED NOT NULL,
  numero VARCHAR(20) NOT NULL,
  tipo ENUM('CELULAR','FIXO','RECADO') NOT NULL DEFAULT 'CELULAR',
  nome_contato VARCHAR(120) NULL,
  principal BOOLEAN NOT NULL DEFAULT FALSE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  telefone_principal_clients BIGINT UNSIGNED
    GENERATED ALWAYS AS (
      CASE WHEN principal = TRUE THEN id_clients ELSE NULL END
    ) STORED,
  PRIMARY KEY (id_telefone),
  UNIQUE KEY uq_telefone_principal_clients (telefone_principal_clients),
  KEY ix_telefones_clients (id_clients),
  CONSTRAINT fk_telefones_clients_clients
    FOREIGN KEY (id_clients)
    REFERENCES clients(id_clients)
    ON UPDATE RESTRICT
    ON DELETE RESTRICT,
  CONSTRAINT chk_telefone_numero
    CHECK (CHAR_LENGTH(TRIM(numero)) >= 8)
) ENGINE=InnoDB;



CREATE TABLE IF NOT EXISTS marcas_veiculo (
  id_marca BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(80) NOT NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_marca),
  CONSTRAINT uq_marcas_veiculo_nome UNIQUE (nome),
  CONSTRAINT chk_marca_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS modelos_veiculo (
  id_modelo BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_marca BIGINT UNSIGNED NOT NULL,
  nome VARCHAR(100) NOT NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_modelo),
  UNIQUE KEY uq_modelo_marca_nome (id_marca, nome),
  KEY ix_modelos_marca (id_marca),
  CONSTRAINT fk_modelos_marca FOREIGN KEY (id_marca)
    REFERENCES marcas_veiculo(id_marca) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_modelo_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS veiculos (
  id_veiculo BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_clients BIGINT UNSIGNED NOT NULL,
  id_modelo BIGINT UNSIGNED NOT NULL,
  placa VARCHAR(7) NOT NULL,
  cor ENUM('PRETO','BRANCO','PRATA','CINZA','VERMELHO','AZUL','VERDE','AMARELO','MARROM','BEGE','DOURADO','OUTRA') NOT NULL DEFAULT 'OUTRA',
  ano_modelo SMALLINT UNSIGNED NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_veiculo),
  CONSTRAINT uq_veiculos_placa UNIQUE (placa),
  KEY ix_veiculos_clients (id_clients),
  KEY ix_veiculos_modelo (id_modelo),
  CONSTRAINT fk_veiculos_clients FOREIGN KEY (id_clients)
    REFERENCES clients(id_clients) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_veiculos_modelo FOREIGN KEY (id_modelo)
    REFERENCES modelos_veiculo(id_modelo) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_veiculo_ano CHECK (ano_modelo IS NULL OR ano_modelo BETWEEN 1950 AND 2155),
  CONSTRAINT chk_veiculo_placa CHECK (placa REGEXP '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$')
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vagas (
  id_vaga BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(20) NOT NULL,
  tipo ENUM('MENSALISTA','ROTATIVA') NOT NULL,
  status ENUM('ATIVA','BLOQUEADA','INATIVA') NOT NULL DEFAULT 'ATIVA',
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  dt_atualizacao DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_vaga),
  CONSTRAINT uq_vagas_codigo UNIQUE (codigo),
  CONSTRAINT chk_vaga_codigo CHECK (CHAR_LENGTH(TRIM(codigo)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS vagas_mensalistas (
  id_vinculo BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_clients BIGINT UNSIGNED NOT NULL,
  id_vaga BIGINT UNSIGNED NOT NULL,
  data_inicio DATE NOT NULL,
  data_fim DATE NULL,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  vaga_atual_id BIGINT UNSIGNED
    GENERATED ALWAYS AS (CASE WHEN data_fim IS NULL THEN id_vaga ELSE NULL END) STORED,
  PRIMARY KEY (id_vinculo),
  UNIQUE KEY uq_vaga_mensalista_atual (vaga_atual_id),
  KEY ix_vinculos_clients (id_clients, data_fim),
  KEY ix_vinculos_vaga (id_vaga, data_fim),
  CONSTRAINT fk_vinculo_clients FOREIGN KEY (id_clients)
    REFERENCES clients(id_clients) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_vinculo_vaga FOREIGN KEY (id_vaga)
    REFERENCES vagas(id_vaga) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_vinculo_datas CHECK (data_fim IS NULL OR data_fim >= data_inicio)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS tarifas (
  id_tarifa BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  nome VARCHAR(100) NOT NULL,
  valor_hora DECIMAL(10,2) NOT NULL,
  minutos_tolerancia SMALLINT UNSIGNED NOT NULL DEFAULT 0,
  minutos_fracao SMALLINT UNSIGNED NOT NULL DEFAULT 60,
  valor_fracao DECIMAL(10,2) NOT NULL,
  inicio_vigencia DATETIME(6) NOT NULL,
  fim_vigencia DATETIME(6) NULL,
  ativo BOOLEAN NOT NULL DEFAULT TRUE,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_tarifa),
  KEY ix_tarifas_vigencia (inicio_vigencia, fim_vigencia, ativo),
  CONSTRAINT chk_tarifa_valor_hora CHECK (valor_hora >= 0),
  CONSTRAINT chk_tarifa_valor_fracao CHECK (valor_fracao >= 0),
  CONSTRAINT chk_tarifa_fracao CHECK (minutos_fracao > 0),
  CONSTRAINT chk_tarifa_vigencia CHECK (fim_vigencia IS NULL OR fim_vigencia > inicio_vigencia),
  CONSTRAINT chk_tarifa_nome CHECK (CHAR_LENGTH(TRIM(nome)) > 0)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS movimentacoes (
  id_movimentacao BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_veiculo BIGINT UNSIGNED NOT NULL,
  id_vaga BIGINT UNSIGNED NOT NULL,
  id_usuario_entrada BIGINT UNSIGNED NOT NULL,
  id_usuario_saida BIGINT UNSIGNED NULL,
  modalidade ENUM('MENSALISTA','HORISTA') NOT NULL,
  data_hora_entrada DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  data_hora_saida DATETIME(6) NULL,
  id_tarifa BIGINT UNSIGNED NULL,
  valor_total DECIMAL(10,2) NULL,
  vaga_aberta_id BIGINT UNSIGNED
    GENERATED ALWAYS AS (CASE WHEN data_hora_saida IS NULL THEN id_vaga ELSE NULL END) STORED,
  veiculo_aberto_id BIGINT UNSIGNED
    GENERATED ALWAYS AS (CASE WHEN data_hora_saida IS NULL THEN id_veiculo ELSE NULL END) STORED,
  dt_cadastro DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  PRIMARY KEY (id_movimentacao),
  UNIQUE KEY uq_movimentacao_vaga_aberta (vaga_aberta_id),
  UNIQUE KEY uq_movimentacao_veiculo_aberto (veiculo_aberto_id),
  KEY ix_movimentacoes_entrada (data_hora_entrada),
  KEY ix_movimentacoes_veiculo (id_veiculo, data_hora_entrada),
  KEY ix_movimentacoes_vaga (id_vaga, data_hora_entrada),
  CONSTRAINT fk_mov_veiculo FOREIGN KEY (id_veiculo)
    REFERENCES veiculos(id_veiculo) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_mov_vaga FOREIGN KEY (id_vaga)
    REFERENCES vagas(id_vaga) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_mov_usuario_entrada FOREIGN KEY (id_usuario_entrada)
    REFERENCES users(id_usuario) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_mov_usuario_saida FOREIGN KEY (id_usuario_saida)
    REFERENCES users(id_usuario) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT fk_mov_tarifa FOREIGN KEY (id_tarifa)
    REFERENCES tarifas(id_tarifa) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT chk_mov_datas CHECK (data_hora_saida IS NULL OR data_hora_saida >= data_hora_entrada),
  CONSTRAINT chk_mov_valor CHECK (valor_total IS NULL OR valor_total >= 0),
  CONSTRAINT chk_mov_modalidade_tarifa CHECK (
    (modalidade = 'HORISTA' AND id_tarifa IS NOT NULL)
    OR (modalidade = 'MENSALISTA' AND id_tarifa IS NULL)
  ),
  CONSTRAINT chk_mov_valor_saida CHECK (
    (data_hora_saida IS NULL AND valor_total IS NULL AND id_usuario_saida IS NULL)
    OR (data_hora_saida IS NOT NULL AND id_usuario_saida IS NOT NULL)
  )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS auditoria (
  id_auditoria BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  id_usuario BIGINT UNSIGNED NULL,
  entidade VARCHAR(60) NOT NULL,
  id_registro VARCHAR(64) NOT NULL,
  acao ENUM('CRIACAO','ALTERACAO','DESATIVACAO','EXCLUSAO') NOT NULL,
  resultado ENUM('SUCESSO','FALHA') NOT NULL DEFAULT 'SUCESSO',
  data_hora DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
  origem VARCHAR(45) NULL,
  identificador_requisicao VARCHAR(64) NULL,
  detalhes JSON NULL,
  PRIMARY KEY (id_auditoria),
  KEY ix_auditoria_usuario_data (id_usuario, data_hora),
  KEY ix_auditoria_entidade_registro (entidade, id_registro, data_hora),
  CONSTRAINT fk_auditoria_usuario FOREIGN KEY (id_usuario)
    REFERENCES users(id_usuario) ON UPDATE RESTRICT ON DELETE SET NULL
) ENGINE=InnoDB;

-- TRIGGERS DE INTEGRIDADE
DELIMITER $$

CREATE TRIGGER bi_veiculos_normalizar_validar
BEFORE INSERT ON veiculos
FOR EACH ROW
BEGIN
  SET NEW.placa = UPPER(REPLACE(REPLACE(TRIM(NEW.placa), '-', ''), ' ', ''));
  IF NEW.placa NOT REGEXP '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Placa inválida. Informe placa no padrão antigo ou Mercosul, sem espaços.';
  END IF;
END$$

CREATE TRIGGER bu_veiculos_normalizar_validar
BEFORE UPDATE ON veiculos
FOR EACH ROW
BEGIN
  SET NEW.placa = UPPER(REPLACE(REPLACE(TRIM(NEW.placa), '-', ''), ' ', ''));
  IF NEW.placa NOT REGEXP '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Placa inválida. Informe placa no padrão antigo ou Mercosul, sem espaços.';
  END IF;
END$$

CREATE TRIGGER bi_vinculo_mensalista_validar
BEFORE INSERT ON vagas_mensalistas
FOR EACH ROW
BEGIN
  DECLARE v_tipo VARCHAR(20);
  SELECT tipo INTO v_tipo FROM vagas WHERE id_vaga = NEW.id_vaga;
  IF v_tipo <> 'MENSALISTA' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Somente vagas do tipo MENSALISTA podem ser vinculadas a clients.';
  END IF;
END$$

CREATE TRIGGER bu_vinculo_mensalista_validar
BEFORE UPDATE ON vagas_mensalistas
FOR EACH ROW
BEGIN
  DECLARE v_tipo VARCHAR(20);
  SELECT tipo INTO v_tipo FROM vagas WHERE id_vaga = NEW.id_vaga;
  IF v_tipo <> 'MENSALISTA' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Somente vagas do tipo MENSALISTA podem ser vinculadas a clients.';
  END IF;
END$$

CREATE TRIGGER bi_movimentacao_validar
BEFORE INSERT ON movimentacoes
FOR EACH ROW
BEGIN
  DECLARE v_tipo_vaga VARCHAR(20);
  DECLARE v_status_vaga VARCHAR(20);
  DECLARE v_clients_veiculo BIGINT UNSIGNED;
  DECLARE v_vinculo BIGINT UNSIGNED DEFAULT NULL;
  SELECT tipo, status INTO v_tipo_vaga, v_status_vaga
    FROM vagas WHERE id_vaga = NEW.id_vaga;
  SELECT id_clients INTO v_clients_veiculo
    FROM veiculos WHERE id_veiculo = NEW.id_veiculo;
  IF v_status_vaga <> 'ATIVA' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Não é permitido iniciar movimentação em vaga bloqueada ou inativa.';
  END IF;
  IF NEW.modalidade = 'HORISTA' AND v_tipo_vaga <> 'ROTATIVA' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Horistas só podem utilizar vagas rotativas.';
  END IF;
  IF NEW.modalidade = 'MENSALISTA' THEN
    IF v_tipo_vaga <> 'MENSALISTA' THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mensalistas devem utilizar vaga mensalista vinculada.';
    END IF;
    SELECT id_vinculo INTO v_vinculo FROM vagas_mensalistas
      WHERE id_vaga = NEW.id_vaga
        AND id_clients = v_clients_veiculo
        AND data_fim IS NULL
      LIMIT 1;
    IF v_vinculo IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'O clients proprietário do veículo não possui vínculo ativo com esta vaga mensalista.';
    END IF;
  END IF;
  IF NEW.modalidade = 'HORISTA' AND NEW.id_tarifa IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Movimentação horista exige tarifa.';
  END IF;
END$$

CREATE TRIGGER bu_movimentacao_validar
BEFORE UPDATE ON movimentacoes
FOR EACH ROW
BEGIN
  DECLARE v_tipo_vaga VARCHAR(20);
  DECLARE v_status_vaga VARCHAR(20);
  DECLARE v_clients_veiculo BIGINT UNSIGNED;
  DECLARE v_vinculo BIGINT UNSIGNED DEFAULT NULL;
  IF OLD.data_hora_saida IS NOT NULL AND NEW.data_hora_saida IS NULL THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Movimentação encerrada não pode ser reaberta.';
  END IF;
  IF OLD.data_hora_saida IS NULL AND NEW.data_hora_saida IS NOT NULL THEN
    IF NEW.id_usuario_saida IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Informe o usuário responsável pela saída.';
    END IF;
    IF NEW.modalidade = 'HORISTA' AND (NEW.valor_total IS NULL OR NEW.valor_total < 0) THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Saída horista exige valor total calculado.';
    END IF;
  END IF;
  SELECT tipo, status INTO v_tipo_vaga, v_status_vaga
    FROM vagas WHERE id_vaga = NEW.id_vaga;
  SELECT id_clients INTO v_clients_veiculo
    FROM veiculos WHERE id_veiculo = NEW.id_veiculo;
  IF NEW.modalidade = 'HORISTA' AND v_tipo_vaga <> 'ROTATIVA' THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Horistas só podem utilizar vagas rotativas.';
  END IF;
  IF NEW.modalidade = 'MENSALISTA' THEN
    IF v_tipo_vaga <> 'MENSALISTA' THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Mensalistas devem utilizar vaga mensalista vinculada.';
    END IF;
    SELECT id_vinculo INTO v_vinculo FROM vagas_mensalistas
      WHERE id_vaga = NEW.id_vaga
        AND id_clients = v_clients_veiculo
        AND data_fim IS NULL
      LIMIT 1;
    IF v_vinculo IS NULL THEN
      SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'O clients proprietário do veículo não possui vínculo ativo com esta vaga mensalista.';
    END IF;
  END IF;
END$$

DELIMITER ;

-- TRIGGERS DE AUDITORIA
-- O backend deverá definir, na mesma conexão/transação:
-- SET @id_usuario_auditoria = <id do usuário autenticado>;
-- SET @origem_auditoria = <IP ou origem técnica>;
-- SET @identificador_requisicao = <id de correlação>;
-- Não grave senhas, hashes, tokens ou segredos nos detalhes da auditoria.

DELIMITER $$

CREATE TRIGGER aiud_auditoria_users_insert
AFTER INSERT ON users
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'users', CAST(NEW.id_usuario AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('nome', 'email', 'perfil', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_users_update
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'users', CAST(NEW.id_usuario AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('nome', 'email', 'perfil', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_users_delete
AFTER DELETE ON users
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'users', CAST(OLD.id_usuario AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('nome', 'email', 'perfil', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_clients_insert
AFTER INSERT ON clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'clients', CAST(NEW.id_clients AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('nome_completo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_clients_update
AFTER UPDATE ON clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'clients', CAST(NEW.id_clients AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('nome_completo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_clients_delete
AFTER DELETE ON clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'clients', CAST(OLD.id_clients AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('nome_completo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_telefones_clients_insert
AFTER INSERT ON telefones_clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'telefones_clients', CAST(NEW.id_telefone AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('id_clients', 'tipo', 'principal')));
END$$

CREATE TRIGGER aiud_auditoria_telefones_clients_update
AFTER UPDATE ON telefones_clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'telefones_clients', CAST(NEW.id_telefone AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('id_clients', 'tipo', 'principal')));
END$$

CREATE TRIGGER aiud_auditoria_telefones_clients_delete
AFTER DELETE ON telefones_clients
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'telefones_clients', CAST(OLD.id_telefone AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('id_clients', 'tipo', 'principal')));
END$$

CREATE TRIGGER aiud_auditoria_marcas_veiculo_insert
AFTER INSERT ON marcas_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'marcas_veiculo', CAST(NEW.id_marca AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_marcas_veiculo_update
AFTER UPDATE ON marcas_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'marcas_veiculo', CAST(NEW.id_marca AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_marcas_veiculo_delete
AFTER DELETE ON marcas_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'marcas_veiculo', CAST(OLD.id_marca AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_modelos_veiculo_insert
AFTER INSERT ON modelos_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'modelos_veiculo', CAST(NEW.id_modelo AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('id_marca', 'nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_modelos_veiculo_update
AFTER UPDATE ON modelos_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'modelos_veiculo', CAST(NEW.id_modelo AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('id_marca', 'nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_modelos_veiculo_delete
AFTER DELETE ON modelos_veiculo
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'modelos_veiculo', CAST(OLD.id_modelo AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('id_marca', 'nome', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_veiculos_insert
AFTER INSERT ON veiculos
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'veiculos', CAST(NEW.id_veiculo AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_modelo', 'placa', 'cor', 'ano_modelo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_veiculos_update
AFTER UPDATE ON veiculos
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'veiculos', CAST(NEW.id_veiculo AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_modelo', 'placa', 'cor', 'ano_modelo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_veiculos_delete
AFTER DELETE ON veiculos
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'veiculos', CAST(OLD.id_veiculo AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_modelo', 'placa', 'cor', 'ano_modelo', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_insert
AFTER INSERT ON vagas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas', CAST(NEW.id_vaga AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('codigo', 'tipo', 'status')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_update
AFTER UPDATE ON vagas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas', CAST(NEW.id_vaga AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('codigo', 'tipo', 'status')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_delete
AFTER DELETE ON vagas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas', CAST(OLD.id_vaga AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('codigo', 'tipo', 'status')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_mensalistas_insert
AFTER INSERT ON vagas_mensalistas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas_mensalistas', CAST(NEW.id_vinculo AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_vaga', 'data_inicio', 'data_fim')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_mensalistas_update
AFTER UPDATE ON vagas_mensalistas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas_mensalistas', CAST(NEW.id_vinculo AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_vaga', 'data_inicio', 'data_fim')));
END$$

CREATE TRIGGER aiud_auditoria_vagas_mensalistas_delete
AFTER DELETE ON vagas_mensalistas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'vagas_mensalistas', CAST(OLD.id_vinculo AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('id_clients', 'id_vaga', 'data_inicio', 'data_fim')));
END$$

CREATE TRIGGER aiud_auditoria_tarifas_insert
AFTER INSERT ON tarifas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'tarifas', CAST(NEW.id_tarifa AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('nome', 'valor_hora', 'minutos_tolerancia', 'minutos_fracao', 'valor_fracao', 'inicio_vigencia', 'fim_vigencia', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_tarifas_update
AFTER UPDATE ON tarifas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'tarifas', CAST(NEW.id_tarifa AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('nome', 'valor_hora', 'minutos_tolerancia', 'minutos_fracao', 'valor_fracao', 'inicio_vigencia', 'fim_vigencia', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_tarifas_delete
AFTER DELETE ON tarifas
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'tarifas', CAST(OLD.id_tarifa AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('nome', 'valor_hora', 'minutos_tolerancia', 'minutos_fracao', 'valor_fracao', 'inicio_vigencia', 'fim_vigencia', 'ativo')));
END$$

CREATE TRIGGER aiud_auditoria_movimentacoes_insert
AFTER INSERT ON movimentacoes
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'movimentacoes', CAST(NEW.id_movimentacao AS CHAR), 'CRIACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'INSERT', 'campos_relevantes', JSON_ARRAY('id_veiculo', 'id_vaga', 'modalidade', 'data_hora_entrada', 'data_hora_saida', 'id_tarifa', 'valor_total')));
END$$

CREATE TRIGGER aiud_auditoria_movimentacoes_update
AFTER UPDATE ON movimentacoes
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'movimentacoes', CAST(NEW.id_movimentacao AS CHAR), 'ALTERACAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'UPDATE', 'campos_relevantes', JSON_ARRAY('id_veiculo', 'id_vaga', 'modalidade', 'data_hora_entrada', 'data_hora_saida', 'id_tarifa', 'valor_total')));
END$$

CREATE TRIGGER aiud_auditoria_movimentacoes_delete
AFTER DELETE ON movimentacoes
FOR EACH ROW
BEGIN
  INSERT INTO auditoria
    (id_usuario, entidade, id_registro, acao, resultado, origem, identificador_requisicao, detalhes)
  VALUES
    (NULLIF(@id_usuario_auditoria, 0), 'movimentacoes', CAST(OLD.id_movimentacao AS CHAR), 'EXCLUSAO', 'SUCESSO',
     LEFT(@origem_auditoria, 45), LEFT(@identificador_requisicao, 64),
     JSON_OBJECT('operacao', 'DELETE', 'campos_relevantes', JSON_ARRAY('id_veiculo', 'id_vaga', 'modalidade', 'data_hora_entrada', 'data_hora_saida', 'id_tarifa', 'valor_total')));
END$$

DELIMITER ;

-- NOTAS DE INTEGRIDADE:
-- 1) Os índices únicos gerados impedem duas movimentações abertas para a mesma vaga
--    e duas movimentações abertas para o mesmo veículo.
-- 2) Uma vaga mensalista só pode ter um vínculo vigente, via uq_vaga_mensalista_atual.
-- 3) A auditoria registra nomes de campos, não valores pessoais antes/depois.
-- 4) As triggers não substituem autenticação/autorização no FastAPI.
-- 5) Para garantir autoria, o backend deve definir as variáveis de sessão acima na mesma
--    conexão usada pela transação. Acesso SQL direto deve ser restrito e auditado.
-- 6) Não apagar usuários/clients/veículos com histórico; desativar quando aplicável.
-- 7) A política exata de tarifa (arredondamento, tolerância, frações) ainda deve ser definida.



INSERT INTO users (nome, email, senha_hash, perfil, ativo)
VALUES (
    'Administrador Teste',
    'admin@estacionamento.com',
    '$argon2id$v=19$m=65536,t=3,p=4$ewDaiC5FGHJ2E7H8WDVdiA$TtTsWj6T1yEOHb/Yc5+AMR2U+lJPIYDFg7VDnIAo12k',
    'ADMINISTRADOR',
    1
);

INSERT INTO users (nome, email, senha_hash, perfil, ativo)
VALUES (
    'Operador Teste',
    'operador@estacionamento.com',
    '$argon2id$v=19$m=65536,t=3,p=4$pMyLdp2vi5NvMEeg7M1mXg$Ab+PlvxZGU+CV3xB1MOcM24MFl17oX89CWB0FEb0zjc',
    'OPERADOR',
    1
);
INSERT INTO marcas_veiculo (nome, ativo) VALUES
('Toyota', TRUE),
('Honda', TRUE),
('Volkswagen', TRUE),
('Chevrolet', TRUE),
('Fiat', TRUE),
('Ford', TRUE),
('Hyundai', TRUE),
('Nissan', TRUE),
('Renault', TRUE),
('Jeep', TRUE),
('BMW', TRUE),
('Mercedes-Benz', TRUE),
('Audi', TRUE),
('BYD', TRUE),
('Mitsubishi', TRUE);


INSERT INTO modelos_veiculo (id_marca, nome, ativo)
SELECT id_marca, 'Corolla', TRUE FROM marcas_veiculo WHERE nome = 'Toyota'
UNION ALL
SELECT id_marca, 'Hilux', TRUE FROM marcas_veiculo WHERE nome = 'Toyota'
UNION ALL
SELECT id_marca, 'Yaris', TRUE FROM marcas_veiculo WHERE nome = 'Toyota'
UNION ALL
SELECT id_marca, 'Civic', TRUE FROM marcas_veiculo WHERE nome = 'Honda'
UNION ALL
SELECT id_marca, 'City', TRUE FROM marcas_veiculo WHERE nome = 'Honda'
UNION ALL
SELECT id_marca, 'HR-V', TRUE FROM marcas_veiculo WHERE nome = 'Honda'
UNION ALL
SELECT id_marca, 'Polo', TRUE FROM marcas_veiculo WHERE nome = 'Volkswagen'
UNION ALL
SELECT id_marca, 'T-Cross', TRUE FROM marcas_veiculo WHERE nome = 'Volkswagen'
UNION ALL
SELECT id_marca, 'Nivus', TRUE FROM marcas_veiculo WHERE nome = 'Volkswagen'
UNION ALL
SELECT id_marca, 'Onix', TRUE FROM marcas_veiculo WHERE nome = 'Chevrolet'
UNION ALL
SELECT id_marca, 'Tracker', TRUE FROM marcas_veiculo WHERE nome = 'Chevrolet'
UNION ALL
SELECT id_marca, 'Montana', TRUE FROM marcas_veiculo WHERE nome = 'Chevrolet'
UNION ALL
SELECT id_marca, 'Argo', TRUE FROM marcas_veiculo WHERE nome = 'Fiat'
UNION ALL
SELECT id_marca, 'Cronos', TRUE FROM marcas_veiculo WHERE nome = 'Fiat'
UNION ALL
SELECT id_marca, 'Toro', TRUE FROM marcas_veiculo WHERE nome = 'Fiat'
UNION ALL
SELECT id_marca, 'Ranger', TRUE FROM marcas_veiculo WHERE nome = 'Ford'
UNION ALL
SELECT id_marca, 'Territory', TRUE FROM marcas_veiculo WHERE nome = 'Ford'
UNION ALL
SELECT id_marca, 'Bronco Sport', TRUE FROM marcas_veiculo WHERE nome = 'Ford'
UNION ALL
SELECT id_marca, 'HB20', TRUE FROM marcas_veiculo WHERE nome = 'Hyundai'
UNION ALL
SELECT id_marca, 'Creta', TRUE FROM marcas_veiculo WHERE nome = 'Hyundai'
UNION ALL
SELECT id_marca, 'Kicks', TRUE FROM marcas_veiculo WHERE nome = 'Nissan'
UNION ALL
SELECT id_marca, 'Versa', TRUE FROM marcas_veiculo WHERE nome = 'Nissan'
UNION ALL
SELECT id_marca, 'Kwid', TRUE FROM marcas_veiculo WHERE nome = 'Renault'
UNION ALL
SELECT id_marca, 'Duster', TRUE FROM marcas_veiculo WHERE nome = 'Renault'
UNION ALL
SELECT id_marca, 'Renegade', TRUE FROM marcas_veiculo WHERE nome = 'Jeep'
UNION ALL
SELECT id_marca, 'Compass', TRUE FROM marcas_veiculo WHERE nome = 'Jeep'
UNION ALL
SELECT id_marca, '320i', TRUE FROM marcas_veiculo WHERE nome = 'BMW'
UNION ALL
SELECT id_marca, 'X1', TRUE FROM marcas_veiculo WHERE nome = 'BMW'
UNION ALL
SELECT id_marca, 'C-Class', TRUE FROM marcas_veiculo WHERE nome = 'Mercedes-Benz'
UNION ALL
SELECT id_marca, 'GLA', TRUE FROM marcas_veiculo WHERE nome = 'Mercedes-Benz'
UNION ALL
SELECT id_marca, 'A3', TRUE FROM marcas_veiculo WHERE nome = 'Audi'
UNION ALL
SELECT id_marca, 'Q3', TRUE FROM marcas_veiculo WHERE nome = 'Audi'
UNION ALL
SELECT id_marca, 'Dolphin', TRUE FROM marcas_veiculo WHERE nome = 'BYD'
UNION ALL
SELECT id_marca, 'Song Plus', TRUE FROM marcas_veiculo WHERE nome = 'BYD'
UNION ALL
SELECT id_marca, 'L200 Triton', TRUE FROM marcas_veiculo WHERE nome = 'Mitsubishi';
SELECT id_usuario, nome, email,senha_hash, perfil, ativo
FROM users
WHERE email IN (
    'admin@estacionamento.com',
    'operador@estacionamento.com'
);

select * from veiculos;

SELECT VERSION();