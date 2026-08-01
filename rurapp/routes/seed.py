"""
routes/seed.py — Popular o banco pela web (útil pra hospedagem gratuita,
como o Render, onde o Shell não está disponível no plano free).

Visitar /api/seed no navegador roda a mesma lógica do seed_exigencias.py.
É seguro visitar mais de uma vez — itens que já existem são ignorados.
"""

from flask import Blueprint, jsonify
from models import db, Ingrediente, ExigenciaNutricional
from seed_data import INGREDIENTES_EXEMPLO, EXIGENCIAS_EXEMPLO

seed_bp = Blueprint("seed", __name__, url_prefix="/api")


@seed_bp.route("/reset-db", methods=["GET"])
def resetar_banco():
    """
    Apaga e recria TODAS as tabelas do zero, seguindo a versão mais
    recente de models.py. Útil quando a estrutura do banco muda
    (ex: um campo de texto precisou ficar maior) — o create_all()
    normal NÃO altera tabelas que já existem, só cria as que faltam.

    ⚠️ Isso apaga todos os dados salvos (animais, pesagens etc.).
    Rode /api/seed de novo depois pra repopular ingredientes/exigências.
    """
    db.drop_all()
    db.create_all()
    return jsonify({"ok": True, "mensagem": "Banco recriado do zero. Agora visite /api/seed pra popular os dados de exemplo."})


@seed_bp.route("/seed", methods=["GET"])
def rodar_seed():
    criados_ing = 0
    for dados in INGREDIENTES_EXEMPLO:
        if not Ingrediente.query.filter_by(nome=dados["nome"]).first():
            db.session.add(Ingrediente(**dados))
            criados_ing += 1

    criados_exig = 0
    for dados in EXIGENCIAS_EXEMPLO:
        existe = ExigenciaNutricional.query.filter_by(
            especie=dados["especie"], fase_de_vida=dados["fase_de_vida"]
        ).first()
        if not existe:
            db.session.add(ExigenciaNutricional(**dados))
            criados_exig += 1

    db.session.commit()
    return jsonify({
        "ok": True,
        "ingredientes_criados": criados_ing,
        "exigencias_criadas": criados_exig,
        "mensagem": "Pode fechar essa aba e voltar pro sistema — os dados já foram inseridos.",
    })
