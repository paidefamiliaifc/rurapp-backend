"""
app.py — Ponto de entrada do backend Flask

Como rodar LOCAL (no seu computador):
    pip install -r requirements.txt
    python app.py

Como rodar HOSPEDADO (ex: Render, Railway): a plataforma define as
variáveis de ambiente DATABASE_URL (banco Postgres) e PORT automaticamente,
e usa o Procfile pra iniciar com gunicorn. Nada a fazer manualmente.

Na primeira execução local, cria o arquivo rurapp.db (SQLite) automaticamente.
Rode `python seed_exigencias.py` depois pra popular as tabelas de
exigência nutricional (Embrapa/NRC) e alguns ingredientes de exemplo.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
from models import db
from routes.manejo import manejo_bp
from routes.racao import racao_bp
from routes.lotes import lotes_bp
from routes.custos import custos_bp


def create_app():
    app = Flask(__name__)

    # Se existir DATABASE_URL (fornecida pela hospedagem, ex: Render), usa
    # o banco Postgres hospedado. Senão, usa o SQLite local de sempre.
    database_url = os.environ.get("DATABASE_URL", "sqlite:///rurapp.db")
    # Render entrega a URL no formato antigo "postgres://" — o SQLAlchemy
    # moderno exige "postgresql://". Corrige isso automaticamente.
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    CORS(app)  # libera acesso do front end (outra origem/porta/domínio)

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


app = create_app()  # nível do módulo — necessário pro gunicorn achar "app:app" quando hospedado

if __name__ == "__main__":
    porta = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=porta)
