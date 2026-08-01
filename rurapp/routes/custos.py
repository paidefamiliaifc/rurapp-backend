"""
routes/custos.py — Custos adicionais e resumo de custo por kg ganho

Cobre a prioridade 3 do projeto: além do custo da ração (calculado no
módulo 2), o produtor pode lançar custos extras (mão de obra, remédio,
frete...) por animal individual ou por lote inteiro, e ver um resumo
de quanto custou, no total, cada kg de peso que o animal ganhou.
"""

from flask import Blueprint, request, jsonify
from models import db, CustoAdicional, Animal, Lote

custos_bp = Blueprint("custos", __name__, url_prefix="/api")


def _parse_date(s):
    from datetime import datetime
    return datetime.strptime(s, "%Y-%m-%d").date() if s else None


@custos_bp.route("/custos", methods=["POST"])
def lancar_custo():
    """
    Corpo: { "descricao": "...", "categoria": "mao_de_obra"|"remedio"|"frete"|"outro",
             "valor": 12.50, "data": "2026-07-30" (opcional),
             "animal_id": 1  OU  "lote_id": 2 }
    Informe animal_id OU lote_id (não os dois).
    """
    dados = request.get_json()
    if not dados.get("animal_id") and not dados.get("lote_id"):
        return jsonify({"erro": "Informe animal_id ou lote_id."}), 400
    try:
        custo = CustoAdicional(
            animal_id=dados.get("animal_id"),
            lote_id=dados.get("lote_id"),
            descricao=dados["descricao"],
            categoria=dados.get("categoria", "outro"),
            valor=dados["valor"],
            data=_parse_date(dados.get("data")) or None,
        )
    except KeyError as e:
        return jsonify({"erro": f"Campo obrigatório faltando: {e}"}), 400

    db.session.add(custo)
    db.session.commit()
    return jsonify(custo.to_dict()), 201


@custos_bp.route("/custos/<int:custo_id>", methods=["DELETE"])
def remover_custo(custo_id):
    custo = CustoAdicional.query.get_or_404(custo_id)
    db.session.delete(custo)
    db.session.commit()
    return jsonify({"ok": True})


@custos_bp.route("/animais/<int:animal_id>/custos", methods=["GET"])
def listar_custos_animal(animal_id):
    Animal.query.get_or_404(animal_id)
    custos = CustoAdicional.query.filter_by(animal_id=animal_id).all()
    return jsonify([c.to_dict() for c in custos])


@custos_bp.route("/lotes/<int:lote_id>/custos", methods=["GET"])
def listar_custos_lote(lote_id):
    Lote.query.get_or_404(lote_id)
    custos = CustoAdicional.query.filter_by(lote_id=lote_id).all()
    return jsonify([c.to_dict() for c in custos])


@custos_bp.route("/animais/<int:animal_id>/resumo-custos", methods=["GET"])
def resumo_custos_animal(animal_id):
    """
    Junta tudo pra responder a pergunta central da prioridade 3:
    "quanto está custando, por kg de peso ganho, esse animal?"

    - custo_por_kg_racao: vem da última formulação de ração calculada
    - custo_estimado_por_kg_ganho (só ração): custo_por_kg_racao * conversão alimentar
    - custo_adicional_direto: soma dos custos lançados direto no animal
    - custo_adicional_rateado_do_lote: parte proporcional dos custos do lote
      (dividido igualmente entre os animais ativos do lote)
    - peso_ganho_total_kg: peso atual - peso ao nascer (baseado nas pesagens reais)
    - custo_adicional_por_kg_ganho: custos extras / peso realmente ganho
    - custo_total_por_kg_ganho: soma da ração + dos custos extras, por kg ganho
    """
    animal = Animal.query.get_or_404(animal_id)
    dieta = animal.dieta_atual()

    custo_adicional_direto = animal.custo_total_adicional()

    custo_adicional_rateado = 0.0
    if animal.lote_id:
        lote = Lote.query.get(animal.lote_id)
        animais_ativos_no_lote = [a for a in lote.animais if a.ativo]
        qtd = len(animais_ativos_no_lote) or 1
        custo_total_lote = round(sum(c.valor for c in lote.custos), 2)
        custo_adicional_rateado = round(custo_total_lote / qtd, 2)

    custo_adicional_total = round(custo_adicional_direto + custo_adicional_rateado, 2)

    peso_atual = animal.peso_atual()
    peso_ganho_total = None
    if peso_atual is not None and animal.peso_nascimento_kg is not None:
        peso_ganho_total = round(peso_atual - animal.peso_nascimento_kg, 2)

    custo_adicional_por_kg_ganho = None
    if peso_ganho_total and peso_ganho_total > 0:
        custo_adicional_por_kg_ganho = round(custo_adicional_total / peso_ganho_total, 2)

    custo_estimado_por_kg_ganho_racao = dieta.custo_por_kg_ganho if dieta else None

    custo_total_por_kg_ganho = None
    if custo_estimado_por_kg_ganho_racao is not None:
        custo_total_por_kg_ganho = round(
            custo_estimado_por_kg_ganho_racao + (custo_adicional_por_kg_ganho or 0), 2
        )

    return jsonify({
        "animal_id": animal.id,
        "nome_identificador": animal.nome_identificador,
        "dieta_atual": dieta.to_dict() if dieta else None,
        "custo_adicional_direto": custo_adicional_direto,
        "custo_adicional_rateado_do_lote": custo_adicional_rateado,
        "custo_adicional_total": custo_adicional_total,
        "peso_nascimento_kg": animal.peso_nascimento_kg,
        "peso_atual_kg": peso_atual,
        "peso_ganho_total_kg": peso_ganho_total,
        "custo_adicional_por_kg_ganho": custo_adicional_por_kg_ganho,
        "custo_estimado_por_kg_ganho_racao": custo_estimado_por_kg_ganho_racao,
        "custo_total_estimado_por_kg_ganho": custo_total_por_kg_ganho,
    })
