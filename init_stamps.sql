-- Удаляем старую таблицу Stamps если она существует
DROP TABLE IF EXISTS Stamps;

-- Создаем таблицу Stamps заново
CREATE TABLE Stamps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    size REAL NOT NULL,
    description TEXT,
    createdAt TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S')),
    updatedAt TEXT DEFAULT (STRFTIME('%Y-%m-%d %H:%M:%S'))
);

-- Вставляем данные из inventory_list
INSERT INTO Stamps (name, size, description) VALUES
('11.3', 11.3, 'Штамп 11.3'),
('12.8', 12.8, 'Штамп 12.8'),
('13.3 dwb new', 13.3, 'Штамп 13.3 dwb new'),
('13.3 dwb 2', 13.3, 'Штамп 13.3 dwb 2'),
('13.3 old', 13.3, 'Штамп 13.3 old'),
('14.0', 14.0, 'Штамп 14.0');
