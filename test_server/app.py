import time
import configparser
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "test-secret-key"

CREDENTIALS = {"admin": "password123"}
PROPERTIES_FILE = Path(__file__).parent / "test.properties"


def load_properties() -> configparser.ConfigParser:
    """Read test.properties fresh on every call so changes apply without restart."""
    cfg = configparser.ConfigParser(inline_comment_prefixes=("#",))
    content = "[default]\n" + PROPERTIES_FILE.read_text()
    cfg.read_string(content)
    return cfg


@app.route("/")
def index():
    if "user" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("home"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        cfg = load_properties()
        delay = cfg.getfloat("default", "login_delay_seconds", fallback=0)
        if delay > 0:
            print(f"[test server] Simulating login delay: {delay}s")
            time.sleep(delay)

        if CREDENTIALS.get(username) == password:
            session["user"] = username
            return redirect(url_for("home"))
        error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", user=session["user"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/users/<int:user_id>/upload", methods=["GET", "POST"])
def upload(user_id: int):
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("file")
        cfg = load_properties()
        should_succeed = cfg.getboolean("default", "upload_success", fallback=True)

        if not file or file.filename == "":
            session["upload_result"] = {"success": False, "message": "No file selected."}
        elif not should_succeed:
            session["upload_result"] = {
                "success": False,
                "message": f'Upload of "{file.filename}" failed (simulated failure).',
            }
        else:
            session["upload_result"] = {
                "success": True,
                "message": f'"{file.filename}" uploaded successfully.',
            }

        time.sleep(2)
        return redirect(url_for("result", user_id=user_id))

    return render_template("upload.html", user=session["user"], user_id=user_id)


@app.route("/users/<int:user_id>/result")
def result(user_id: int):
    if "user" not in session:
        return redirect(url_for("login"))

    outcome = session.pop("upload_result", None)
    if outcome is None:
        return redirect(url_for("upload", user_id=user_id))

    return render_template("result.html", user_id=user_id, outcome=outcome)


if __name__ == "__main__":
    app.run(debug=True, port=8080)
