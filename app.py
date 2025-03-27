# MVP: Central Inteligente de Notas Fiscais (NF-e)
# Linguagem: Python | Frameworks: Flask + SQLite (simples para começar)

from flask import Flask, request, session, render_template, redirect, url_for, jsonify
import os
from datetime import datetime
import sqlite3
import xml.etree.ElementTree as ET
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder=r'C:\Users\luis.felipe\Desktop\NFeVision\templates')
app.secret_key = 'supersecretkey'
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

now = datetime.now()
now = now.strftime('%Y-%m-%d')

# === Banco de dados ===
def init_db():
    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE,
                        senha TEXT
                    )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS notas_fiscais (
                        id              INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id      INTEGER,
                        status          TEXT,
                        pagamento       TEXT,
                        cnpj_emitente   TEXT,
                        razao_social    TEXT,
                        data_emissao    TEXT,
                        data_vencimento TEXT,
                        valor_total     REAL,
                        chave_acesso    TEXT    UNIQUE,
                        data_referencia TEXT    NOT NULL,
                        categoria       TEXT,
                        FOREIGN KEY (
                            usuario_id
                        ) REFERENCES usuarios (id));
                        ''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS itens_nfe (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        nota_id INTEGER,
                        cProd TEXT,
                        xProd TEXT,
                        qCom REAL,
                        vUnCom REAL,
                        vProd REAL,
                        FOREIGN KEY(nota_id) REFERENCES notas_fiscais(id)
                    )''')
        conn.commit()

# === Leitura de XML ===
def parse_nfe_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
    emit = root.find('.//nfe:emit', ns)
    ide = root.find('.//nfe:ide', ns)
    total = root.find('.//nfe:ICMSTot', ns)
    infNFe = root.find('.//nfe:infNFe', ns)
    data_emissao_elem = ide.find('nfe:dhEmi', ns) or ide.find('nfe:dEmi', ns)
    if emit is None or total is None or infNFe is None or data_emissao_elem is None:
        raise ValueError("Campos obrigatórios não encontrados no XML.")
    nota_data = {
        'cnpj_emitente': emit.find('nfe:CNPJ', ns).text,
        'razao_social': emit.find('nfe:xNome', ns).text,
        'data_emissao': data_emissao_elem.text[:10],
        'valor_total': float(total.find('nfe:vNF', ns).text),
        'chave_acesso': infNFe.attrib['Id'].replace('NFe', ''),
        'status': "Pendente",
        'pagamento' : "Pendente",
        'data_vencimento' : "Pendente",
        'categoria' : "Pendente",
    }
    itens = []
    for item in root.findall('.//nfe:det', ns):
        prod = item.find('nfe:prod', ns)
        if prod is not None:
            cProd = prod.findtext('nfe:cProd', default='', namespaces=ns)
            xProd = prod.findtext('nfe:xProd', default='', namespaces=ns)
            qCom = float(prod.findtext('nfe:qCom', default='0', namespaces=ns))
            vUnCom = float(prod.findtext('nfe:vUnCom', default='0', namespaces=ns))
            vProd = float(prod.findtext('nfe:vProd', default='0', namespaces=ns))
            itens.append((cProd, xProd, qCom, vUnCom, vProd))
    return nota_data, itens

# === Dashboard ===
@app.route('/')
def index():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()

        # Total de notas do usuário
        c.execute('SELECT COUNT(*) FROM notas_fiscais WHERE usuario_id = ?', (session['usuario_id'],))
        total_notas = c.fetchone()[0]

        # Notas cadastradas hoje
        c.execute(f'''SELECT COUNT(*) FROM notas_fiscais
                     WHERE usuario_id = ? AND data_referencia = "{now}"''',
                  (session['usuario_id'],))
        uploads_hoje = c.fetchone()[0]

        # Erros fictícios (ajuste se quiser registrar erros reais em tabela futura)
        erros_processamento = 0

        # Lista de notas para a tabela do dashboard
        c.execute('''SELECT id, razao_social, cnpj_emitente, data_emissao, valor_total, chave_acesso
                     FROM notas_fiscais
                     WHERE usuario_id = ?
                     ORDER BY data_emissao DESC''', (session['usuario_id'],))
        notas = c.fetchall()

    return render_template('dashboard.html',
                           notas=notas,
                           total_notas=total_notas,
                           uploads_hoje=uploads_hoje,
                           erros_processamento=erros_processamento)


# === Upload de XML ===
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files.get('nfe_xml')
        if file and file.filename.endswith('.xml'):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                nota_data, itens = parse_nfe_xml(filepath)
                with sqlite3.connect('nfe.db') as conn:
                    c = conn.cursor()
                    c.execute('''INSERT OR IGNORE INTO notas_fiscais
                                 (usuario_id, status, pagamento, cnpj_emitente, razao_social, data_emissao, 
                                 data_vencimento, valor_total, chave_acesso, data_referencia, categoria)
                                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                              (session['usuario_id'], nota_data['status'], nota_data['pagamento'], nota_data['cnpj_emitente'], nota_data['razao_social'],
                               nota_data['data_emissao'], nota_data['data_vencimento'], 
                               nota_data['valor_total'], nota_data['chave_acesso'], now, nota_data['categoria']))
                    conn.commit()

                    c.execute('SELECT id FROM notas_fiscais WHERE chave_acesso = ?', (nota_data['chave_acesso'],))
                    nota_id = c.fetchone()[0]

                    for item in itens:
                        c.execute('''INSERT INTO itens_nfe (nota_id, cProd, xProd, qCom, vUnCom, vProd)
                                     VALUES (?, ?, ?, ?, ?, ?)''', (nota_id, *item))
                    conn.commit()
                return render_template('upload.html', mensagem='Nota fiscal enviada com sucesso!')
            except Exception as e:
                return render_template('upload.html', erro=f'Erro ao processar XML: {str(e)}')

        return render_template('upload.html', erro='Arquivo inválido. Envie um arquivo XML.')

    return render_template('upload.html')

# === Gerenciamento de Notas ===
@app.route('/gerenciamento')
def gerenciamento():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    razao_social = request.args.get('razao_social', '')
    cnpj = request.args.get('cnpj', '')
    data_inicio = request.args.get('data_inicio', '')
    valor_total = request.args.get('valor_total', '')

    query = '''SELECT id, razao_social, status, pagamento, cnpj_emitente, data_emissao, data_vencimento, 
                valor_total, chave_acesso, categoria
               FROM notas_fiscais WHERE usuario_id = ?'''
    params = [session['usuario_id']]

    if razao_social:
        query += ' AND razao_social LIKE ?'
        params.append(f'%{razao_social}%')
    if cnpj:
        query += ' AND cnpj_emitente LIKE ?'
        params.append(f'%{cnpj}%')
    if data_inicio:
        query += ' AND DATE(data_emissao) >= DATE(?)'
        params.append(data_inicio)
    if valor_total:
        query += ' AND valor_total = ?'
        params.append(valor_total)

    query += ' ORDER BY data_emissao DESC'

    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        c.execute(query, params)
        notas = c.fetchall()

    return render_template('gerenciamento.html', notas=notas)

@app.route('/nota/<int:nota_id>/excluir')
def excluir_nota(nota_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        # Apaga os itens primeiro
        c.execute('DELETE FROM itens_nfe WHERE nota_id = ?', (nota_id,))
        # Depois apaga a nota
        c.execute('DELETE FROM notas_fiscais WHERE id = ? AND usuario_id = ?', (nota_id, session['usuario_id']))
        conn.commit()

    return redirect(url_for('gerenciamento'))

@app.route('/nota/<int:nota_id>/editar', methods=['GET', 'POST'])
def editar_nota(nota_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        if request.method == 'POST':
            razao_social = request.form['razao_social']
            cnpj = request.form['cnpj_emitente']
            data_emissao = request.form['data_emissao']
            valor_total = request.form['valor_total']
            chave_acesso = request.form['chave_acesso']
            status = request.form['status']
            pagamento = request.form['pagamento']
            data_vencimento = request.form['data_vencimento']
            categoria = request.form['categoria']

            c.execute('''UPDATE notas_fiscais
                         SET razao_social = ?, cnpj_emitente = ?, data_emissao = ?, valor_total = ?, chave_acesso = ?,
                             status = ?, pagamento = ?, data_vencimento = ?, categoria = ?
                         WHERE id = ? AND usuario_id = ?''',
                      (razao_social, cnpj, data_emissao, valor_total, chave_acesso,
                       status, pagamento, data_vencimento, categoria, nota_id, session['usuario_id']))
            conn.commit()
            return redirect(url_for('gerenciamento'))

        # Corrigir ordem dos campos para bater com o HTML
        c.execute('''SELECT razao_social, cnpj_emitente, data_emissao, valor_total, chave_acesso,
                            status, pagamento, data_vencimento, categoria
                     FROM notas_fiscais WHERE id = ? AND usuario_id = ?''',
                  (nota_id, session['usuario_id']))
        nota = c.fetchone()

    return render_template('editar_nota.html', nota=nota, nota_id=nota_id)


# === Visualizar Itens ===
@app.route('/nota/<int:nota_id>/itens')
def ver_itens_json(nota_id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        c.execute('''SELECT cProd, xProd, qCom, vUnCom, vProd
                     FROM itens_nfe WHERE nota_id = ?''', (nota_id,))
        itens = c.fetchall()
    return jsonify(itens)

# === Cadastro Manual ===
@app.route('/cadastro_manual', methods=['GET', 'POST'])
def cadastro_manual():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        razao_social = request.form['razao_social']
        cnpj_emitente = request.form['cnpj_emitente']
        data_emissao = request.form['data_emissao']
        valor_total = request.form['valor_total']
        chave_acesso = request.form['chave_acesso']

        try:
            with sqlite3.connect('nfe.db') as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO notas_fiscais 
                             (usuario_id, cnpj_emitente, razao_social, data_emissao, valor_total, chave_acesso, data_referencia)
                             VALUES (?, ?, ?, ?, ?, ?, ?)''',
                          (session['usuario_id'], cnpj_emitente, razao_social, data_emissao, valor_total, chave_acesso, now))
                conn.commit()
            return render_template('cadastro_manual.html', mensagem='Nota fiscal cadastrada com sucesso!')
        except sqlite3.IntegrityError:
            return render_template('cadastro_manual.html', erro='Chave de acesso já cadastrada.')

    return render_template('cadastro_manual.html')

# === Usuarios ===
@app.route('/admin/usuarios')
def admin_usuarios():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    with sqlite3.connect('nfe.db') as conn:
        c = conn.cursor()
        c.execute('''
            SELECT u.id, u.email, COUNT(n.id) as total_notas
            FROM usuarios u
            LEFT JOIN notas_fiscais n ON n.usuario_id = u.id
            GROUP BY u.id, u.email
            ORDER BY u.id
        ''')
        usuarios = c.fetchall()
    return render_template('usuarios.html', usuarios=usuarios)


# === Login ===
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        with sqlite3.connect('nfe.db') as conn:
            c = conn.cursor()
            c.execute('SELECT id FROM usuarios WHERE email = ? AND senha = ?', (email, senha))
            user = c.fetchone()
            if user:
                session['usuario_id'] = user[0]
                return redirect(url_for('index'))
            else:
                return render_template('login.html', erro="Login inválido.")
    return render_template('login.html')


# === Cadastro ===
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        try:
            with sqlite3.connect('nfe.db') as conn:
                c = conn.cursor()
                c.execute('INSERT INTO usuarios (email, senha) VALUES (?, ?)', (email, senha))
                conn.commit()
            return render_template('login.html', mensagem="Cadastro realizado com sucesso.")
        except sqlite3.IntegrityError:
            return render_template('cadastro.html', erro="E-mail já cadastrado.")
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
