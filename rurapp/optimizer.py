"""
optimizer.py — Formulação de ração de mínimo custo (Programação Linear)

Problema clássico de PO em zootecnia: dado um conjunto de ingredientes
(cada um com custo e composição nutricional) e um conjunto de exigências
nutricionais mínimas/máximas, encontrar as proporções (%) de cada
ingrediente que:

    minimizam:      custo total da mistura (R$/kg)
    sujeito a:       soma das proporções = 100%
                     nutrientes da mistura >= exigência mínima
                     nutrientes da mistura <= exigência máxima (quando houver)
                     inclusao_min_pct <= proporção do ingrediente <= inclusao_max_pct

Isso é exatamente um problema de Programação Linear (PL): função objetivo
linear + restrições lineares. Usamos PuLP (interface Python para solvers
de PL como CBC, que já vem embutido).

Referência clássica: o problema da "dieta de custo mínimo" (Stigler, 1945)
é um dos primeiros usos históricos de PL, e sua aplicação em nutrição
animal é tema de pesquisa ativo em zootecnia/PO.
"""

from dataclasses import dataclass
from typing import List, Optional
import pulp


@dataclass
class ResultadoOtimizacao:
    sucesso: bool
    status: str
    custo_por_kg: Optional[float]
    composicao: dict  # {nome_ingrediente: percentual_na_mistura}
    nutrientes_atingidos: dict  # {nutriente: valor_na_mistura}
    mensagem: Optional[str] = None


def formular_racao_minimo_custo(ingredientes: list, exigencia, max_ingredientes: int = None) -> ResultadoOtimizacao:
    """
    ingredientes: lista de objetos Ingrediente (ou dicts com os mesmos campos)
    exigencia: objeto ExigenciaNutricional (ou dict com os mesmos campos)
    max_ingredientes: se informado, limita quantos ingredientes DISTINTOS podem
        entrar na mistura final (ex: 4). Sem isso, a Programação Linear "pura"
        às vezes espalha percentuais pequenos por muitos ingredientes — o que é
        matematicamente ótimo, mas inviável na prática (o produtor não vai pesar
        8 ingredientes diferentes todo dia). Com o limite, o problema vira uma
        Programação Linear Inteira Mista (adicionamos uma variável 0/1 "usa esse
        ingrediente?" pra cada item, e uma restrição de soma dessas variáveis).
    """
    ingredientes = [_as_dict(i) for i in ingredientes]
    exigencia = _as_dict(exigencia)

    if not ingredientes:
        return ResultadoOtimizacao(False, "sem_ingredientes", None, {}, {},
                                    "Nenhum ingrediente disponível para formular a mistura.")

    problema = pulp.LpProblem("formulacao_racao_minimo_custo", pulp.LpMinimize)

    # Variável de decisão: percentual (0-100) de cada ingrediente na mistura
    variaveis = {
        ing["nome"]: pulp.LpVariable(
            f"pct_{ing['nome']}",
            lowBound=0,  # o mínimo de inclusão só é aplicado QUANDO o ingrediente é usado (ver abaixo)
            upBound=ing.get("inclusao_max_pct", 100) or 100,
        )
        for ing in ingredientes
    }

    # Variáveis binárias "usa esse ingrediente?" — só existem/entram em jogo
    # quando queremos limitar a quantidade de ingredientes distintos.
    usa = None
    if max_ingredientes:
        usa = {
            ing["nome"]: pulp.LpVariable(f"usa_{ing['nome']}", cat="Binary")
            for ing in ingredientes
        }

    # Função objetivo: custo total por kg de ração = soma(pct * 0.01 * custo_kg)
    # (usamos multiplicação por 0.01 em vez de divisão por 100, porque o PuLP
    # não aceita dividir uma LpVariable por um número — só multiplicar)
    problema += pulp.lpSum(
        (variaveis[ing["nome"]] * 0.01) * ing["custo_por_kg"] for ing in ingredientes
    ), "custo_total"

    # Restrição: soma dos percentuais = 100%
    problema += pulp.lpSum(variaveis[ing["nome"]] for ing in ingredientes) == 100, "soma_100"

    if max_ingredientes:
        for ing in ingredientes:
            nome = ing["nome"]
            maximo = ing.get("inclusao_max_pct", 100) or 100
            minimo = ing.get("inclusao_min_pct", 0) or 0
            # se usa[nome] == 0, o percentual é travado em 0 (ingrediente fora da mistura)
            problema += variaveis[nome] <= usa[nome] * maximo, f"liga_max_{nome}"
            if minimo > 0:
                # se usa[nome] == 1, respeita o mínimo de inclusão; se 0, fica de fato em 0
                problema += variaveis[nome] >= usa[nome] * minimo, f"liga_min_{nome}"
        problema += pulp.lpSum(usa.values()) <= max_ingredientes, "limite_qtd_ingredientes"

    # Restrições nutricionais (mínimas)
    def soma_nutriente(campo):
        return pulp.lpSum(
            (variaveis[ing["nome"]] * 0.01) * ing.get(campo, 0) for ing in ingredientes
        )

    problema += soma_nutriente("proteina_pct") >= exigencia["proteina_min_pct"], "proteina_min"
    problema += soma_nutriente("energia_mcal_kg") >= exigencia["energia_min_mcal_kg"], "energia_min"
    problema += soma_nutriente("calcio_pct") >= exigencia["calcio_min_pct"], "calcio_min"
    problema += soma_nutriente("fosforo_pct") >= exigencia["fosforo_min_pct"], "fosforo_min"

    if exigencia.get("calcio_max_pct"):
        problema += soma_nutriente("calcio_pct") <= exigencia["calcio_max_pct"], "calcio_max"

    # Resolve com CBC (solver que já vem junto com o PuLP, não precisa instalar nada externo)
    problema.solve(pulp.PULP_CBC_CMD(msg=False))

    status = pulp.LpStatus[problema.status]

    if status != "Optimal":
        mensagem = (
            "Não foi possível encontrar uma combinação viável. Verifique se os "
            "ingredientes disponíveis conseguem, juntos, atingir as exigências "
            "mínimas (proteína/energia/cálcio/fósforo), ou se os limites de "
            "inclusão de algum ingrediente estão bloqueando a solução."
        )
        if max_ingredientes:
            mensagem += (
                f" Também pode ser que {max_ingredientes} ingrediente(s) não sejam "
                f"suficientes pra bater as exigências — tente aumentar esse limite."
            )
        return ResultadoOtimizacao(False, status, None, {}, {}, mensagem)

    composicao = {
        nome: round(var.value(), 2) for nome, var in variaveis.items() if var.value() and var.value() > 0.01
    }
    custo_total = round(pulp.value(problema.objective), 4)

    nutrientes_atingidos = {}
    for campo, label in [
        ("proteina_pct", "proteina_pct"),
        ("energia_mcal_kg", "energia_mcal_kg"),
        ("calcio_pct", "calcio_pct"),
        ("fosforo_pct", "fosforo_pct"),
    ]:
        valor = sum(
            (variaveis[ing["nome"]].value() / 100) * ing.get(campo, 0) for ing in ingredientes
        )
        nutrientes_atingidos[label] = round(valor, 3)

    return ResultadoOtimizacao(
        sucesso=True,
        status=status,
        custo_por_kg=custo_total,
        composicao=composicao,
        nutrientes_atingidos=nutrientes_atingidos,
    )


def _as_dict(obj):
    if isinstance(obj, dict):
        return obj
    # objeto SQLAlchemy: usa to_dict() se existir, senão vasculha __dict__
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
