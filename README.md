# Observatório Nacional de Acessibilidade e Qualidade Digital (Gov.br)

Este projeto consiste em um pipeline de engenharia de dados ponta a ponta (end-to-end) projetado para auditar, armazenar e analisar a conformidade dos serviços públicos digitais federais com o **e-MAG (Modelo de Acessibilidade em Governo Eletrônico)**, cruzando esses dados com a satisfação real do cidadão brasileiro.

---

## 1. Planejamento do Projeto (Metodologia 5W2H)

* **What (O que):** Um pipeline de dados para extrair serviços públicos de cartas de serviços em PDF, armazenar de forma relacionalizada e monitorar índices de acessibilidade (e-MAG/WCAG) e satisfação de usuários.
* **Why (Por que):** Promover a transparência pública e fornecer insumos de IHC (Interação Humano-Computador) para que a Secretaria de Governo Digital (SGD) do MGI identifique quais serviços precisam de melhorias urgentes de acessibilidade.
* **Who (Quem):** Desenvolvido com foco nas diretrizes e necessidades da Secretaria de Governo Digital do Ministério da Gestão e da Inovação em Serviços Públicos (MGI).
* **Where (Onde):** Dados brutos extraídos do PDF oficial de Cartas de Serviços do Gov.br, processados via Python, hospedados em banco de dados na nuvem (PostgreSQL no Supabase) com replicação local via Docker (PostgreSQL) e analisados via Power BI.
* **When (Quando):** Histórico contínuo de auditorias com rastreamento temporal.
* **How (Como):** Automação de varredura de tags HTML acoplada a um modelo de banco de dados normalizado na Terceira Forma Normal (3NF).
* **How Much (Quanto custa):** Desenvolvimento baseado em ferramentas open-source e camadas gratuitas de computação em nuvem (Custo R$ 0,00).

---

## 2. Engenharia de Requisitos

### Requisitos Funcionais (Métricas de Negócio)
* **[RF01]** O sistema deve registrar auditorias de acessibilidade automáticas (via robô) e manuais (via analistas).
* **[RF02]** O sistema deve permitir o acompanhamento histórico de evolução da acessibilidade de um mesmo serviço ao longo do tempo.
* **[RF03]** O sistema deve coletar e registrar o feedback quantitativo (notas de 1 a 5) de satisfação dos usuários do portal Gov.br.

### Requisitos Não-Funcionais (Arquitetura e Segurança)
* **[RNF01] Normalização:** O esquema relacional deve mitigar redundâncias e inconsistências de dados, atingindo conformidade estrita até a Terceira Forma Normal (3NF / BCNF).
* **[RNF02] Integridade Referencial:** O banco deve garantir que a remoção ou desativação de um órgão público remova em cascata (`ON DELETE CASCADE`) seus respectivos serviços e auditorias associados, impedindo dados órfãos.
* **[RNF03] Validação de Domínio:** O banco de dados deve utilizar constraints físicas (`CHECK`) para impedir a inserção de scores de acessibilidade inválidos (fora do intervalo de 0 a 100) ou notas de avaliação fora do intervalo de 1 a 5.

---

## 3. Modelo Lógico e Dicionário de Dados

Abaixo está o esquema lógico relacional das tabelas físicas criadas no PostgreSQL:

* **Orgao** (<u>id_orgao</u>, nome, sigla)
    * *Cadastro mestre dos Ministérios e Secretarias Federais.*
* **Servico** (<u>id_serv</u>, nome, url, tipo, *id_orgao*)
    * *id_orgao* referencia `Orgao(id_orgao)` com eliminação em cascata.
* **Funcionario** (<u>id_func</u>, nome, email, cpf, cargo)
    * *Mapeamento de auditores e contas de sistemas automatizados (ex: Robô ASES).*
* **Avaliacao** (<u>id_ava</u>, nota, data, hora, *id_serv*)
    * *id_serv* referencia `Servico(id_serv)`. Restrição de nota: `CHECK (nota >= 1 AND nota <= 5)`.
* **Auditoria** (<u>*id_func*, *id_serv*, data</u>, score, tipo)
    * *id_func* referencia `Funcionario(id_func)`.
    * *id_serv* referencia `Servico(id_serv)`.
    * *A Chave Primária Composta por (id_func, id_serv, data) viabiliza o rastreamento histórico de auditorias periódicas.*
    * Restrição de score: `CHECK (score >= 0 AND score <= 100)`.

---

---

## Próximos Passos (Roadmap de Implementação)

O projeto encontra-se em desenvolvimento ativo. As seguintes etapas e funcionalidades estão mapeadas para as próximas sprints:

* [X] **Ambiente de Staging com Docker:** Configuração de um container Docker rodando PostgreSQL local para simular o ambiente de produção, testes de integração e rotinas de backup.
* [ ] **Construção do Dashboard (Power BI):** Desenvolvimento da camada de visualização de dados para expor os indicadores de conformidade de acessibilidade e o ranking dos ministérios.
* [X] **Ingestão de Dados de Satisfação (Métrica de Negócio):** Implementação do módulo de raspagem/coleta das notas de avaliação (1 a 5 estrelas) diretamente do portal Gov.br para viabilizar o cruzamento de dados entre a qualidade técnica (e-MAG) e a percepção do cidadão.
