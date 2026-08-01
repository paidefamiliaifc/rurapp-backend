"""
routes/manejo.py — Módulo 1: Diário de Manejo Digital

Endpoints REST para cadastro de animais, registro de pesagens
e histórico sanitário com alertas de vencimento.
"""

from datetime import date, datetime
from flask import Blueprint, request, jsonify
from models import db, Animal, Pesagem, RegistroSanitario

manejo_bp = Blueprint("manejo", __name__, url_prefix="/api")


def _parse_date(s):
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


# ---------- Animais ----------

@manejo_bp.route("/animais", methods=["GET"])
def listar_animais():
    animais = Animal.query.filter_by(ativo=True).all()
    return jsonify([a.to_dict() for a in animais])


@manejo_bp.route("/animais/<int:animal_id>", methods=["GET"])
def obter_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    return jsonify(animal.to_dict())


@manejo_bp.route("/animais", methods=["POST"])
def criar_animal():
    """
    Campos: nome_identificador é obrigatório (pode ser o brinco/código, ou
    um apelido — o que você já usa hoje continua funcionando). Os campos
    novos (codigo_identificacao, nome, lote_id, mae_id, pai_id) são opcionais.
    """
    dados = request.get_json()
    try:
        animal = Animal(
            codigo_identificacao=dados.get("codigo_identificacao"),
            nome=dados.get("nome"),
            nome_identificador=dados["nome_identificador"],
            especie=dados["especie"],
            raca=dados.get("raca"),
            sexo=dados.get("sexo"),
            data_nascimento=_parse_date(dados["data_nascimento"]),
            peso_nascimento_kg=dados.get("peso_nascimento_kg"),
            lote_id=dados.get("lote_id"),
            mae_id=dados.get("mae_id"),
            pai_id=dados.get("pai_id"),
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(animal)
    db.session.commit()
    return jsonify(animal.to_dict()), 201


@manejo_bp.route("/animais/<int:animal_id>", methods=["PUT"])
def atualizar_animal(animal_id):
    """
    Editar dados do animal (código, nome, raça, sexo, lote, pai/mãe...).
    Envie só os campos que quer mudar.
    """
    animal = Animal.query.get_or_404(animal_id)
    dados = request.get_json()
    for campo in [
        "codigo_identificacao", "nome", "nome_identificador", "especie", "raca",
        "sexo", "peso_nascimento_kg", "lote_id", "mae_id", "pai_id", "ativo",
    ]:
        if campo in dados:
            setattr(animal, campo, dados[campo])
    if "data_nascimento" in dados:
        animal.data_nascimento = _parse_date(dados["data_nascimento"])
    db.session.commit()
    return jsonify(animal.to_dict())


@manejo_bp.route("/animais/<int:animal_id>", methods=["DELETE"])
def desativar_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    animal.ativo = False
    db.session.commit()
    return jsonify({"ok": True})


# ---------- Pesagens ----------

@manejo_bp.route("/animais/<int:animal_id>/pesagens", methods=["GET"])
def listar_pesagens(animal_id):
    Animal.query.get_or_404(animal_id)
    pesagens = (
        Pesagem.query.filter_by(animal_id=animal_id).order_by(Pesagem.data).all()
    )
    return jsonify([p.to_dict() for p in pesagens])


@manejo_bp.route("/animais/<int:animal_id>/pesagens", methods=["POST"])
def registrar_pesagem(animal_id):
    Animal.query.get_or_404(animal_id)
    dados = request.get_json()
    try:
        pesagem = Pesagem(
            animal_id=animal_id,
            data=_parse_date(dados.get("data")) or date.today(),
            peso_kg=dados["peso_kg"],
            observacao=dados.get("observacao"),
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(pesagem)
    db.session.commit()
    return jsonify(pesagem.to_dict()), 201


# ---------- Sanidade ----------

@manejo_bp.route("/animais/<int:animal_id>/sanidade", methods=["GET"])
def listar_sanidade(animal_id):
    Animal.query.get_or_404(animal_id)
    registros = RegistroSanitario.query.filter_by(animal_id=animal_id).all()
    return jsonify([r.to_dict() for r in registros])


@manejo_bp.route("/animais/<int:animal_id>/sanidade", methods=["POST"])
def registrar_sanidade(animal_id):
    Animal.query.get_or_404(animal_id)
    dados = request.get_json()
    try:
        registro = RegistroSanitario(
            animal_id=animal_id,
            tipo=dados["tipo"],
            produto=dados["produto"],
            data_aplicacao=_parse_date(dados["data_aplicacao"]),
            data_proxima_dose=_parse_date(dados.get("data_proxima_dose")),
            observacao=dados.get("observacao"),
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(registro)
    db.session.commit()
    return jsonify(registro.to_dict()), 201


@manejo_bp.route("/alertas-sanitarios", methods=["GET"])
def alertas_sanitarios():
    """
    Retorna todos os registros sanitários vencidos ou a vencer em até 7 dias,
    de todos os animais ativos. Pensado pra alimentar um card de alerta
    na tela inicial do app.
    """
    registros = RegistroSanitario.query.all()
    alertas = [
        r.to_dict() for r in registros
        if r.dias_para_vencer() is not None and r.dias_para_vencer() <= 7
    ]
    alertas.sort(key=lambda r: r["dias_para_vencer"])
    return jsonify(alertas)
