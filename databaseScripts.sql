CREATE SCHEMA `attendancedb` ;

CREATE USER 'atsys'@'localhost' IDENTIFIED BY 'atsys';

GRANT ALL PRIVILEGES ON attendancedb . * TO 'atsys'@'localhost';

CREATE TABLE `system_users` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `pwd` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `admin` char(1) DEFAULT 'N',
  `notes` varchar(255) DEFAULT NULL,  
  `last_active_date` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`),  
  -- CONSTRAINT `company_users_brn_fk` FOREIGN KEY (`BRN_ID`) REFERENCES `company_branches` (`id`),
  CONSTRAINT `company_users_admin_ck` CHECK ((`admin` in (_utf8mb4'N',_utf8mb4'Y')))
);