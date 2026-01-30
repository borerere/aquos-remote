import os
import socket
import time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# 環境変数
TV_IP = os.getenv("TV_IP", "192.168.10.24")
TV_PORT = int(os.getenv("TV_PORT", 10002))
TV_ID = os.getenv("TV_ID", "admin")
TV_PASS = os.getenv("TV_PASS", "password")

# シンプルなリモコンUI（HTML/CSS/JS）
REMOTE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AQUOS Remote</title>
    <style>
        body { font-family: sans-serif; display: flex; flex-direction: column; align-items: center; background: #f0f0f0; }
        .btn { width: 150px; padding: 15px; margin: 10px; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; color: white; transition: 0.2s; }
        .btn-pwr { background: #e74c3c; }
        .btn-vol { background: #3498db; }
        .btn-inp { background: #f1c40f; color: black; }
        .btn:active { transform: scale(0.95); opacity: 0.8; }
    </style>
</head>
<body>
    <h2>AQUOS Controller</h2>
    <button class="btn btn-pwr" onclick="send('POWR', '0')">Power OFF</button>
    <button class="btn btn-vol" onclick="send('VOLM', '15')">Volume 15</button>
    <button class="btn btn-inp" onclick="send('IAV0', '4')">Input 4 (HDMI)</button>
    <div id="status" style="margin-top: 20px; color: #666;"></div>

    <script>
        function send(cmd, val) {
            const status = document.getElementById('status');
            status.innerText = "Sending...";
            fetch(`/tv?cmd=${cmd}&val=${val}`)
                .then(r => r.json())
                .then(data => { status.innerText = "Result: " + data.status; })
                .catch(e => { status.innerText = "Error: " + e; });
        }
    </script>
</body>
</html>
"""

def send_aquos_command(command, param):
    cmd_full = f"{command:<4}{param:<4}\r"
    # リトライ回数を設定
    for attempt in range(3):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3.0) # タイムアウトを少し短くして回転を速める
                s.connect((TV_IP, TV_PORT))
                
                # ログイン処理
                time.sleep(0.2)
                s.sendall(f"{TV_ID}\n".encode())
                time.sleep(0.2)
                s.sendall(f"{TV_PASS}\n".encode())
                time.sleep(0.5) # 認証後の安定待ち

                # 受信バッファを空にする（ゴミデータの掃除）
                s.setblocking(False)
                try:
                    while s.recv(1024): pass
                except:
                    pass
                s.setblocking(True)

                # コマンド送信
                s.sendall(cmd_full.encode())
                response = s.recv(1024).decode().strip()
                
                # OKかERRが返ってくれば成功として終了
                if response:
                    return True, response
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(1.0) # 少し待ってからリトライ
            continue
            
    return False, "Timeout after retries"

@app.route('/')
def index():
    return render_template_string(REMOTE_HTML)

@app.route('/tv', methods=['GET'])
def control_tv():
    cmd = request.args.get('cmd')
    val = request.args.get('val', '')
    success, res = send_aquos_command(cmd, val)
    return jsonify({"status": "ok" if success else "error", "tv_response": res})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)