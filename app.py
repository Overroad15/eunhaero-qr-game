from flask import Flask, request, render_template_string, session, redirect, url_for, send_file
import os
import csv
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = "은혜로보물찾기_비밀키_아무거나!"

log_file = "logs.csv"
max_winners = 10
admin_id = "overroad15"
admin_pw = "gangking15"

# 결과 페이지 템플릿
result_html = '''
<html>
    <body style="text-align:center;">
        <h1>{{ message }}</h1>
        <img src="{{ image_url }}" width="600"><br><br>
        <p>당신의 세션 ID: {{ sid }}</p>
        {% if winner %}
        <form method="post" action="/submit_info">
            📱 전화번호: <input type="text" name="phone" required><br><br>
            <input type="hidden" name="sid" value="{{ sid }}">
            <p>⚠️전화번호를 넣어야 당첨이 확정됩니다!</p>
            <input type="submit" value="전화번호 제출">
        </form>
        {% endif %}
    </body>
</html>
'''

# 로그 기록
def log_visit(session_id, result, phone="", email=""):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(log_file, "a", newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([now, session_id, result, phone, email])

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
    session_id = session.get("sid")
    if not session_id:
        session_id = os.urandom(8).hex()
        session["sid"] = session_id

    if has_played(session_id):
        return render_template_string(result_html,
            message="⚠️ 이미 참여하셨습니다. 한 번만 도전할 수 있어요!",
            image_url="/static/lose.png",
            sid=session_id,
            winner=False
        )

    winner_count = get_winner_count()

    if winner_count < max_winners:
        result = "당첨"
        image = "/static/winner.png"
        message = f"🎉 축하합니다! {winner_count + 1}번째 당첨자입니다! 🎉"
        session["pending_winner"] = True
        session["result"] = result
    else:
        result = "꽝"
        image = "/static/lose.png"
        message = "😢 아쉽지만 당첨자 10명이 모두 나왔습니다."
        log_visit(session_id, result)
        session["result"] = result

    return render_template_string(result_html,
        message=message,
        image_url=image,
        sid=session_id,
        winner=(result == "당첨")
    )

@app.route("/submit_info", methods=["POST"])
def submit_info():
    sid = request.form.get("sid") or session.get("sid")
    phone = request.form.get("phone")

    phone_regex = re.compile(r'^01[016789]-?\d{3,4}-?\d{4}$')
    if not phone_regex.match(phone):
        return render_template_string('''
            <html><body style="text-align:center;">
                <h2>⚠️ 잘못된 전화번호 형식입니다</h2>
                <p>예: 010-1234-5678 또는 01012345678</p><br>
                <form method="post" action="/submit_info">
                    📱 전화번호: <input type="text" name="phone" required><br><br>
                    <input type="hidden" name="sid" value="{{ sid }}">
                    <input type="submit" value="다시 제출하기">
                </form>
                <br><a href="/">🏠 홈으로</a>
            </body></html>
        ''', sid=sid)

    if session.get("pending_winner"):
        log_visit(sid, "당첨", phone, "")
        session.pop("pending_winner")

    return render_template_string('''
        <html><body style="text-align:center;">
            <h2>✅ 전화번호가 등록되었습니다!</h2>
            <p>📱 {{ phone }}</p><br>
            <a href="/">🏠 홈으로</a>
        </body></html>
    ''', phone=phone)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        uid = request.form.get("id")
        pw = request.form.get("pw")
        if uid == admin_id and pw == admin_pw:
            session["admin"] = True
            return redirect(url_for("winner_list"))
        else:
            return "<h3>❌ 로그인 실패. 다시 시도해주세요.</h3><a href='/admin'>돌아가기</a>"

    return '''
        <form method="post" style="text-align:center;">
            <h2>🔐 관리자 로그인</h2>
            ID: <input type="text" name="id"><br><br>
            PW: <input type="password" name="pw"><br><br>
            <input type="submit" value="로그인">
        </form>
    '''

@app.route("/winner-list")
def winner_list():
    if not session.get("admin"):
        return redirect(url_for("admin"))

    winners = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding='utf-8') as f:
            for row in csv.reader(f):
                if len(row) >= 3 and row[2] == "당첨":
                    winners.append(row)

    table = "<table border=1 style='margin:auto;'><tr><th>시간</th><th>세션</th><th>결과</th><th>전화번호</th></tr>"
    for row in winners:
        table += f"<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>"
    table += "</table>"

    return f'''
        <html><body style="text-align:center;">
            <h2>🎯 당첨자 목록 ({len(winners)}명)</h2>
            {table}
            <br><a href="/download-logs">📥 logs.csv 다운로드</a>
        </body></html>
    '''

@app.route("/download-logs")
def download_logs():
    if not session.get("admin"):
        return redirect(url_for("admin"))
    return send_file(log_file, as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
