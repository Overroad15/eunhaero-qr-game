from flask import Flask, request, render_template_string, session, redirect, send_file
import os, csv, re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "은혜로보물찾기_비밀키_아무거나!"
log_file = "logs.csv"
max_winners = 10
admin_id = "overroad15"
admin_pw = "gangking15"

# ----------- HTML 템플릿 -----------

result_html = '''
<html>
<body style="text-align:center;">
    <h1>{{ message }}</h1>
    <img src="{{ image_url }}" width="600"><br><br>
    <p>당신의 ID: {{ sid }}</p>
    {% if is_winner %}
        <form method="post" action="/submit_phone">
            📱 전화번호 입력: <input type="text" name="phone" required><br><br>
            <input type="hidden" name="sid" value="{{ sid }}">
            <input type="submit" value="보상 받기">
        </form>
    {% endif %}
</body>
</html>
'''

thanks_html = '''
<html>
<body style="text-align:center;">
    <h2>✅ 전화번호가 등록되었습니다!</h2>
    <p>📱 {{ phone }}</p>
    <a href="/">🏠 홈으로</a>
</body>
</html>
'''

login_html = '''
<html>
<body style="text-align:center;">
    <h2>🔐 관리자 로그인</h2>
    <form method="post" action="/admin-login">
        ID: <input type="text" name="id"><br>
        PW: <input type="password" name="pw"><br><br>
        <input type="submit" value="로그인">
    </form>
</body>
</html>
'''

winner_list_html = '''
<html>
<body style="text-align:center;">
    <h2>🏆 당첨자 리스트 (총 {{ count }}명)</h2>
    <a href="/download-logs">📥 logs.csv 다운로드</a><br><br>
    <table border="1" cellpadding="10" style="margin:auto;">
        <tr><th>날짜</th><th>세션 ID</th><th>전화번호</th></tr>
        {% for w in winners %}
            <tr><td>{{ w[0] }}</td><td>{{ w[1] }}</td><td>{{ w[2] }}</td></tr>
        {% endfor %}
    </table>
    <br><a href="/logout">🔓 로그아웃</a>
</body>
</html>
'''

# ----------- 로직 함수 -----------

def log_visit(session_id, result, phone=None):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    row = [now, session_id, result]
    if phone:
        row.append(phone)
    with open(log_file, "a", newline='', encoding='utf-8') as f:
        csv.writer(f).writerow(row)

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

def is_valid_phone(phone):
    # 한국 휴대폰 번호 정규식 (010-1234-5678 또는 01012345678)
    return re.match(r'^01[016789]-?\d{3,4}-?\d{4}$', phone)

# ----------- 메인 라우트 -----------

@app.route("/")
def play():
    session_id = session.get("id")
    if not session_id:
        session_id = os.urandom(8).hex()
        session["id"] = session_id

    if has_played(session_id):
        return render_template_string(result_html,
            message="⚠️ 이미 참여하셨습니다. 한 번만 도전할 수 있어요!",
            image_url="/static/lose.png",
            sid=session_id,
            is_winner=False
        )

    winner_count = get_winner_count()
    if winner_count < max_winners:
        result = "당첨"
        image = "/static/winner.png"
        message = f"🎉 축하합니다! {winner_count + 1}번째 당첨자입니다! 🎉"
        is_winner = True
    else:
        result = "꽝"
        image = "/static/lose.png"
        message = "😢 아쉽지만 당첨자 10명이 모두 나왔습니다."
        is_winner = False

    log_visit(session_id, result)
    return render_template_string(result_html,
        message=message,
        image_url=image,
        sid=session_id,
        is_winner=is_winner
    )

# ----------- 전화번호 등록 -----------

@app.route("/submit_phone", methods=["POST"])
def submit_phone():
    sid = request.form.get("sid")
    phone = request.form.get("phone")

    if not is_valid_phone(phone):
        return f"<h3>⚠️ 잘못된 전화번호 형식입니다.<br>📱 예시: 010-1234-5678</h3>"

    updated_rows = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[1] == sid and row[2] == "당첨":
                    if len(row) < 4:
                        row.append(phone)
                updated_rows.append(row)
        with open(log_file, "w", newline='', encoding='utf-8') as f:
            csv.writer(f).writerows(updated_rows)

    return render_template_string(thanks_html, phone=phone)

# ----------- 관리자 로그인 -----------

@app.route("/admin", methods=["GET"])
def admin_login_form():
    return render_template_string(login_html)

@app.route("/admin-login", methods=["POST"])
def admin_login():
    uid = request.form.get("id")
    pw = request.form.get("pw")
    if uid == admin_id and pw == admin_pw:
        session["admin"] = True
        return redirect("/winner-list")
    else:
        return "❌ 로그인 실패"

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/admin")

# ----------- 관리자 당첨자 리스트 -----------

@app.route("/winner-list")
def winner_list():
    if not session.get("admin"):
        return redirect("/admin")

    winners = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == "당첨":
                    phone = row[3] if len(row) >= 4 else "📭 미입력"
                    winners.append((row[0], row[1], phone))
    return render_template_string(winner_list_html, winners=winners, count=len(winners))

# ----------- 로그 파일 다운로드 -----------

@app.route("/download-logs")
def download_logs():
    if not session.get("admin"):
        return redirect("/admin")
    return send_file(log_file, as_attachment=True)

# ----------- 실행 -----------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
