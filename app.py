print("BON FICHIER LANCÉ")
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = "secretkey"
import os

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("postgresql://historique_gk_traquer_user:SnUomHF0JxEXFi7bFvWRf9q8BXMshxnp@dpg-d7l4rf4m0tmc73b1ffk0-a/historique_gk_traquer")

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

    nickname = db.Column(db.String(100))
    bio = db.Column(db.Text)
    experience = db.Column(db.String(200))
    avatar = db.Column(db.String(200))

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer)
    shots = db.Column(db.Integer)
    saves = db.Column(db.Integer)
    goals = db.Column(db.Integer)
    rating = db.Column(db.Float)
    pen_saved = db.Column(db.Integer, default=0)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return redirect("/login")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])

        if User.query.filter_by(username=username).first():
            return "Username already exists"

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/dashboard")
@login_required
def dashboard():

    matches = Match.query.filter_by(user_id=current_user.id).all()
    match_count = len(matches)

    shots = sum(m.shots for m in matches)
    saves = sum(m.saves for m in matches)
    goals = sum(m.goals for m in matches)

    save_pct = (saves / shots * 100) if shots else 0

    clean_sheets = sum(1 for m in matches if m.goals == 0)
    clutch = sum(1 for m in matches if m.saves >= 8)
    pen = sum(m.pen_saved for m in matches)

    return render_template(
    "dashboard.html",
    matches=matches,
    save_pct=round(save_pct,1),
    shots=shots,
    goals=goals,
    clean_sheets=clean_sheets,
    clutch=clutch,
    pen=pen,
    match_count=match_count
)
    

@app.route("/add_match", methods=["GET","POST"])
@login_required
def add_match():

    if request.method == "POST":

        shots = int(request.form["shots"])
        saves = int(request.form["saves"])
        goals = int(request.form["goals"])
        rating = float(request.form["rating"])
        pen_saved = int(request.form.get("pen_saved",0))

        if saves > shots:
            return "Erreur : saves > shots"

        match = Match(
            user_id=current_user.id,
            shots=shots,
            saves=saves,
            goals=goals,
            rating=rating,
            pen_saved=pen_saved
        )

        db.session.add(match)
        db.session.commit()

        return redirect("/dashboard")

    return render_template("add_match.html")

@app.route("/leaderboard")
def leaderboard():

    users = User.query.all()
    data = []

    for u in users:
        matches = Match.query.filter_by(user_id=u.id).all()

        shots = sum(m.shots for m in matches)
        saves = sum(m.saves for m in matches)

        pct = (saves / shots * 100) if shots else 0

        data.append({
            "name": u.username,
            "save_pct": round(pct,1)
        })

    data = sorted(data, key=lambda x: x["save_pct"], reverse=True)

    return render_template("leaderboard.html", data=data)

@app.route("/profile/<username>")
def profile(username):

    user = User.query.filter_by(username=username).first()

    matches = Match.query.filter_by(user_id=user.id).all()

    shots = sum(m.shots for m in matches)
    saves = sum(m.saves for m in matches)
    goals = sum(m.goals for m in matches)

    save_pct = (saves/shots*100) if shots else 0
    match_count = len(matches)

    return render_template(
        "profile.html",
        player=user,
        matches=len(matches),
        save_pct=round(save_pct,1),
        shots=shots,
        goals=goals
    )


@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(host="0.0.0.0", port=10000)