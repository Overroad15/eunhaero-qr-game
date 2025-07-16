from flask import Flask, request, render_template_string
import os
import csv
from datetime import datetime

app = Flask(__name__)
log_file = "logs.csv"
max_winners = 10

result_html = '''
<html>
    <body style="text-align:center;">
        <h1>{{ message }}</h1>
        <img src="{{ image_url }}" width="300"><br><br>
        <p>접속 IP: {{ ip }}</p>
    </body>
</html>
'''

def log_visit(ip, result):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, ip, result])

def has_played(ip):
    if not os.path.exists(log_file):
        return False
    with open(log_file, "r", encoding='utf-8') as f:
        for row in csv.reader(f):
            if ip == row[1]:
                return True
    return False

def get_winner_count():
    if not os.path.exists(log_file):
        return 0
    count = 0
    with open(log_file, "r", encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 3 and row[2] == "당첨":
                count += 1
    return count

@app.route("/")
def play():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if has_played(ip):
        return render_template_string(result_html,
            message="⚠️ 이미 참여하셨습니다. 한 번만 도전할 수 있어요!",
            image_url="/static/lose.png",
            ip=ip
        )

    winner_count = get_winner_count()

    if winner_count < max_winners:
        result = "당첨"
        image = "/static/winner.png"
        message = f"🎉 축하합니다! {winner_count + 1}번째 은혜로 보물 당첨자입니다! 🎉"
    else:
        result = "꽝"
        image = "/static/lose.png"
        message = "😢 아쉽지만 당첨자 10명이 모두 나왔습니다."

    log_visit(ip, result)

    return render_template_string(result_html,
        message=message,
        image_url=image,
        ip=ip
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
