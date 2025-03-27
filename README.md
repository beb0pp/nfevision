# 📄 NFeVision

Sistema web para gestão e análise inteligente de Notas Fiscais Eletrônicas (NF-e), desenvolvido com Python (Flask), SQLite, HTML/CSS moderno e integração com leitura de XML.

---

## 🚀 Funcionalidades

- 🔐 Login e cadastro de usuários
- 📊 Dashboard com resumos e estatísticas
- 📁 Upload de arquivos XML de NF-e
- 📄 Leitura e extração automática de dados do XML
- 🧾 Cadastro manual de NF-e
- 🧮 Cálculo de itens e totalizadores
- 🧠 Classificação por status, pagamento e categoria
- 📂 Gerenciamento completo das notas cadastradas
- 📌 Filtros por data, valor, CNPJ e mais
- 👁 Visualização detalhada dos itens da nota
- 👨‍💼 Painel Admin para gestão de usuários

---

## 🧱 Tecnologias Utilizadas

| Tecnologia | Descrição |
|------------|-------------|
| Python     | Back-end principal (Flask) |
| Flask      | Framework leve e rápido |
| SQLite     | Banco de dados local e simples |
| HTML/CSS   | Interface responsiva e moderna |
| JavaScript | Funcionalidades dinâmicas (modais, filtros) |
| FontAwesome | Ícones estilosos no layout |

---

## 🖼 Layout

O projeto segue um visual moderno e limpo:

- 🎨 Painel lateral fixo
- 📊 Cards com números destacados
- 🧾 Tabela de gerenciamento com bordas coloridas
- 💡 Cores por status: verde, amarelo, vermelho, azul, cinza

---

## 📦 Instalação

```bash
# Clone o repositório
$ git clone https://github.com/seu-usuario/nfevision.git

# Entre no diretório
$ cd nfevision

# Instale as dependências
$ pip install -r requirements.txt

# Execute o sistema
$ python app.py
```

A aplicação estará disponível em: `http://localhost:5000`

---

## 🗃 Estrutura de Pastas

```
NFeVision/
│
├── static/               # Arquivos CSS, JS, ícones
├── templates/            # HTMLs (dashboard, login, upload...)
├── uploads/              # Armazenamento dos arquivos XML
├── app.py                # Lógica principal do sistema
├── nfe.db                # Banco de dados SQLite
└── requirements.txt      # Dependências
```

---

## 📘 Observações

- O sistema é focado para uso interno por empresas, contadores e administradores financeiros.
- Pode ser facilmente migrado para PostgreSQL ou MySQL.
- Suporte a leitura completa de XML baseado na estrutura da SEFAZ.

---

## 📬 Contato

Se desejar contribuir ou precisa de ajuda:

**Dev:** Luis Abreu\
**Sócios:** Enzo Cunha, Pedro Henrique\
**Email:** luss.fel@gmai.com
<!-- **LinkedIn:** [linkedin.com/in/seu-usuario](https://linkedin.com/in/seu-usuario) -->

---

Feito com 💙 para transformar o controle de NF-e em algo simples e elegante.
