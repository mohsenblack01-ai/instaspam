from flask import Flask, render_template, request, redirect, url_for
from instagrapi import Client
import threading
import time
import random

app = Flask(__name__)

# Global status + LIVE LOGS
spam_status = {
    "running": False,
    "total_sent": 0,
    "status": "",
    "threads": 0,
    "logs": []          # ← YEH NAYA HAI – LIVE CONSOLE
}

configs = {
    "username": "", "password": "", "thread_id": 0,
    "messages": [], "delay": 8.0,
    "cycle_count": 50, "cycle_break": 35,
    "threads": 3
}

clients = []
threads_list = []

def add_log(message):
    spam_status["logs"].append(f"[{time.strftime('%H:%M:%S')}] {message}")
    if len(spam_status["logs"]) > 500:      # max 500 lines rakhega
        spam_status["logs"] = spam_status["logs"][-500:]

def spam_worker(client, thread_id, messages, delay, cycle_count, cycle_break):
    sent = 0
    while spam_status["running"]:
        try:
            msg = random.choice(messages)
            client.direct_send(msg, thread_ids=[thread_id])
            sent += 1
            spam_status["total_sent"] += 1
            add_log(f"Sent #{spam_status['total_sent']} → {msg[:60]}{'...' if len(msg)>60 else ''}")

            if sent % cycle_count == 0:
                add_log(f"Break {cycle_break}s after {cycle_count} messages...")
                time.sleep(cycle_break)

            time.sleep(delay * random.uniform(0.9, 1.4))
        except Exception as e:
            add_log(f"Error → {str(e)[:100]}")
            time.sleep(30)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        spam_status["running"] = False
        time.sleep(2)
        spam_status["logs"].clear()

        # Form data
        configs["username"] = request.form['username']
        configs["password"] = request.form['password']
        configs["thread_id"] = int(request.form['thread_id'])
        configs["messages"] = [m.strip() for m in request.form['messages'].split('\n') if m.strip()]
        configs["delay"] = float(request.form['delay'])
        configs["cycle_count"] = int(request.form['cycle_count'])
        configs["cycle_break"] = int(request.form['cycle_break'])
        configs["threads"] = int(request.form['threads'])

        # Start spam
        spam_status["running"] = True
        spam_status["total_sent"] = 0
        spam_status["status"] = "RUNNING 24×7"
        spam_status["threads"] = configs["threads"]
        add_log("SPAMMER STARTED BY USER")
        threads_list.clear()
        clients.clear()

        for i in range(configs["threads"]):
            client = Client()
            client.delay_range = [1, 5]
            try:
                client.login(configs["username"], configs["password"])
                add_log(f"Thread {i+1} logged in successfully")
                clients.append(client)
                t = threading.Thread(target=spam_worker, args=(client, configs["thread_id"], configs["messages"],
                                                             configs["delay"], configs["cycle_count"], configs["cycle_break"]), daemon=True)
                t.start()
                threads_list.append(t)
            except Exception as e:
                add_log(f"Thread {i+1} login failed → {str(e)[:80]}")

    return render_template('index.html',
                         status=spam_status["status"],
                         total_sent=spam_status["total_sent"],
                         threads=spam_status["threads"],
                         logs=spam_status["logs"])

@app.route('/stop')
def stop():
    spam_status["running"] = False
    add_log("SPAM STOPPED BY USER")
    spam_status["status"] = "STOPPED"
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
