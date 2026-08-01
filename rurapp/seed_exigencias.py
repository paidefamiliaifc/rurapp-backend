"""
seed_exigencias.py — Popula o banco LOCAL com dados de exemplo

Rode com: python seed_exigencias.py (depois de já ter rodado app.py
pelo menos uma vez pra criar o banco).

Pra popular o banco HOSPEDADO (Render), use a rota /api/seed do
navegador em vez deste script — ver routes/seed.py.
"""

from app import create_app
from models import db, Ingrediente, ExigenciaNutricional
from seed_data import INGREDIENTES_EXEMPLO, EXIGENCIAS_EXEMPLO

app = create_app()


def seed():
    with app.app_context():
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
        print(f"Seed concluído: {criados_ing} ingredientes e "
              f"{criados_exig} exigências de exemplo inseridos "
              f"(itens repetidos são ignorados automaticamente).")
        print("LEMBRETE: confira/substitua os valores pelas tabelas oficiais "
              "(Rostagno/Embrapa/NRC/BR-CORTE) antes de apresentar na banca.")


if __name__ == "__main__":
    seed()
