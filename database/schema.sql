CREATE TABLE FunciONario (
    id_func serial PRIMARY KEY, 
    nome TEXT NOT NULL, 
    email TEXT UNIQUE, 
    cpf varchar(11) UNIQUE, 
    cargo TEXT
);

CREATE TABLE Orgao (
    id_orgao serial PRIMARY KEY, 
    nome TEXT NOT NULL, 
    sigla TEXT NOT NULL UNIQUE 
);

CREATE TABLE Servico (
    id_serv serial PRIMARY KEY,
    nome TEXT NOT NULL,
    url TEXT,
    tipo TEXT,
    id_orgao INT NOT NULL,
    FOREIGN KEY (id_orgao) REFERENCES Orgao(id_orgao) ON DELETE CASCADE 
);

CREATE TABLE Avaliacao (
    id_ava serial PRIMARY KEY, 
    nota INT NOT NULL CHECK (nota >= 1 AND nota <= 5),
    data date,                
    hora time,                
    id_serv INT NOT NULL,     
    FOREIGN KEY (id_serv) REFERENCES Servico(id_serv)
);

CREATE TABLE Auditoria (
    id_func INT NOT NULL,      
    id_serv INT NOT NULL,     
    data date NOT NULL,       
    score INT NOT NULL CHECK (score >= 0 AND score <=100),
    tipo TEXT NOT NULL,       
    PRIMARY KEY (id_func, id_serv, data), 
    FOREIGN KEY (id_func) REFERENCES FunciONario(id_func),
    FOREIGN KEY (id_serv) REFERENCES Servico(id_serv) ON DELETE CASCADE
);