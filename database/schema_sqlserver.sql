-- Esquema de base de datos SQL Server optimizado para velocidad
-- Con índices y optimizaciones para consultas rápidas

-- Crear base de datos si no existe (ejecutar en master primero)
-- CREATE DATABASE vehicles_db;
-- GO
-- USE vehicles_db;
-- GO

-- Tabla de vehículos
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[vehicles]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[vehicles] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [plate_number] VARCHAR(20) NOT NULL UNIQUE,
        [owner_name] NVARCHAR(255) NOT NULL,
        [owner_id] VARCHAR(50) NULL,
        [vehicle_make] VARCHAR(100) NULL,
        [vehicle_model] VARCHAR(100) NULL,
        [vehicle_year] INT NULL,
        [vehicle_color] VARCHAR(50) NULL,
        [registration_date] DATE NULL,
        [created_at] DATETIME2 DEFAULT GETDATE(),
        [updated_at] DATETIME2 DEFAULT GETDATE()
    );
END
GO

-- Tabla de detecciones
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[detections]') AND type in (N'U'))
BEGIN
    CREATE TABLE [dbo].[detections] (
        [id] INT IDENTITY(1,1) PRIMARY KEY,
        [plate_number] VARCHAR(20) NOT NULL,
        [vehicle_id] INT NULL,
        [detection_timestamp] DATETIME2 DEFAULT GETDATE(),
        [image_path] NVARCHAR(MAX) NULL,
        [confidence_score] FLOAT NULL,
        [location] VARCHAR(255) NULL,
        FOREIGN KEY ([vehicle_id]) REFERENCES [dbo].[vehicles]([id]) ON DELETE SET NULL
    );
END
GO

-- ÍNDICES OPTIMIZADOS PARA VELOCIDAD
-- Índice único en plate_number (ya incluido en UNIQUE, pero explícito para búsquedas)
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vehicles_plate_number' AND object_id = OBJECT_ID('dbo.vehicles'))
BEGIN
    CREATE INDEX idx_vehicles_plate_number ON [dbo].[vehicles]([plate_number]);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_vehicles_created_at' AND object_id = OBJECT_ID('dbo.vehicles'))
BEGIN
    CREATE INDEX idx_vehicles_created_at ON [dbo].[vehicles]([created_at] DESC);
END
GO

-- Índices para detecciones
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detections_plate_number' AND object_id = OBJECT_ID('dbo.detections'))
BEGIN
    CREATE INDEX idx_detections_plate_number ON [dbo].[detections]([plate_number]);
END
GO

-- Nota: Índices con funciones no son soportados directamente en SQL Server
-- Se usa la columna computada plate_normalized en su lugar
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detections_vehicle_id' AND object_id = OBJECT_ID('dbo.detections'))
BEGIN
    CREATE INDEX idx_detections_vehicle_id ON [dbo].[detections]([vehicle_id]);
END
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detections_timestamp' AND object_id = OBJECT_ID('dbo.detections'))
BEGIN
    CREATE INDEX idx_detections_timestamp ON [dbo].[detections]([detection_timestamp] DESC);
END
GO

-- Índice compuesto para búsquedas frecuentes
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_detections_plate_timestamp' AND object_id = OBJECT_ID('dbo.detections'))
BEGIN
    CREATE INDEX idx_detections_plate_timestamp ON [dbo].[detections]([plate_number], [detection_timestamp] DESC);
END
GO

-- Trigger para actualizar updated_at automáticamente
IF EXISTS (SELECT * FROM sys.triggers WHERE name = 'update_vehicles_updated_at')
BEGIN
    DROP TRIGGER update_vehicles_updated_at;
END
GO

CREATE TRIGGER update_vehicles_updated_at
ON [dbo].[vehicles]
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;
    UPDATE [dbo].[vehicles]
    SET [updated_at] = GETDATE()
    FROM [dbo].[vehicles] v
    INNER JOIN inserted i ON v.id = i.id;
END
GO

-- Función para búsqueda rápida de matrícula (normalizada)
IF EXISTS (SELECT * FROM sys.objects WHERE name = 'normalize_plate' AND type = 'FN')
BEGIN
    DROP FUNCTION normalize_plate;
END
GO

CREATE FUNCTION normalize_plate(@plate VARCHAR(20))
RETURNS VARCHAR(20)
AS
BEGIN
    DECLARE @result VARCHAR(20);
    SET @result = UPPER(REPLACE(REPLACE(REPLACE(REPLACE(@plate, ' ', ''), '-', ''), '_', ''), '.', ''));
    RETURN @result;
END
GO

-- Índice funcional no disponible en SQL Server, pero podemos crear un índice computado
-- Alternativa: usar computed column
IF NOT EXISTS (SELECT * FROM sys.columns WHERE name = 'plate_normalized' AND object_id = OBJECT_ID('dbo.vehicles'))
BEGIN
    ALTER TABLE [dbo].[vehicles]
    ADD plate_normalized AS UPPER(REPLACE(REPLACE(REPLACE(REPLACE([plate_number], ' ', ''), '-', ''), '_', ''), '.', '')) PERSISTED;
    
    CREATE INDEX idx_vehicles_plate_normalized ON [dbo].[vehicles]([plate_normalized]);
END
GO

