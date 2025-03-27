from flask import Flask, render_template, request, redirect, url_for, session
import matplotlib.pyplot as plt
import io
import base64
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Минимальная и максимальная ставка
MIN_BET = 10
MAX_BET = 10000

# Начальный баланс пользователя
INITIAL_BALANCE = 1000

# Список доступных событий для ставок
events = [
    {"id": 1, "name": "Футбол: Россия - Бразилия", "odds": [2.5, 3.2, 2.8]},
    {"id": 2, "name": "Теннис: Надаль - Федерер", "odds": [1.8, 2.1]},
    {"id": 3, "name": "Баскетбол: ЦСКА - Лейкерс", "odds": [1.9, 2.0]},
    {"id": 4, "name": "Хоккей: СКА - Динамо", "odds": [2.0, 3.0, 2.5]},
]


@app.route('/')
def index():
    # Инициализация баланса пользователя при первом посещении
    if 'balance' not in session:
        session['balance'] = INITIAL_BALANCE

    return render_template('index.html', events=events, balance=session['balance'])


@app.route('/bet/<int:event_id>', methods=['GET', 'POST'])
def place_bet(event_id):
    # Получаем информацию о событии
    event = next((e for e in events if e['id'] == event_id), None)
    if not event:
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Получаем данные из формы
        bet_amount = float(request.form['amount'])
        selected_outcome = int(request.form['outcome'])

        # Проверяем, что ставка в допустимых пределах
        if bet_amount < MIN_BET or bet_amount > MAX_BET:
            return render_template('bet.html', event=event, error=f"Ставка должна быть между {MIN_BET} и {MAX_BET}")

        # Проверяем, что у пользователя достаточно средств
        if bet_amount > session['balance']:
            return render_template('bet.html', event=event, error="Недостаточно средств на балансе")

        # Вычисляем потенциальный выигрыш
        potential_win = bet_amount * event['odds'][selected_outcome]

        # Сохраняем данные ставки в сессии
        session['current_bet'] = {
            'event_id': event_id,
            'event_name': event['name'],
            'bet_amount': bet_amount,
            'selected_outcome': selected_outcome,
            'potential_win': potential_win,
            'odds': event['odds'][selected_outcome]
        }

        # Генерируем график выигрыша
        plot_url = generate_win_chart(bet_amount, event['odds'])

        return render_template('result.html',
                               bet=session['current_bet'],
                               plot_url=plot_url,
                               balance=session['balance'])

    return render_template('bet.html', event=event, balance=session['balance'])


@app.route('/process_bet', methods=['POST'])
def process_bet():
    if 'current_bet' not in session:
        return redirect(url_for('index'))

    # Симулируем случайный результат
    current_bet = session['current_bet']
    event = next((e for e in events if e['id'] == current_bet['event_id']), None)

    # Генерируем случайный победитель
    winning_outcome = random.randint(0, len(event['odds']) - 1)

    # Проверяем, выиграла ли ставка
    if winning_outcome == current_bet['selected_outcome']:
        win_amount = current_bet['potential_win']
        result_message = f"Поздравляем! Вы выиграли {win_amount:.2f}!"
        session['balance'] += win_amount
    else:
        win_amount = 0
        result_message = "К сожалению, вы проиграли."
        session['balance'] -= current_bet['bet_amount']

    # Сохраняем историю ставок
    if 'bet_history' not in session:
        session['bet_history'] = []

    session['bet_history'].append({
        'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'event': current_bet['event_name'],
        'bet_amount': current_bet['bet_amount'],
        'win_amount': win_amount,
        'odds': current_bet['odds']
    })

    # Очищаем текущую ставку
    session.pop('current_bet', None)

    return render_template('index.html',
                           events=events,
                           balance=session['balance'],
                           result_message=result_message)


def generate_win_chart(bet_amount, odds):
    """Генерирует график потенциальных выигрышей для разных исходов"""
    outcomes = range(len(odds))
    potential_wins = [bet_amount * odd for odd in odds]

    plt.figure(figsize=(8, 4))
    bars = plt.bar(outcomes, potential_wins, color=['#4CAF50', '#2196F3', '#FF5722'])

    plt.title('Потенциальные выигрыши по исходам')
    plt.xlabel('Исход')
    plt.ylabel('Выигрыш')
    plt.xticks(outcomes, [f"Исход {i + 1}" for i in outcomes])

    # Добавляем значения на столбцы
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2., height,
                 f'{height:.2f}',
                 ha='center', va='bottom')

    # Сохраняем график в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()

    # Кодируем изображение в base64
    plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
    return f"data:image/png;base64,{plot_url}"


if __name__ == '__main__':
    app.run(debug=True)