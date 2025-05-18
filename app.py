import os
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import csv
import io
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = '788932HJIOsadihdshHI'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance_manager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- MODELS ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    transactions = db.relationship('Transaction', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    t_type = db.Column(db.String(16), nullable=False)  # income/expense
    date = db.Column(db.Date, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


# --- UTILS ---

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None


#  advice
def get_market_activity():
    tickers = ['AAPL', 'GOOGL', 'TSLA', 'AMZN', 'BTC', 'ETH']
    return [{
        'symbol': t,
        'price': round(random.uniform(80, 3200), 2),
        'change': round(random.uniform(-2, 2), 2)
    } for t in tickers]


def get_daily_advice():
    advices = [
        "Рассмотрите покупку акций с растущей динамикой, например, AAPL.",
        "Сегодня наилучшие перспективы у криптовалюты BTC.",
        "Диверсифицируйте портфель: добавьте облигации.",
        "Избегайте инвестиций в волатильные активы вроде TSLA сегодня.",
        "AMZN выглядит перепроданным, возможен рост.",
        "ETH показывает стабильность — хорош для долгосрочных вложений."
    ]
    return random.choice(advices)


# --- ROUTES ---

@app.route('/')
def index():
    user = get_current_user()
    return render_template('index.html', user=user)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        if not username or not password:
            flash('Поля не могут быть пустыми.')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Пользователь с таким именем уже существует.')
            return redirect(url_for('register'))
        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация прошла успешно! Войдите в систему.')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Ошибка регистрации: {}'.format(str(e)))
            return redirect(url_for('register'))
    return render_template('register.html', user=get_current_user())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Вы вошли в систему.')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль.')
    return render_template('login.html', user=get_current_user())


@app.route('/demo-login')
def demo_login():
    # Входим тестовым пользователем
    user = User.query.filter_by(username="demo").first()
    if not user:
        # Создаем, если не существует
        user = User(username="demo")
        user.set_password("demo")
        db.session.add(user)
        db.session.commit()
    session['user_id'] = user.id
    flash('Вы вошли как демо-пользователь.')
    return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы.')
    return redirect(url_for('index'))


@app.route('/dashboard')
def dashboard():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    transactions = Transaction.query.filter_by(user_id=user.id).order_by(Transaction.date.desc()).all()
    income = sum(t.amount for t in transactions if t.t_type == 'income')
    expense = sum(t.amount for t in transactions if t.t_type == 'expense')
    categories = list(set(t.category for t in transactions))
    return render_template(
        'dashboard.html',
        user=user,
        transactions=transactions,
        income=income,
        expense=expense,
        categories=categories,
        date=date
    )


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    category = request.form['category']
    amount = float(request.form['amount'])
    t_type = request.form['t_type']
    t_date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()
    transaction = Transaction(category=category, amount=amount, t_type=t_type, date=t_date, user_id=user.id)
    db.session.add(transaction)
    db.session.commit()
    flash('Транзакция добавлена!')
    return redirect(url_for('dashboard'))


@app.route('/analytics')
def analytics():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    # аналитика на месяц
    monthly_data = {}
    for t in Transaction.query.filter_by(user_id=user.id).all():
        ym = t.date.strftime('%Y-%m')
        if ym not in monthly_data:
            monthly_data[ym] = {'income': 0, 'expense': 0}
        monthly_data[ym][t.t_type] += t.amount
    months = sorted(monthly_data.keys())
    incomes = [monthly_data[m]['income'] for m in months]
    expenses = [monthly_data[m]['expense'] for m in months]
    # Pie chart data
    cat_data = {}
    for t in Transaction.query.filter_by(user_id=user.id, t_type='expense').all():
        cat_data[t.category] = cat_data.get(t.category, 0) + t.amount
    return render_template(
        'analytics.html',
        user=user,
        months=months,
        incomes=incomes,
        expenses=expenses,
        cat_data=cat_data
    )


@app.route('/export')
def export():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Дата', 'Категория', 'Тип', 'Сумма'])
    for t in Transaction.query.filter_by(user_id=user.id).all():
        writer.writerow([t.date.strftime('%Y-%m-%d'), t.category, t.t_type, t.amount])
    output.seek(0)
    return send_file(io.BytesIO(output.read().encode('utf-8')),
                     mimetype='text/csv',
                     as_attachment=True,
                     download_name='transactions.csv')


@app.route('/market')
def market():
    user = get_current_user()
    market_data = get_market_activity()
    advice = get_daily_advice()
    return render_template('market.html', user=user, market_data=market_data, advice=advice)


@app.route('/api/monthly')
def api_monthly():
    user = get_current_user()
    if not user:
        return jsonify({})
    monthly_data = {}
    for t in Transaction.query.filter_by(user_id=user.id).all():
        ym = t.date.strftime('%Y-%m')
        if ym not in monthly_data:
            monthly_data[ym] = {'income': 0, 'expense': 0}
        monthly_data[ym][t.t_type] += t.amount
    months = sorted(monthly_data.keys())
    incomes = [monthly_data[m]['income'] for m in months]
    expenses = [monthly_data[m]['expense'] for m in months]
    return jsonify({'months': months, 'incomes': incomes, 'expenses': expenses})


@app.route('/api/pie')
def api_pie():
    user = get_current_user()
    if not user:
        return jsonify({})
    cat_data = {}
    for t in Transaction.query.filter_by(user_id=user.id, t_type='expense').all():
        cat_data[t.category] = cat_data.get(t.category, 0) + t.amount
    return jsonify(cat_data)


# --- INIT DB ---

@app.cli.command('init-db')
def init_db():
    db.create_all()
    # Добавление тестового пользователя
    if not User.query.filter_by(username="demo").first():
        user = User(username="demo")
        user.set_password("demo")
        db.session.add(user)
        db.session.commit()
        print('Демо-пользователь создан: demo/demo')
    else:
        print('Демо-пользователь уже существует.')
    print('Database initialized.')


# -- Окак(лучшая часть) --
@app.errorhandler(500)
@app.errorhandler(404)
def error_handler(error):
    return render_template('error_cat.html', error=error, user=get_current_user()), getattr(error, 'code', 500)


if __name__ == '__main__':
    app.run(debug=True)
