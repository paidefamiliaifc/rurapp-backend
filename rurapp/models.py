"""
models.py — Modelos de dados do Sistema de Gestão Nutricional e Sanitária

Usa SQLAlchemy (ORM) sobre SQLite. Rodar `db.create_all()` uma vez
dentro do contexto da app cria o arquivo .db com todas as tabelas.
"""

from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Lote(db.Model):
    """
    Agrupamento de animais (ex: "Lote de recria 2026", "Piquete 3").
    Usado pra listar/gerenciar vários animais juntos e pra lançar
    custos que valem pro grupo inteiro (ex: mão de obra do mês).
    """
    __tablename__ = "lotes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    descricao = db.Column(db.String(200))
    data_criacao = db.Column(db.Date, default=date.today)

    animais = db.relationship("Animal", backref="lote")
    custos = db.relationship("CustoAdicional", backref="lote", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "data_criacao": self.data_criacao.isoformat() if self.data_criacao else None,
            "quantidade_animais": len(self.animais),
        }


class Animal(db.Model):
    __tablename__ = "animais"

    id = db.Column(db.Integer, primary_key=True)
    codigo_identificacao = db.Column(db.String(40))  # nº do brinco/chip
    nome = db.Column(db.String(80))  # nome carinhoso, opcional
    nome_identificador = db.Column(db.String(80), nullable=False)  # mantido p/ compatibilidade (brinco ou nome)
    especie = db.Column(db.String(40), nullable=False)  # bovino, suíno, ovino, ave...
    raca = db.Column(db.String(60))
    sexo = db.Column(db.String(1))  # M/F
    data_nascimento = db.Column(db.Date, nullable=False)
    peso_nascimento_kg = db.Column(db.Float)
    ativo = db.Column(db.Boolean, default=True)

    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"))
    mae_id = db.Column(db.Integer, db.ForeignKey("animais.id"))
    pai_id = db.Column(db.Integer, db.ForeignKey("animais.id"))

    mae = db.relationship("Animal", remote_side=[id], foreign_keys=[mae_id])
    pai = db.relationship("Animal", remote_side=[id], foreign_keys=[pai_id])

    pesagens = db.relationship(
        "Pesagem", backref="animal", cascade="all, delete-orphan",
        foreign_keys="Pesagem.animal_id",
    )
    registros_sanitarios = db.relationship(
        "RegistroSanitario", backref="animal", cascade="all, delete-orphan"
    )
    formulacoes = db.relationship(
        "FormulacaoRacao", backref="animal", cascade="all, delete-orphan",
        order_by="desc(FormulacaoRacao.id)",  # ID cresce a cada cálculo novo — mais confiável
        # que ordenar só pela data (dois cálculos no mesmo dia empatariam na data).
    )
    custos = db.relationship("CustoAdicional", backref="animal", cascade="all, delete-orphan")

    @property
    def idade_dias(self):
        return (date.today() - self.data_nascimento).days

    def fase_de_vida(self):
        """
        Classificação simplificada de fase de vida por espécie/idade.
        Usada para escolher a tabela de exigência nutricional correta
        na calculadora de ração (módulo 2).
        Ajustar limiares conforme espécie/raça e tabelas Embrapa/NRC usadas.
        """
        dias = self.idade_dias
        especie = (self.especie or "").lower()

        if especie == "bovino":
            if dias <= 240:
                return "bezerro_cria"
            elif dias <= 730:
                return "recria"
            else:
                return "terminacao"
        elif especie == "suino":
            if dias <= 21:
                return "leitao_lactente"
            elif dias <= 70:
                return "creche"
            elif dias <= 150:
                return "crescimento"
            else:
                return "terminacao"
        elif especie == "ave":
            if dias <= 21:
                return "inicial"
            elif dias <= 42:
                return "crescimento"
            else:
                return "final"
        elif especie == "ovino" or especie == "caprino":
            if dias <= 90:
                return "cordeiro_lactente"
            elif dias <= 240:
                return "recria"
            else:
                return "terminacao"
        return "adulto_manutencao"

    def peso_atual(self):
        """Retorna a pesagem mais recente registrada."""
        if not self.pesagens:
            return None
        return max(self.pesagens, key=lambda p: p.data).peso_kg

    def dieta_atual(self):
        """Última formulação de ração calculada/salva pra esse animal."""
        return self.formulacoes[0] if self.formulacoes else None

    def custo_total_adicional(self):
        """Soma dos custos extras lançados direto no animal (não do lote)."""
        return round(sum(c.valor for c in self.custos), 2)

    def to_dict(self, incluir_dieta=True):
        dieta = self.dieta_atual()
        d = {
            "id": self.id,
            "codigo_identificacao": self.codigo_identificacao,
            "nome": self.nome,
            "nome_identificador": self.nome_identificador,
            "especie": self.especie,
            "raca": self.raca,
            "sexo": self.sexo,
            "data_nascimento": self.data_nascimento.isoformat(),
            "idade_dias": self.idade_dias,
            "fase_de_vida": self.fase_de_vida(),
            "peso_atual_kg": self.peso_atual(),
            "ativo": self.ativo,
            "lote_id": self.lote_id,
            "lote_nome": self.lote.nome if self.lote else None,
            "mae_id": self.mae_id,
            "mae_identificacao": self.mae.nome_identificador if self.mae else None,
            "pai_id": self.pai_id,
            "pai_identificacao": self.pai.nome_identificador if self.pai else None,
            "custo_adicional_total": self.custo_total_adicional(),
        }
        if incluir_dieta:
            d["dieta_atual"] = dieta.to_dict() if dieta else None
        return d


class Pesagem(db.Model):
    __tablename__ = "pesagens"

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey("animais.id"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    peso_kg = db.Column(db.Float, nullable=False)
    observacao = db.Column(db.String(200))

    def to_dict(self):
        return {
            "id": self.id,
            "animal_id": self.animal_id,
            "data": self.data.isoformat(),
            "peso_kg": self.peso_kg,
            "observacao": self.observacao,
        }


class RegistroSanitario(db.Model):
    __tablename__ = "registros_sanitarios"

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey("animais.id"), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)  # vacina, vermifugo, tratamento
    produto = db.Column(db.String(120), nullable=False)
    data_aplicacao = db.Column(db.Date, nullable=False)
    data_proxima_dose = db.Column(db.Date)  # usado para alerta de vencimento
    observacao = db.Column(db.String(200))

    def dias_para_vencer(self):
        if not self.data_proxima_dose:
            return None
        return (self.data_proxima_dose - date.today()).days

    def to_dict(self):
        dias = self.dias_para_vencer()
        return {
            "id": self.id,
            "animal_id": self.animal_id,
            "tipo": self.tipo,
            "produto": self.produto,
            "data_aplicacao": self.data_aplicacao.isoformat(),
            "data_proxima_dose": (
                self.data_proxima_dose.isoformat() if self.data_proxima_dose else None
            ),
            "dias_para_vencer": dias,
            "status_alerta": (
                "vencido" if dias is not None and dias < 0
                else "proximo" if dias is not None and dias <= 7
                else "ok"
            ),
            "observacao": self.observacao,
        }


class Ingrediente(db.Model):
    """
    Ingrediente disponível para compor a ração (ex: milho, silagem de milho,
    farelo de soja, ureia, calcário calcítico...). Os teores nutricionais
    são inseridos por 1kg de matéria natural (ou matéria seca, à sua escolha,
    desde que seja consistente com as exigências cadastradas).
    Valores de referência: tabelas Embrapa / Rostagno (Tabelas Brasileiras
    para Aves e Suínos) / NRC.

    `custo_por_kg` é o campo que o produtor edita quando o preço muda
    (ex: preço da silagem variou) — é isso que alimenta a aba de custos.
    """
    __tablename__ = "ingredientes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False, unique=True)
    categoria = db.Column(db.String(40))  # volumoso, concentrado_energetico, concentrado_proteico, mineral, aditivo_npn...
    custo_por_kg = db.Column(db.Float, nullable=False)
    proteina_pct = db.Column(db.Float, nullable=False, default=0)   # % PB (ou equivalente-proteico p/ ureia)
    energia_mcal_kg = db.Column(db.Float, nullable=False, default=0)  # Mcal EM/kg
    calcio_pct = db.Column(db.Float, nullable=False, default=0)
    fosforo_pct = db.Column(db.Float, nullable=False, default=0)
    inclusao_min_pct = db.Column(db.Float, default=0)   # limite mín. na mistura (0-100)
    inclusao_max_pct = db.Column(db.Float, default=100)  # limite máx. na mistura (0-100)
    restrito_a_especies = db.Column(db.String(120))  # ex: "bovino,ovino,caprino" — vazio = todas. Usado p/ ureia (só ruminantes).
    observacao_uso = db.Column(db.Text)  # avisos de manejo — sem limite de tamanho
    fonte_bibliografica = db.Column(db.String(200))
    disponivel = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "categoria": self.categoria,
            "custo_por_kg": self.custo_por_kg,
            "proteina_pct": self.proteina_pct,
            "energia_mcal_kg": self.energia_mcal_kg,
            "calcio_pct": self.calcio_pct,
            "fosforo_pct": self.fosforo_pct,
            "inclusao_min_pct": self.inclusao_min_pct,
            "inclusao_max_pct": self.inclusao_max_pct,
            "restrito_a_especies": self.restrito_a_especies,
            "observacao_uso": self.observacao_uso,
            "fonte_bibliografica": self.fonte_bibliografica,
            "disponivel": self.disponivel,
        }


class ExigenciaNutricional(db.Model):
    """
    Exigência nutricional (% ou Mcal por kg de ração) por espécie + fase de vida,
    junto com a conversão alimentar típica esperada — usada pra estimar o
    ganho de peso e o custo por kg ganho (prioridade 1 e 3 do projeto).
    Popular a partir de tabelas Embrapa/NRC/Rostagno — ver seed_exigencias.py.
    """
    __tablename__ = "exigencias_nutricionais"

    id = db.Column(db.Integer, primary_key=True)
    especie = db.Column(db.String(40), nullable=False)
    fase_de_vida = db.Column(db.String(40), nullable=False)
    proteina_min_pct = db.Column(db.Float, nullable=False)
    energia_min_mcal_kg = db.Column(db.Float, nullable=False)
    calcio_min_pct = db.Column(db.Float, nullable=False)
    calcio_max_pct = db.Column(db.Float)
    fosforo_min_pct = db.Column(db.Float, nullable=False)

    # Usados pra estimar ganho de peso (prioridade 1 do projeto)
    conversao_alimentar = db.Column(db.Float)  # kg de ração consumida / kg de peso ganho (CA)
    ganho_medio_diario_kg = db.Column(db.Float)  # GMD esperado nessa fase, kg/dia

    fonte_bibliografica = db.Column(db.String(200))  # ex: "Embrapa CT 179, 2019"

    __table_args__ = (
        db.UniqueConstraint("especie", "fase_de_vida", name="uq_especie_fase"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "especie": self.especie,
            "fase_de_vida": self.fase_de_vida,
            "proteina_min_pct": self.proteina_min_pct,
            "energia_min_mcal_kg": self.energia_min_mcal_kg,
            "calcio_min_pct": self.calcio_min_pct,
            "calcio_max_pct": self.calcio_max_pct,
            "fosforo_min_pct": self.fosforo_min_pct,
            "conversao_alimentar": self.conversao_alimentar,
            "ganho_medio_diario_kg": self.ganho_medio_diario_kg,
            "fonte_bibliografica": self.fonte_bibliografica,
        }


class FormulacaoRacao(db.Model):
    """
    "Fotografia" de uma formulação de ração calculada pro animal — vira a
    "dieta atual" que aparece na ficha dele. Guardamos o resultado (não só
    recalculamos na hora) pra manter histórico de quando o preço/composição
    mudou, e pra alimentar a aba de custos (custo por kg de ganho).
    """
    __tablename__ = "formulacoes_racao"

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey("animais.id"), nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)
    composicao_pct_json = db.Column(db.Text)  # JSON: {"Milho moído": 70.0, ...}
    custo_por_kg_racao = db.Column(db.Float)
    conversao_alimentar_usada = db.Column(db.Float)
    ganho_medio_diario_kg = db.Column(db.Float)
    custo_por_kg_ganho = db.Column(db.Float)  # = custo_por_kg_racao * conversao_alimentar

    def to_dict(self):
        import json
        return {
            "id": self.id,
            "animal_id": self.animal_id,
            "data": self.data.isoformat(),
            "composicao_pct": json.loads(self.composicao_pct_json) if self.composicao_pct_json else {},
            "custo_por_kg_racao": self.custo_por_kg_racao,
            "conversao_alimentar_usada": self.conversao_alimentar_usada,
            "ganho_medio_diario_kg": self.ganho_medio_diario_kg,
            "custo_por_kg_ganho": self.custo_por_kg_ganho,
        }


class CustoAdicional(db.Model):
    """
    Custos que não são de ingrediente — mão de obra, remédios, vacinas
    compradas, frete etc. Podem ser lançados por animal individual OU
    por lote inteiro (rateando entre os animais do lote na hora de somar).
    """
    __tablename__ = "custos_adicionais"

    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey("animais.id"))
    lote_id = db.Column(db.Integer, db.ForeignKey("lotes.id"))
    descricao = db.Column(db.String(120), nullable=False)  # ex: "Mão de obra", "Vermífugo"
    categoria = db.Column(db.String(40))  # mao_de_obra, remedio, frete, outro
    valor = db.Column(db.Float, nullable=False)
    data = db.Column(db.Date, nullable=False, default=date.today)

    def to_dict(self):
        return {
            "id": self.id,
            "animal_id": self.animal_id,
            "lote_id": self.lote_id,
            "descricao": self.descricao,
            "categoria": self.categoria,
            "valor": self.valor,
            "data": self.data.isoformat(),
        }
