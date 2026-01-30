import os
import socket
import time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

# 環境変数（192.168.10.200 用の設定）
TV_IP = os.getenv("TV_IP", "192.168.10.24") # ここは実際のTVのIPに合わせてください
TV_PORT = int(os.getenv("TV_PORT", 10002))
TV_ID = os.getenv("TV_ID", "admin")
TV_PASS = os.getenv("TV_PASS", "password")

REMOTE_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>AQUOS Expert Remote</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #1a1a1a; color: white; display: flex; flex-direction: column; align-items: center; margin: 0; padding: 20px; touch-action: manipulation; }
        .section { margin-bottom: 20px; width: 100%; max-width: 400px; display: grid; gap: 10px; }
        .btn { padding: 18px 5px; border: none; border-radius: 10px; font-size: 16px; font-weight: bold; cursor: pointer; color: white; background: #333; transition: transform 0.1s; }
        .btn:active { transform: scale(0.95); opacity: 0.8; }
        
        /* 電源ボタンの色分け */
        .pwr-on { background: #2ecc71; grid-column: span 1; } /* 緑 */
        .pwr-off { background: #e74c3c; grid-column: span 1; } /* 赤 */
        
        .blue { background: #2980b9; } .red { background: #c0392b; } .green { background: #27ae60; } .yellow { background: #f1c40f; color: black; }
        .nav { background: #444; } .enter { background: #777; }
        .grid-3 { grid-template-columns: repeat(3, 1fr); }
        .grid-4 { grid-template-columns: repeat(4, 1fr); }
        .status-bar { height: 25px; color: #888; font-size: 13px; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="status-bar" id="status">Ready</div>

    <div class="section grid-3">
        <button class="btn pwr-on" onclick="send('POWR', '1')">電源 ON</button>
        <button class="btn pwr-off" onclick="send('POWR', '0')">電源 OFF</button>
        <button class="btn" onclick="send('IAVD', '4')">入力 4</button>
    </div>

    <div class="section grid-3">
        <script>
            for(let i=1; i<=12; i++) {
                let ch = ("0" + i).slice(-2); 
                document.write(`<button class="btn" onclick="send('CTBD', '0${ch} ')">${i}</button>`);
            }
        </script>
    </div>

    <div class="section grid-3">
        <button class="btn" onclick="send('RKEY', '33')">音量＋</button>
        <button class="btn" onclick="send('RKEY', '32')">音量－</button>
        <button class="btn" onclick="send('RKEY', '31')">消音</button>
    </div>

    <div class="section grid-3">
        <div></div><button class="btn nav" onclick="send('RKEY', '41')">▲</button><div></div>
        <button class="btn nav" onclick="send('RKEY', '44')">◀</button>
        <button class="btn enter" onclick="send('RKEY', '40')">決定</button>
        <button class="btn nav" onclick="send('RKEY', '43')">▶</button>
        <div></div><button class="btn nav" onclick="send('RKEY', '42')">▼</button>
        <button class="btn nav" onclick="send('RKEY', '45')">戻る</button>
    </div>

    <div class="section grid-4">
        <button class="btn blue" onclick="send('RKEY', '52')">青</button>
        <button class="btn red" onclick="send('RKEY', '50')">赤</button>
        <button class="btn green" onclick="send('RKEY', '51')">緑</button>
        <button class="btn yellow" onclick="send('RKEY', '53')">黄</button>
    </div>

    <div class="section grid-3">
        <button class="btn" onclick="send('RKEY', '61')">戻る</button>
        <button class="btn" onclick="send('RKEY', '60')">再生</button>
        <button class="btn" onclick="send('RKEY', '62')">送り</button>
    </div>

    <script>
        function send(cmd, val) {
            const st = document.getElementById('status');
            st.innerText = "Sending " + cmd + "...";
            fetch(`/tv?cmd=${cmd}&val=${val}`)
                .then(r => r.json())
                .then(d => { st.innerText = d.status === "ok" ? "Success" : "Error"; })
                .catch(e => { st.innerText = "Failed"; });
        }
    </script>
</body>
</html>
"""

def send_aquos_command(command, param):
    # 【修正！】\\r を \r に、\\n を \n に戻します
    cmd_full = f"{command:<4}{param:<4}\r" 
    for attempt in range(3):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(3.0)
                s.connect((TV_IP, TV_PORT))
                time.sleep(0.2)
                s.sendall(f"{TV_ID}\n".encode()) # ここも \n に修正
                time.sleep(0.2)
                s.sendall(f"{TV_PASS}\n".encode()) # ここも \n に修正
                time.sleep(0.5)
                
                # バッファクリア
                s.setblocking(False)
                try:
                    while s.recv(1024): pass
                except:
                    pass
                s.setblocking(True)

                s.sendall(cmd_full.encode())
                response = s.recv(1024).decode().strip()
                if response:
                    return True, response
        except Exception as e:
            time.sleep(1.0)
            continue
    return False, "Timeout"

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