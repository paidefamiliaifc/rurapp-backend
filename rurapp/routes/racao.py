"""
routes/racao.py — Módulo 2: Calculadora de Ração de Mínimo Custo

Endpoints para cadastro de ingredientes disponíveis e para rodar a
otimização (formulação de mínimo custo), puxando peso/fase de vida
automaticamente do animal cadastrado no módulo 1. Também estima o
ganho de peso esperado e o custo por kg de peso ganho, e salva o
resultado como a "dieta atual" do animal.
"""

import json
from flask import Blueprint, request, jsonify
from models import db, Ingrediente, ExigenciaNutricional, Animal, FormulacaoRacao
from optimizer import formular_racao_minimo_custo

racao_bp = Blueprint("racao", __name__, url_prefix="/api")


# ---------- Ingredientes ----------

@racao_bp.route("/ingredientes", methods=["GET"])
def listar_ingredientes():
    ingredientes = Ingrediente.query.filter_by(disponivel=True).all()
    return jsonify([i.to_dict() for i in ingredientes])


@racao_bp.route("/ingredientes", methods=["POST"])
def criar_ingrediente():
    dados = request.get_json()
    try:
        ingrediente = Ingrediente(
            nome=dados["nome"],
            categoria=dados.get("categoria"),
            custo_por_kg=dados["custo_por_kg"],
            proteina_pct=dados.get("proteina_pct", 0),
            energia_mcal_kg=dados.get("energia_mcal_kg", 0),
            calcio_pct=dados.get("calcio_pct", 0),
            fosforo_pct=dados.get("fosforo_pct", 0),
            inclusao_min_pct=dados.get("inclusao_min_pct", 0),
            inclusao_max_pct=dados.get("inclusao_max_pct", 100),
            restrito_a_especies=dados.get("restrito_a_especies"),
            observacao_uso=dados.get("observacao_uso"),
            fonte_bibliografica=dados.get("fonte_bibliografica"),
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(ingrediente)
    db.session.commit()
    return jsonify(ingrediente.to_dict()), 201


@racao_bp.route("/ingredientes/<int:ingrediente_id>", methods=["PUT"])
def atualizar_ingrediente(ingrediente_id):
    """
    Usado principalmente pra ATUALIZAR O PREÇO (custo_por_kg) quando o
    valor pago pelo ingrediente muda — é isso que alimenta a aba de custos.
    """
    ingrediente = Ingrediente.query.get_or_404(ingrediente_id)
    dados = request.get_json()
    for campo in [
        "categoria", "custo_por_kg", "proteina_pct", "energia_mcal_kg", "calcio_pct",
        "fosforo_pct", "inclusao_min_pct", "inclusao_max_pct", "restrito_a_especies",
        "observacao_uso", "fonte_bibliografica", "disponivel",
    ]:
        if campo in dados:
            setattr(ingrediente, campo, dados[campo])
    db.session.commit()
    return jsonify(ingrediente.to_dict())


@racao_bp.route("/ingredientes/<int:ingrediente_id>", methods=["DELETE"])
def remover_ingrediente(ingrediente_id):
    ingrediente = Ingrediente.query.get_or_404(ingrediente_id)
    ingrediente.disponivel = False
    db.session.commit()
    return jsonify({"ok": True})


# ---------- Exigências nutricionais ----------

@racao_bp.route("/exigencias", methods=["GET"])
def listar_exigencias():
    exigencias = ExigenciaNutricional.query.all()
    return jsonify([e.to_dict() for e in exigencias])


@racao_bp.route("/exigencias", methods=["POST"])
def criar_exigencia():
    dados = request.get_json()
    try:
        exigencia = ExigenciaNutricional(
            especie=dados["especie"],
            fase_de_vida=dados["fase_de_vida"],
            proteina_min_pct=dados["proteina_min_pct"],
            energia_min_mcal_kg=dados["energia_min_mcal_kg"],
            calcio_min_pct=dados["calcio_min_pct"],
            calcio_max_pct=dados.get("calcio_max_pct"),
            fosforo_min_pct=dados["fosforo_min_pct"],
            conversao_alimentar=dados.get("conversao_alimentar"),
            ganho_medio_diario_kg=dados.get("ganho_medio_diario_kg"),
            fonte_bibliografica=dados.get("fonte_bibliografica"),
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(exigencia)
    db.session.commit()
    return jsonify(exigencia.to_dict()), 201


# ---------- Otimização (o coração do módulo 2) ----------

def _ingrediente_permitido_para_especie(ingrediente: Ingrediente, especie: str) -> bool:
    """
    Alguns ingredientes só valem pra certas espécies — o caso clássico é a
    ureia (fonte de NPN), que só pode ser usada em ruminantes adultos
    (bovinos, ovinos, caprinos) com rúmen funcional. Em monogástricos
    (suínos, aves) ela é tóxica e nunca deve entrar na formulação.
    """
    if not ingrediente.restrito_a_especies:
        return True  # sem restrição cadastrada = vale pra todas
    permitidas = [e.strip().lower() for e in ingrediente.restrito_a_especies.split(",")]
    return (especie or "").lower() in permitidas


@racao_bp.route("/animais/<int:animal_id>/formular-racao", methods=["POST"])
def formular_racao_para_animal(animal_id):
    """
    Fluxo principal: pega o animal (peso/fase de vida vêm do módulo 1),
    busca a exigência nutricional correspondente, filtra ingredientes
    compatíveis com a espécie do animal, roda a otimização e devolve
    a mistura de mínimo custo — junto com uma estimativa de ganho de
    peso e o custo por kg de peso ganho.

    Corpo opcional:
    {
        "ingrediente_ids": [1, 2, 5],   // se omitido, usa todos os disponíveis (já filtrados por espécie)
        "salvar_como_dieta_atual": true,  // default: true
        "max_ingredientes": 5             // default: 5 — limite de ingredientes DISTINTOS na mistura
                                           // (evita misturas com percentuais minúsculos de 8+ itens,
                                           // que são matematicamente ótimas mas inviáveis na prática).
                                           // Use null pra desligar o limite.
    }
    """
    animal = Animal.query.get_or_404(animal_id)
    fase = animal.fase_de_vida()

    exigencia = ExigenciaNutricional.query.filter_by(
        especie=animal.especie, fase_de_vida=fase
    ).first()

    if not exigencia:
        return jsonify({
            "erro": f"Nenhuma exigência nutricional cadastrada para "
                    f"espécie='{animal.especie}', fase='{fase}'. "
                    f"Cadastre em POST /api/exigencias."
        }), 400

    dados = request.get_json(silent=True) or {}
    ids_selecionados = dados.get("ingrediente_ids")
    salvar_dieta = dados.get("salvar_como_dieta_atual", True)
    max_ingredientes = dados.get("max_ingredientes", 5)  # padrão prático: até 5 itens na mistura

    query = Ingrediente.query.filter_by(disponivel=True)
    if ids_selecionados:
        query = query.filter(Ingrediente.id.in_(ids_selecionados))
    ingredientes = [
        i for i in query.all()
        if _ingrediente_permitido_para_especie(i, animal.especie)
    ]

    resultado = formular_racao_minimo_custo(ingredientes, exigencia, max_ingredientes=max_ingredientes)

    ganho_estimado = None
    custo_por_kg_ganho = None
    if resultado.sucesso and exigencia.conversao_alimentar:
        custo_por_kg_ganho = round(resultado.custo_por_kg * exigencia.conversao_alimentar, 2)
        ganho_estimado = exigencia.ganho_medio_diario_kg

    if resultado.sucesso and salvar_dieta:
        formulacao = FormulacaoRacao(
            animal_id=animal.id,
            composicao_pct_json=json.dumps(resultado.composicao, ensure_ascii=False),
            custo_por_kg_racao=resultado.custo_por_kg,
            conversao_alimentar_usada=exigencia.conversao_alimentar,
            ganho_medio_diario_kg=exigencia.ganho_medio_diario_kg,
            custo_por_kg_ganho=custo_por_kg_ganho,
        )
        db.session.add(formulacao)
        db.session.commit()

    return jsonify({
        "animal": {
            "id": animal.id,
            "nome_identificador": animal.nome_identificador,
            "peso_atual_kg": animal.peso_atual(),
            "fase_de_vida": fase,
        },
        "exigencia_utilizada": exigencia.to_dict(),
        "sucesso": resultado.sucesso,
        "status": resultado.status,
        "max_ingredientes_permitido": max_ingredientes,
        "quantidade_ingredientes_usados": len(resultado.composicao),
        "custo_por_kg_racao": resultado.custo_por_kg,
        "composicao_pct": resultado.composicao,
        "nutrientes_atingidos": resultado.nutrientes_atingidos,
        "ganho_medio_diario_estimado_kg": ganho_estimado,
        "custo_estimado_por_kg_ganho": custo_por_kg_ganho,
        "mensagem": resultado.mensagem,
    }), (200 if resultado.sucesso else 422)


@racao_bp.route("/animais/<int:animal_id>/dieta-atual", methods=["GET"])
def obter_dieta_atual(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    dieta = animal.dieta_atual()
    if not dieta:
        return jsonify({"erro": "Esse animal ainda não tem uma dieta calculada. "
                                 "Use POST /api/animais/<id>/formular-racao."}), 404
    return jsonify(dieta.to_dict())
