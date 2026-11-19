USE gedenaz;

CREATE TABLE IF NOT EXISTS plan_pago (
    id                 INT AUTO_INCREMENT PRIMARY KEY,
    venta_id           INT NOT NULL UNIQUE,
    cantidad_cuotas    INT NOT NULL,
    frecuencia         VARCHAR(20) NOT NULL,
    monto_total        DECIMAL(12,2) NOT NULL,
    primer_vencimiento DATE NOT NULL,
    fecha_creacion     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_pago_venta FOREIGN KEY (venta_id) REFERENCES venta (id),
    CONSTRAINT chk_plan_cuotas CHECK (cantidad_cuotas BETWEEN 2 AND 120),
    CONSTRAINT chk_plan_total CHECK (monto_total > 0)
);

CREATE TABLE IF NOT EXISTS cuota (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    plan_pago_id      INT NOT NULL,
    numero            INT NOT NULL,
    monto             DECIMAL(12,2) NOT NULL,
    fecha_vencimiento DATE NOT NULL,
    CONSTRAINT fk_cuota_plan FOREIGN KEY (plan_pago_id) REFERENCES plan_pago (id),
    CONSTRAINT uq_cuota_plan_numero UNIQUE (plan_pago_id, numero),
    CONSTRAINT chk_cuota_numero CHECK (numero > 0),
    CONSTRAINT chk_cuota_monto CHECK (monto > 0)
);

CREATE TABLE IF NOT EXISTS abono (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    cuota_id   INT NOT NULL,
    monto      DECIMAL(12,2) NOT NULL,
    fecha_pago DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_abono_cuota FOREIGN KEY (cuota_id) REFERENCES cuota (id),
    CONSTRAINT chk_abono_monto CHECK (monto > 0)
);
