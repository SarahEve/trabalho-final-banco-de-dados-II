from flask import Flask, render_template, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Conexão com o banco de dados
mongopass = "mongodb://localhost:27017/"
client = MongoClient(mongopass)
db = client["recycle_system"]
points_collection = db['points']
users_collection = db['users']

# Página inicial
@app.route('/')
def index():
    if 'user_email' in session:
        user_name = session.get('user_name')
        return render_template('index.html', user_name=user_name)
    return redirect(url_for('login'))

# Página de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_collection.find_one({'email': email, 'password': password})
        if user:
            session['user_email'] = user['email']
            session['user_name'] = user['name']
            session['user_profile'] = user['profile']
            flash('Login bem-sucedido!')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.')
    return render_template('login.html')

# Página de cadastro de usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')  # Uso de get para evitar KeyError
        email = request.form.get('email')
        password = request.form.get('password')
        profile = request.form.get('profile')  # Uso de get para evitar KeyError

        if profile is None:
            flash('Selecione um perfil para se cadastrar.')
            return redirect(url_for('register'))

        users_collection.insert_one({
            'name': name,
            'email': email,
            'password': password,
            'profile': profile
        })
        flash('Cadastro realizado com sucesso! Você pode fazer login agora.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Página para adicionar um novo ponto de descarte
@app.route('/add_point', methods=['GET', 'POST'])
def add_point():
    if 'user_profile' in session and session['user_profile'] == 'coleta':
        flash('Usuários de coleta não podem adicionar pontos de descarte.')
        return redirect(url_for('index'))

    if request.method == 'POST':
        address = request.form['address']
        waste_type = request.form['waste_type']
        status = 'pending'
        user_email = session['user_email']  # Associa o ponto ao usuário que está logado

        points_collection.insert_one({
            'address': address,
            'waste_type': waste_type,
            'status': status,
            'user_email': user_email  # Associando o ponto ao usuário
        })

        flash('Ponto de descarte adicionado com sucesso!')
        return redirect(url_for('index'))

    return render_template('add_point.html')

# Página para mostrar pontos disponíveis para coleta
@app.route('/match')
def match():
    if 'user_profile' in session and session['user_profile'] == 'coleta':
        points = points_collection.find({'status': 'pending'})
        return render_template('match.html', points=points)
    return redirect(url_for('index'))

# Atualizar status do ponto (para indicar que foi coletado)
@app.route('/collect/<point_id>', methods=['POST'])
def collect(point_id):
    points_collection.update_one({'_id': ObjectId(point_id)}, {'$set': {'status': 'collected'}})
    flash('Ponto coletado com sucesso!')
    return redirect(url_for('match'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('Você foi desconectado.')
    return redirect(url_for('login'))

# Histórico
@app.route('/history')
def history():
    if 'user_profile' in session and session['user_profile'] == 'descarte':
        user_email = session['user_email']
        points = points_collection.find({'user_email': user_email})
        return render_template('history.html', points=points)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)