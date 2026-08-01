"""
app.py — Ponto de entrada do backend Flask

Como rodar:
    pip install -r requirements.txt
    python app.py

O servidor sobe em http://localhost:5000 com CORS liberado, pronto
pra ser consumido pelo front React (rodando em outra porta, ex: 5173/3000).

Na primeira execução, cria o arquivo rurapp.db (SQLite) automaticamente.
Rode `python seed_exigencias.py` depois pra popular as tabelas de
exigência nutricional (Embrapa/NRC) e alguns ingredientes de exemplo.
"""

from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from routes.manejo import manejo_bp
from routes.racao import racao_bp
from routes.lotes import lotes_bp
from routes.custos import custos_bp


def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rurapp.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)  # libera acesso do front React (outra origem/porta)

    db.init_app(app)

    app.register_blueprint(manejo_bp)
    app.register_blueprint(racao_bp)
    app.register_blueprint(lotes_bp)
    app.register_blueprint(custos_bp)

    @app.route("/api/health")
    def health_check():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
