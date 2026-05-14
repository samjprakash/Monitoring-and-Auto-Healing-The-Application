from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "monitoring-secret-key"

# ---------------- CONFIG ----------------
USERNAME = "admin"
PASSWORD = "admin123"

GRAFANA_URL = "http://127.0.0.1:57787/"
PROMETHEUS_URL = " http://127.0.0.1:60299/"
METRICS_URL = "http://127.0.0.1:64885/"
ALERTMANAGER_URL = "http://127.0.0.1:56520/"

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == USERNAME and password == PASSWORD:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")


# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    queries = {
        "total": 'count(kube_pod_info)',
        "running": 'count(kube_pod_status_phase{phase="Running"} == 1)',
        "failed": 'count(kube_pod_status_phase{phase="Failed"} == 1)',
        "pending": 'count(kube_pod_status_phase{phase="Pending"} == 1)'
    }

    pods = {}

    for key, query in queries.items():
        try:
            response = requests.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=3
            )
            result = response.json()
            pods[key] = int(float(result["data"]["result"][0]["value"][1]))
        except Exception:
            pods[key] = 0

    return render_template(
        "dashboard.html",
        user=session["user"],
        grafana_url=GRAFANA_URL,
        prometheus_url=PROMETHEUS_URL,
        metrics_url=METRICS_URL,
        pods=pods
    )


# ---------------- ALERT API ----------------
@app.route("/api/alerts")
def get_alerts():
    try:
        r = requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts", timeout=5)
        alerts = r.json()

        active_alerts = []
        for alert in alerts:
            if alert["status"]["state"] == "active":
                active_alerts.append({
                    "name": alert["labels"].get("alertname", "Unknown"),
                    "severity": alert["labels"].get("severity", "unknown"),
                    "namespace": alert["labels"].get("namespace", "N/A")
                })

        return {
            "count": len(active_alerts),
            "alerts": active_alerts
        }

    except Exception as e:
        return {"count": 0, "alerts": [], "error": str(e)}


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))


# ---------------- AUTO-HEALING (NEW – ADDED ONLY) ----------------
from kubernetes import client, config


def restart_pod(namespace, pod_name):
    try:
        config.load_kube_config()   # uses ~/.kube/config (Minikube)
        v1 = client.CoreV1Api()
        v1.delete_namespaced_pod(
            name=pod_name,
            namespace=namespace
        )
        return True
    except Exception as e:
        print("Auto-heal error:", e)
        return False


@app.route("/api/auto-heal")
def auto_heal():
    try:
        r = requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts", timeout=5)
        alerts = r.json()

        actions = []

        for alert in alerts:
            if alert["status"]["state"] != "active":
                continue

            name = alert["labels"].get("alertname")
            namespace = alert["labels"].get("namespace", "default")
            pod = alert["labels"].get("pod")

            if name == "KubePodNotReady" and pod:
                if restart_pod(namespace, pod):
                    actions.append(f"Restarted pod {pod}")

        return {"actions": actions}

    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
