from flask import Flask, render_template, request, redirect, url_for
import threading
import os
import random
from bot import bot, fetch_user_report, users_table, log_message, get_random_line
from SQLTable import SQLTable

app = Flask(__name__)
HOMEDIR = 'C:\\Users\\lewdm\\source\\repos\\FlaskWebProject6\\FlaskWebProject6\\data\\'
HELLO_FILE = HOMEDIR + 'hello.txt'
FACTS_FILE = HOMEDIR + 'facts.txt'

DB_CONFIG = {
    'user': 'j1007852',
    'password': 'el|N#2}-F8',
    'host': 'mysql.j1007852.myjino.ru',
    'database': 'j1007852',
    'charset': 'utf8mb4'
}

# Инициализация таблиц
users_table = SQLTable(DB_CONFIG, "users")
messages_table = SQLTable(DB_CONFIG, "messages")  # Таблица сообщений
games_table = SQLTable(DB_CONFIG, "games")        # Таблица игр
commands_log_table = SQLTable(DB_CONFIG, "commands_log")  # Новая таблица для команд

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/facts', methods=['GET', 'POST'])
def facts():
    if request.method == 'POST':
        try:
            fact = request.form['fact']
            with open(FACTS_FILE, 'a', encoding='utf-8') as f:
                f.write(fact + '\n')
            return redirect(url_for('facts'))
        except Exception as e:
            return f"Error saving fact: {e}"
    try:
        with open(FACTS_FILE, 'r', encoding='utf-8') as f:
            facts = f.readlines()
    except Exception as e:
        facts = []
        print(f"Error reading facts: {e}")
    return render_template('facts.html', facts=facts)


@app.route('/hello', methods=['GET', 'POST'])
def hello():
    if request.method == 'POST':
        try:
            greeting = request.form['greeting']
            with open(HELLO_FILE, 'a', encoding='utf-8') as f:
                f.write(greeting + '\n')
            return redirect(url_for('hello'))
        except Exception as e:
            return f"Error saving greeting: {e}"
    try:
        with open(HELLO_FILE, 'r', encoding='utf-8') as f:
            greetings = f.readlines()
    except Exception as e:
        greetings = []
        print(f"Error reading greetings: {e}")
    return render_template('hello.html', greetings=greetings)


@app.route('/users')
def all_users():
    try:
        # Получаем всех пользователей
        df_users = users_table.fetch_all()
        users = df_users.to_dict(orient="records")
        with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
            file.write("1" + "\n")
        # Преобразуем строки в правильную кодировку
        for user in users:
            for key, value in user.items():
                if isinstance(value, str):
                    user[key] = value.encode('utf-8', errors='ignore').decode('utf-8')
        with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
            file.write("2" + "\n")
        # Для каждого пользователя собираем связанные данные
        for user in users:
            user_id = user['user_id']

            # Получаем сообщения пользователя
            df_messages = messages_table.fetch_all()
            user_messages = df_messages[df_messages['user_id'] == user_id]
            with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
                file.write("2.1" + "\n")
            user['messages'] = user_messages.to_dict(orient="records")
            with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
                file.write("2.2" + "\n")
            # Получаем игры пользователя
            df_games = games_table.fetch_all()
            user_games = df_games[df_games['user_id'] == user_id]
            user['games'] = user_games.to_dict(orient="records")
            with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
                file.write("2.3" + "\n")

        return render_template('users.html', users=users)
    except Exception as e:
        with open("C:\\Users\\lewdm\\Desktop\\zxc.txt", "a") as file:
            file.write(str(e) + "\n")
        return f"Error fetching users: {e}"


@app.route('/message_statistics')
def message_statistics():
    try:
        # Fetch all commands
        df_commands = commands_log_table.fetch_all()

        # Apply filters
        user_id_filter = request.args.get('user_id')
        command_filter = request.args.get('command')
        date_filter = request.args.get('date')

        if user_id_filter:
            df_commands = df_commands[df_commands['user_id'] == int(user_id_filter)]
        if command_filter:
            df_commands = df_commands[df_commands['command'].str.contains(command_filter, case=False, na=False)]
        if date_filter:
            df_commands['timestamp'] = df_commands['timestamp'].astype(str)
            df_commands = df_commands[df_commands['timestamp'].str.startswith(date_filter)]

        # Calculate statistics
        total_commands = len(df_commands)
        command_counts = df_commands.groupby('user_id').size().reset_index(name='command_count')
        top_users = command_counts.sort_values(by='command_count', ascending=False).head(5)

        df_commands['timestamp'] = df_commands['timestamp'].astype(str)
        df_commands['date'] = df_commands['timestamp'].str[:10]
        daily_counts = df_commands.groupby('date').size().reset_index(name='daily_command_count')

        return render_template('message_statistics.html', 
                               total_commands=total_commands,
                               top_users=top_users.to_dict(orient='records'),
                               daily_counts=daily_counts.to_dict(orient='records'),
                               commands=df_commands.to_dict(orient='records'))
    except Exception as e:
        return f"Error fetching message statistics: {e}"

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    try:
        users_table.delete_row("user_id", user_id)
        return redirect(url_for('all_users'))
    except Exception as e:
        return f"Error deleting user: {e}"


def run_bot():
    bot.polling(none_stop=True)  # Запуск Telegram-бота

if __name__ == '__main__':
    # Запуск Telegram-бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()

    # Запуск Flask приложения
    app.run(debug=True, use_reloader=False)