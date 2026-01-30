import os
import socket
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# 環境変数から設定を取得（デフォルト値も設定可能）
TV_IP = os.getenv("TV_IP", "192.168.10.24")
TV_PORT = int(os.getenv("TV_PORT", 10002))
TV_ID = os.getenv("TV_ID", "admin")
TV_PASS = os.getenv("TV_PASS", "password")

def send_aquos_command(command, param):
    cmd_full = f"{command:<4}{param:<4}\r"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5.0)
            s.connect((TV_IP, TV_PORT))
            
            # 認証
            time.sleep(0.5)
            s.sendall(f"{TV_ID}\n".encode())
            time.sleep(0.5)
            s.sendall(f"{TV_PASS}\n".encode())
            time.sleep(0.5)
            
            # バッファを一度クリア
            if s.pending() if hasattr(s, 'pending') else True: 
                s.recv(1024)
            
            # コマンド送信
            s.sendall(cmd_full.encode())
            response = s.recv(1024).decode().strip()
            return True, response
    except Exception as e:
        return False, str(e)

@app.route('/tv', methods=['GET'])
def control_tv():
    cmd = request.args.get('cmd')
    val = request.args.get('val', '') # valがなくても空文字で埋める
    success, res = send_aquos_command(cmd, val)
    return jsonify({"status": "ok" if success else "error", "tv_response": res})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)