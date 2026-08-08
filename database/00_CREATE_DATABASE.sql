IF DB_ID('ecoMonitoringDB') IS NULL
BEGIN
    CREATE DATABASE ecoMonitoringDB;
END
GO