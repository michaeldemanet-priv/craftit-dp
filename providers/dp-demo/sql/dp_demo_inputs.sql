-- Source rows for the dp-demo provider.
-- Local database: dummydb on localhost\MSSQLSERVERCRAFT (Windows authentication).

IF OBJECT_ID(N'dbo.DpDemoInputs', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DpDemoInputs (
        record_id nvarchar(64) NOT NULL CONSTRAINT PK_DpDemoInputs PRIMARY KEY,
        input_1 decimal(18, 6) NOT NULL,
        input_2 decimal(18, 6) NOT NULL
    );
END;

IF NOT EXISTS (SELECT 1 FROM dbo.DpDemoInputs)
BEGIN
    INSERT INTO dbo.DpDemoInputs (record_id, input_1, input_2) VALUES
        (N'row-0', 1, 0),
        (N'row-1', 2, 10),
        (N'row-2', 3, 20),
        (N'row-3', 4, 30),
        (N'row-4', 5, 40),
        (N'row-5', 6, 50),
        (N'row-6', 7, 60),
        (N'row-7', 8, 70),
        (N'row-8', 9, 80),
        (N'row-9', 10, 90);
END;
