CREATE USER 'atsys'@'localhost' IDENTIFIED BY 'atsys';

GRANT ALL PRIVILEGES ON attendancedb . * TO 'atsys'@'localhost';

CREATE TABLE `system_users` (
  `id` int NOT NULL,
  `name` varchar(255) NOT NULL,
  `pwd` varchar(255) NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `admin` char(1) DEFAULT 'N',
  `student` char(1) DEFAULT 'N',
  `teacher` char(1) DEFAULT 'N',
  `notes` varchar(255) DEFAULT NULL,  
  `last_active_date` datetime DEFAULT NULL,
  PRIMARY KEY (`ID`),  
  -- CONSTRAINT `company_users_brn_fk` FOREIGN KEY (`BRN_ID`) REFERENCES `company_branches` (`id`),
  CONSTRAINT `system_users_admin_ck` CHECK ((`admin` in ('N','Y'))),
  CONSTRAINT `system_users_student_ck` CHECK ((`admin` in ('N','Y'))),
  CONSTRAINT `system_users_teacher_ck` CHECK ((`admin` in ('N','Y')))
);
 
-- alter table system_users
-- add `student` char(1) DEFAULT 'N';

-- alter table system_users
-- add `teacher` char(1) DEFAULT 'N';

-- alter table system_users
-- add CONSTRAINT `system_users_student_ck` CHECK ((`admin` in ('N','Y')));

-- alter table system_users
-- add CONSTRAINT `system_users_teacher_ck` CHECK ((`admin` in ('N','Y')));

insert into system_users values ( 1, 'admin', '123', 'admin@gmail.com', 'Y', 'N', 'N', null, null);

-- Date : 23-05-22
create table majors(
	id int not null,
	code varchar(255) not null,
    name varchar(255) not null,
    primary key (id)    
);

create table years (
	id int not null,
    code int not null,
    name varchar(255) not null,
    primary key (id)
);

create table classes (
	id int not null,
    code varchar(255) not null,
    name varchar(255) not null,    
	year_id int,   
    major_id int,
    loc_lat double,
    loc_lang double,    
    description varchar(255),
    primary key (id),
    constraint classes_year_id_fk foreign key (year_id) references years(id),
    constraint classes_major_id_fk foreign key (major_id) references majors(id)
);

create table students (
	id int not null,    
    code int not null,
    name varchar(255) not null,
    user_id int,
    class_id int,       
    picture varchar(255) not null,
    primary key (id),
    constraint students_user_id_fk foreign key (user_id) references system_users(id),
    constraint students_class_id_fk foreign key (class_id) references classes(id)
);

create table attendance (
	id int not null,  
    date varchar(255) not null,
    time DATETIME DEFAULT CURRENT_TIMESTAMP not null,
    student_id int not null,
    class_id int not null,    	
    primary key (id),
    CONSTRAINT attendance_uq UNIQUE (date,student_id,class_id),
    constraint attendance_student_id_fk foreign key (student_id) references students(id),
    constraint attendance_class_id_fk foreign key (class_id) references classes(id)
);

insert into majors values ( 1, 'CS', 'Computer Science');
insert into years values ( 1, 1, 'Freshmen');
insert into classes values (
 1, 
'SE101', 
'Software Engineering',
1,
1, 
30.5765383, 31.5040656, 
'Software Engineering or SE123 is for cs majors and its a good course');
insert into students values ( 1, 101, 'Omar nazih mohamed', 2, 1, 'C:\Users\PC\Documents\GitHub\gps-attendance-system\app\images\omar.jpg');