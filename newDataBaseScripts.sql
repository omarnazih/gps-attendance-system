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

alter table schedule
add year INT(1);

alter table schedule
add major_id INT;

alter table schedule
add constraint schedule_major_id_fk foreign key (major_id) references majors(id);

alter table users
drop constraint users_sch_id_fk ;

alter table users
drop sch_id;

alter table users
add grp_id int;

alter table users
add constraint users_grp_id_fk foreign key (grp_id) references sch_groups(id);        

-- 04/06/2022 12:24
create table years (
	id int not null,
    year varchar(250),
    PRIMARY KEY (ID),
    constraint years_uq unique(id, year)
);

INSERT INTO `attendancedb`.`years` (`id`, `year`) VALUES ('1', 'Prep');
INSERT INTO `attendancedb`.`years` (`id`, `year`) VALUES ('2', 'Y1');
INSERT INTO `attendancedb`.`years` (`id`, `year`) VALUES ('3', 'Y2');
INSERT INTO `attendancedb`.`years` (`id`, `year`) VALUES ('4', 'Y4');
INSERT INTO `attendancedb`.`years` (`id`, `year`) VALUES ('5', 'Y5');

create table schedule_hd (
	id int not null,
    major_id int,
    year int,
    grp_id int,
    PRIMARY KEY (ID),
    constraint schedule_hd_major_id_fk foreign key (major_id) references majors(id),
    constraint schedule_hd_year_id_fk foreign key (year) references years(id),
    constraint schedule_hd_grp_id_fk foreign key (grp_id) references sch_groups(id),
    constraint schedule_hd_uq unique(major_id, year, grp_id)
);

alter table schedule 
add hd_id int;

alter table schedule 
add constraint schedule_hd_id_fk foreign key (hd_id) references schedule_hd(id);


ALTER TABLE `attendancedb`.`schedule` 
DROP FOREIGN KEY `schedule_major_id_fk`,
DROP FOREIGN KEY `schedule_group_id_fk`;
ALTER TABLE `attendancedb`.`schedule` 
DROP COLUMN `major_id`,
DROP COLUMN `year`,
DROP COLUMN `grp_id`,
DROP INDEX `schedule_major_id_fk` ,
DROP INDEX `schedule_group_id_fk` ;
;

-- 09/06/2022
alter table halls
add floor int;