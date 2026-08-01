"""
routes/lotes.py — Gerenciamento de lotes (grupos de animais)

Um lote é um jeito de agrupar animais (ex: "Recria 2026", "Piquete 3")
pra facilitar a visão geral e pra lançar custos que valem pro grupo
inteiro (mão de obra, remédio aplicado em todo o lote, etc.).
"""

from flask import Blueprint, request, jsonify
from models import db, Lote, Animal

lotes_bp = Blueprint("lotes", __name__, url_prefix="/api")


@lotes_bp.route("/lotes", methods=["GET"])
def listar_lotes():
    lotes = Lote.query.all()
    return jsonify([l.to_dict() for l in lotes])


@lotes_bp.route("/lotes/<int:lote_id>", methods=["GET"])
def obter_lote(lote_id):
    lote = Lote.query.get_or_404(lote_id)
    dados = lote.to_dict()
    dados["animais"] = [a.to_dict(incluir_dieta=False) for a in lote.animais]
    return jsonify(dados)


@lotes_bp.route("/lotes", methods=["POST"])
def criar_lote():
    dados = request.get_json()
    try:
        lote = Lote(nome=dados["nome"], descricao=dados.get("descricao"))
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(lote)
    db.session.commit()
    return jsonify(lote.to_dict()), 201


@lotes_bp.route("/lotes/<int:lote_id>", methods=["PUT"])
def atualizar_lote(lote_id):
    lote = Lote.query.get_or_404(lote_id)
    dados = request.get_json()
    for campo in ["nome", "descricao"]:
        if campo in dados:
            setattr(lote, campo, dados[campo])
    db.session.commit()
    return jsonify(lote.to_dict())


@lotes_bp.route("/lotes/<int:lote_id>", methods=["DELETE"])
def remover_lote(lote_id):
    lote = Lote.query.get_or_404(lote_id)
    # animais do lote não são apagados — só ficam sem lote
    for animal in lote.animais:
        animal.lote_id = None
    db.session.delete(lote)
    db.session.commit()
    return jsonify({"ok": True})
