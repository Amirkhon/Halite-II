ALTER TABLE `halite2`.`user` 
CHANGE COLUMN `oauth_id` `oauth_id` INT(12) NULL ,
CHANGE COLUMN `oauth_provider` `oauth_provider` TINYINT(1) NULL ,
CHANGE COLUMN `is_email_good` `is_email_good` TINYINT(1) NOT NULL DEFAULT '1',
CHANGE COLUMN `verification_code` `verification_code` VARCHAR(64) NOT NULL ,
ADD UNIQUE INDEX `verification_code_UNIQUE` (`verification_code` ASC);

INSERT INTO `halite2`.`organization` (`organization_name`, `kind`, `verification_code`) VALUES ('ACI Worldwide Russia', 'Company', 'ACI_VER_CODE');
INSERT INTO `halite2`.`organization_email_domain` (`organization_id`, `domain`) VALUES ('26472', 'students24.com');
INSERT INTO `halite2`.`hackathon` (`title`, `description`, `start_date`, `end_date`, `verification_code`, `organization_id`, `location`, `is_open`) VALUES ('Students 24', 'ACI Worldwide Russia Student Programming Competition', '2018-11-24 08:00:00', '2018-11-24 18:00:00', 'S24VCODE', '26472', 'Kazan & Yoshkar-Ola', '1');

insert into user (username, email, verification_code) values
('Fathers of Google', 'penkov.pavel.it@gmail.com',  'dHIg5Sbaec'), 
('Looney tunes ', 'alexey99979@yandex.ru',  'sWevDIOVfu'), 
('Как тебе такое Илон Маск?', 'bezrukovq@yandex.ru',  'JFXlsFPtBc'), 
('Ромашка', 'daniil.klinov@bk.ru',  'eqrxyCG1ZN'), 
('SKOP', 'azot273@gmail.com',  'qNWzdQ4kO8'), 
('LEMON', 'razil0071999@gmail.com',  'UcwbJlXTsN'), 
('Феечки', 'alb-ert@mail.ru',  'bIk0TkBwqt'), 
('До-Диез', 'graf.rav@gmail.com',  'UTGSlVdh1n'), 
('Французы', 'alisher.gulov97@mail.ru',  'XdFUuzsHLw'), 
('В поисках бага', 'fexolm@gmail.com',  '6lCEKuspBT'), 
('Один бежал, другой стрелял', 'amionv99@gmail.com',  'BYfxHL1GNx'), 
('КоШи', 'alex.korum@mail.ru',  '5JaNGgLw6S'), 
('ReMind', 'canismajorisvy@yandex.ru',  'xKMlh4cYgH'), 
('Pheonix', 'ilnursup@mail.ru',  '1Q2q4C86mT'), 
('Garbage collectors', 'reenaz@mail.ru',  'Oz1RWLeWlw'), 
('Горбатая гора', 'dkarpov.it@gmail.com',  '7SAo39BC7p'), 
('Sunny Narwhal', 'nikita.karamoff@gmail.com',  'IgyR0hXJI3'), 
('mute all chat', 'ernestfilippov@mail.ru',  'O2Uvhji6MC'), 
('ZDL', 'samat.zay@mail.ru',  'CTEPlxLkfD'), 
('Нияз', 'learpyp@gmail.com',  'r3xdqfLsz1'), 
('ParseMarsters', 'kadyrov_samat@inbox.ru',  'k6y6hm8tPU'), 
('Бульба', 'gtoshev2@mail.ru',  'v4U7a2YS1d'), 
('BorruZ', 'ruzalin4ik@mail.ru',  'vf3snP5c8e'), 
('Поехали', 's.sawka@mail.ru',  'ig5gRWz2tc'), 
('704', 'borisgk98@ya.ru',  'J4D53cUuQ4'), 
('); drop table users cascade; --', 'farvaev.emil@gmail.com',  'LA2OZZNwFf'), 
('In Doge We Trust', 'random.finelife@gmail.com',  '1lmnrPD1H0'), 
('ТВИМС', 'rinat@khanov.com',  'GLn4oTdasi');

update user set organization_id = (select id from organization limit 1) where id > 0;

DROP PROCEDURE IF EXISTS ROWPERROW;
DELIMITER ;;

CREATE PROCEDURE ROWPERROW()
BEGIN
DECLARE hackathon_id INT DEFAULT 0;
DECLARE n INT DEFAULT 0;
DECLARE i INT DEFAULT 0;
SELECT id FROM hackathon limit 1 INTO hackathon_id;
SELECT COUNT(*) FROM user INTO n;
SET i=0;
WHILE i<n DO 
  INSERT INTO hackathon_participant(hackathon_id, user_id) values (hackathon_id, (SELECT id FROM user LIMIT i,1));
  SET i = i + 1;
END WHILE;
End;
;;

DELIMITER ;

CALL ROWPERROW();