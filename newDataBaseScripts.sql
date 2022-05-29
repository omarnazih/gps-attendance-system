CREATE TABLE `halls` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `loc_lat` double DEFAULT NULL,
  `loc_lang` double DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `halls_uq` (`name`,`loc_lat`,`loc_lang`)
);

CREATE TABLE `majors` (
  `id` int NOT NULL,
  `code` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `modules` (
  `id` int NOT NULL,
  `code` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `major_id` int DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `classes_major_id_fk` (`major_id`),
  CONSTRAINT `classes_major_id_fk` FOREIGN KEY (`major_id`) REFERENCES `majors` (`id`)
);

CREATE TABLE `sch_groups` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
);

CREATE TABLE `schedule` (
  `id` int NOT NULL,
  `hall_id` int DEFAULT NULL,
  `module_id` int DEFAULT NULL,
  `day` varchar(255) DEFAULT NULL,
  `time` time DEFAULT NULL,
  `grp_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `schedule_hall_id_fk` (`hall_id`),
  KEY `schedule_class_id_fk` (`module_id`),
  KEY `schedule_group_id_fk` (`grp_id`),
  CONSTRAINT `schedule_class_id_fk` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`),
  CONSTRAINT `schedule_group_id_fk` FOREIGN KEY (`grp_id`) REFERENCES `sch_groups` (`id`),
  CONSTRAINT `schedule_hall_id_fk` FOREIGN KEY (`hall_id`) REFERENCES `halls` (`id`)
);

CREATE TABLE `users` (
  `id` int NOT NULL,
  `username` varchar(255) NOT NULL,
  `pwd` varchar(255) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `notes` varchar(255) DEFAULT NULL,
  `sch_id` int DEFAULT NULL,
  `year` int DEFAULT NULL,
  `last_active_date` datetime DEFAULT NULL,
  `picture` varchar(255) DEFAULT NULL,
  `usertype` char(1) DEFAULT 'S',
  `major_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `users_sch_id_fk` (`sch_id`),
  KEY `USERS_MAJOR_ID_FK` (`major_id`),
  CONSTRAINT `USERS_MAJOR_ID_FK` FOREIGN KEY (`major_id`) REFERENCES `majors` (`id`),
  CONSTRAINT `users_sch_id_fk` FOREIGN KEY (`sch_id`) REFERENCES `schedule` (`id`)
);

CREATE TABLE `attendance` (
  `id` int NOT NULL,
  `date` varchar(255) NOT NULL,
  `time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `module_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `attendance_uq` (`date`,`module_id`),
  KEY `attendance_user_id_fk` (`user_id`),
  KEY `attendance_class_id_fk` (`module_id`),
  CONSTRAINT `attendance_class_id_fk` FOREIGN KEY (`module_id`) REFERENCES `modules` (`id`),
  CONSTRAINT `attendance_user_id_fk` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
);