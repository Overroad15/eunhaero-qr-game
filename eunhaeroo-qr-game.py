from flask import Flask, request, redirect, render_template_string
import os
import csv
from datetime import datetime

app = Flask(__name__)
counter_file = "counter.txt"
log_file = "logs.csv"
max_winners = 10

form_html = '''
<html>
    <body style="text-align:center;">
        <h2>🎯 이메일을 입력하고 보물을 찾아보세요!</h2>
        <form method="post" action="/play">
            이메일: <input type="email" name="email" required><br><br>
            <input type="submit" value="도전하기">
        </form>
    </body>
</html>
'''

result_html = '''
<html>
    <body style="text-align:center;">
        <h1>{{ message }}</h1>
        <img src="{{ image_url }}" width="300"><br><br>
        <p>참여자 이메일: {{ email }}</p>
        <p>접속 IP: {{ ip }}</p>
    </body>
</html>
'''

def log_visit(ip, email, result):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, ip, email, result])

def has_played(ip, email):
    if not os.path.exists(log_file):
        return False
    with open(log_file, "r", encoding='utf-8') as f:
        for row in f:
            if ip in row or email in row:
                return True
    return False

def get_winner_count():
    if not os.path.exists(log_file):
        return 0
    count = 0
    with open(log_file, "r", encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 4 and row[3] == "당첨":
                count += 1
    return count

@app.route("/")
def index():
    return form_html

@app.route("/play", methods=["POST"])
def play():
    ip = request.remote_addr
    email = request.form.get("email")

    if has_played(ip, email):
        return render_template_string(result_html,
            message="⚠️ 이미 참여하셨습니다. 한 번만 도전할 수 있어요!",
            image_url="/static/lose.png",
            email=email,
            ip=ip
        )

    winner_count = get_winner_count()

    if winner_count < max_winners:
        result = "당첨"
        image = "/static/winner.png"
        message = f"🎉 축하합니다! {winner_count + 1}번째 보물 당첨자입니다! 🎉"
    else:
        result = "꽝"
        image = "/static/lose.png"
        message = "😢 아쉽지만 당첨자 10명이 모두 나왔습니다."

    log_visit(ip, email, result)

    return render_template_string(result_html,
        message=message,
        image_url=image,
        email=email,
        ip=ip
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))