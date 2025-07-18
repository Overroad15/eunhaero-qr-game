from flask import Flask, request, render_template_string, session, make_response
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = "은혜로보물찾기_비밀키_아무거나!"  # 세션 암호화를 위한 필수값
log_file = "logs.csv"
max_winners = 10

result_html = '''
<html>git add .
    <body style="text-align:center;">
        <h1>{{ message }}</h1>
        <img src="{{ image_url }}" width="600"><br><br>
        <p>당신의 순번 ID: {{ sid }}</p>
    </body>
</html>
'''

def log_visit(session_id, result):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, session_id, result])

def has_played(session_id):
    try:
        with open(log_file, "r", encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 2 and row[1].strip() == session_id.strip():
                    return True
    except FileNotFoundError:
        return False
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
    # 세션 ID 생성 또는 기존 값 불러오기
    session_id = session.get("id")
    if not session_id:
        session_id = os.urandom(8).hex()
        session["id"] = session_id

    if has_played(session_id):
        return render_template_string(result_html,
            message="⚠️ 이미 참여하셨습니다. 한 번만 도전할 수 있어요!",
            image_url="/static/lose.png",
            sid=session_id
        )

    winner_count = get_winner_count()

    if winner_count < max_winners:
        result = "당첨"
        image = "/static/winner.png"
        message = f"🎉 축하합니다! {winner_count + 1}번째 당첨자입니다! 🎉"
    else:
        result = "꽝"
        image = "/static/lose.png"
        message = "😢 아쉽지만 당첨자 10명이 모두 나왔습니다."

    log_visit(session_id, result)

    return render_template_string(result_html,
        message=message,
        image_url=image,
        sid=session_id
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
