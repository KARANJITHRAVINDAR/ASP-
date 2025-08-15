# database_setup.py
import mysql.connector
from mysql.connector import errorcode

DB_NAME = 'hospital_ai_dashboard'
TABLES = {}

TABLES['predictions'] = (
    "CREATE TABLE `predictions` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "  `patientId` varchar(50) DEFAULT NULL,"
    "  `patientName` varchar(255) DEFAULT NULL,"
    "  `admissionDate` date DEFAULT NULL,"
    "  `age` int(11) DEFAULT NULL,"
    "  `admissionType` int(11) DEFAULT NULL,"
    "  `priorAdmissions` int(11) DEFAULT NULL,"
    "  `surgeryMethod` int(11) DEFAULT NULL,"
    "  `albumin` float DEFAULT NULL,"
    "  `hemoglobin` float DEFAULT NULL,"
    "  `hasSepsis` tinyint(1) DEFAULT '0',"
    "  `hasDelirium` tinyint(1) DEFAULT '0',"
    "  `hasMalignancy` tinyint(1) DEFAULT '0',"
    "  `hasDiabetes` tinyint(1) DEFAULT '0',"
    "  `hasCHF` tinyint(1) DEFAULT '0',"
    "  `hasCKD` tinyint(1) DEFAULT '0',"
    "  `hasCOPD` tinyint(1) DEFAULT '0',"
    "  `hasStroke` tinyint(1) DEFAULT '0',"
    "  `hasLiverDisease` tinyint(1) DEFAULT '0',"
    "  `predicted_los` int(11) DEFAULT NULL,"
    "  `riskScore` int(11) DEFAULT NULL,"
    "  `riskLevel` varchar(50) DEFAULT NULL,"
    "  PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB")

TABLES['feedback'] = (
    "CREATE TABLE `feedback` ("
    "  `id` int(11) NOT NULL AUTO_INCREMENT,"
    "  `patient_id` varchar(255) NOT NULL,"
    "  `feedback_text` text,"
    "  `sentiment_score` float DEFAULT NULL,"
    "  `sentiment_label` varchar(50) DEFAULT NULL,"
    "  `category` varchar(100) DEFAULT NULL,"
    "  `timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,"
    "  PRIMARY KEY (`id`)"
    ") ENGINE=InnoDB")

# --- Database Connection Details ---
# It's recommended to use environment variables for production.
config = {
    'user': 'root',
    'password': 'Ks@kbd23777', # The password you provided
    'host': '127.0.0.1'
}

try:
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET 'utf8'")
    print(f"Database '{DB_NAME}' created or already exists.")
    conn.database = DB_NAME
except mysql.connector.Error as err:
    print(f"Failed creating database: {err}")
    exit(1)

for table_name in TABLES:
    table_description = TABLES[table_name]
    try:
        print(f"Creating table {table_name}: ", end='')
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};") # Drop if exists for a clean setup
        cursor.execute(table_description)
        print("OK")
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
            print("already exists.")
        else:
            print(err.msg)

cursor.close()
conn.close()
print("Database setup complete.")