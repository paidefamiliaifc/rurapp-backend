"""
seed_data.py — Só os DADOS de exemplo (ingredientes e exigências), sem
nenhuma dependência do Flask/banco. Existe separado pra evitar import
circular: tanto o script de linha de comando (seed_exigencias.py) quanto
a rota de seed pela web (routes/seed.py) importam esses dados daqui.

IMPORTANTE PRA BOLSA/FEIRA DE CIÊNCIAS: os valores abaixo são TÍPICOS
de referência, só pra o sistema funcionar de ponta a ponta. Substituir
pelas tabelas oficiais (Rostagno/Embrapa/NRC/BR-CORTE) antes de
apresentar — ver marcações "AJUSTAR" em cada item.
"""

INGREDIENTES_EXEMPLO = [
    # ---- Volumosos ----
    dict(nome="Silagem de milho", categoria="volumoso", custo_por_kg=0.25,
         proteina_pct=7.5, energia_mcal_kg=1.10, calcio_pct=0.25, fosforo_pct=0.20,
         inclusao_min_pct=0, inclusao_max_pct=80,
         fonte_bibliografica="AJUSTAR: Valadares Filho et al., Tabelas Brasileiras "
                              "de Composição de Alimentos para Bovinos"),
    dict(nome="Cana-de-açúcar picada", categoria="volumoso", custo_por_kg=0.10,
         proteina_pct=2.5, energia_mcal_kg=1.30, calcio_pct=0.05, fosforo_pct=0.06,
         inclusao_min_pct=0, inclusao_max_pct=60,
         fonte_bibliografica="AJUSTAR: Embrapa Gado de Corte / BR-CORTE"),
    dict(nome="Feno de Tifton", categoria="volumoso", custo_por_kg=0.80,
         proteina_pct=10.0, energia_mcal_kg=1.05, calcio_pct=0.40, fosforo_pct=0.22,
         inclusao_min_pct=0, inclusao_max_pct=100,
         fonte_bibliografica="AJUSTAR: Embrapa Gado de Leite"),

    # ---- Concentrados energéticos ----
    dict(nome="Milho moído", categoria="concentrado_energetico", custo_por_kg=0.90,
         proteina_pct=8.0, energia_mcal_kg=3.30, calcio_pct=0.03, fosforo_pct=0.27,
         inclusao_min_pct=0, inclusao_max_pct=70,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),
    dict(nome="Farelo de trigo", categoria="concentrado_energetico", custo_por_kg=1.10,
         proteina_pct=15.5, energia_mcal_kg=1.90, calcio_pct=0.13, fosforo_pct=0.93,
         inclusao_min_pct=0, inclusao_max_pct=20,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),
    dict(nome="Farelo de arroz", categoria="concentrado_energetico", custo_por_kg=0.70,
         proteina_pct=13.0, energia_mcal_kg=2.98, calcio_pct=0.08, fosforo_pct=1.50,
         inclusao_min_pct=0, inclusao_max_pct=20,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),

    # ---- Concentrados proteicos ----
    dict(nome="Farelo de soja", categoria="concentrado_proteico", custo_por_kg=2.20,
         proteina_pct=45.0, energia_mcal_kg=2.24, calcio_pct=0.27, fosforo_pct=0.65,
         inclusao_min_pct=0, inclusao_max_pct=40,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),
    dict(nome="Farelo de algodão", categoria="concentrado_proteico", custo_por_kg=1.60,
         proteina_pct=38.0, energia_mcal_kg=1.90, calcio_pct=0.20, fosforo_pct=1.00,
         inclusao_min_pct=0, inclusao_max_pct=20,
         fonte_bibliografica="AJUSTAR: Embrapa Gado de Corte / BR-CORTE"),
    dict(nome="Óleo de soja", categoria="concentrado_energetico", custo_por_kg=6.50,
         proteina_pct=0, energia_mcal_kg=8.80, calcio_pct=0, fosforo_pct=0,
         inclusao_min_pct=0, inclusao_max_pct=8,
         restrito_a_especies="suino,ave",
         observacao_uso="Fonte de energia concentrada (gordura), usada em rações "
                         "de suínos/aves jovens que precisam de alta densidade "
                         "energética. Custo alto, por isso a otimização só usa "
                         "o quanto for necessário.",
         fonte_bibliografica="AJUSTAR: Rostagno et al."),

    # ---- Aditivo NPN (só ruminantes) ----
    dict(nome="Ureia pecuária", categoria="aditivo_npn", custo_por_kg=3.20,
         proteina_pct=280.0,  # "proteína bruta equivalente" — NPN convertida (~262-281% PB eq.)
         energia_mcal_kg=0, calcio_pct=0, fosforo_pct=0,
         inclusao_min_pct=0, inclusao_max_pct=1.0,
         restrito_a_especies="bovino,ovino,caprino",
         observacao_uso="NPN: introduzir de forma GRADUAL (adaptação de 10-15 dias), "
                         "nunca fornecer em jejum, sempre com fonte de energia "
                         "fermentável disponível (ex: milho) e água à vontade. "
                         "Não usar em bezerros/cordeiros antes do rúmen funcional "
                         "nem em monogástricos (é tóxica). CONFIRME o limite de "
                         "inclusão com fonte técnica — este valor é só ilustrativo.",
         fonte_bibliografica="AJUSTAR: Embrapa Gado de Corte — uso de ureia em "
                              "dietas de ruminantes"),

    # ---- Minerais ----
    dict(nome="Calcário calcítico", categoria="mineral", custo_por_kg=0.40,
         proteina_pct=0, energia_mcal_kg=0, calcio_pct=38.0, fosforo_pct=0,
         inclusao_min_pct=0, inclusao_max_pct=3,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),
    dict(nome="Fosfato bicálcico", categoria="mineral", custo_por_kg=3.50,
         proteina_pct=0, energia_mcal_kg=0, calcio_pct=24.0, fosforo_pct=18.5,
         inclusao_min_pct=0, inclusao_max_pct=2,
         fonte_bibliografica="AJUSTAR: Rostagno et al."),
    dict(nome="Sal mineral bovino", categoria="mineral", custo_por_kg=4.50,
         proteina_pct=0, energia_mcal_kg=0, calcio_pct=12.0, fosforo_pct=8.0,
         inclusao_min_pct=0.3, inclusao_max_pct=1.0,
         restrito_a_especies="bovino,ovino,caprino",
         fonte_bibliografica="AJUSTAR: rótulo do fabricante / Embrapa"),
    dict(nome="Sal comum", categoria="mineral", custo_por_kg=0.60,
         proteina_pct=0, energia_mcal_kg=0, calcio_pct=0, fosforo_pct=0,
         inclusao_min_pct=0.3, inclusao_max_pct=0.5),
]

# conversao_alimentar = kg de ração consumida por kg de peso ganho (CA)
# ganho_medio_diario_kg = GMD esperado nessa fase (kg/dia)
# ESTES SÃO VALORES TÍPICOS ILUSTRATIVOS — AJUSTAR com Rostagno/Embrapa/NRC
EXIGENCIAS_EXEMPLO = [
    dict(especie="suino", fase_de_vida="creche",
         proteina_min_pct=20.0, energia_min_mcal_kg=3.30,
         calcio_min_pct=0.80, calcio_max_pct=1.10, fosforo_min_pct=0.40,
         conversao_alimentar=1.6, ganho_medio_diario_kg=0.40,
         fonte_bibliografica="AJUSTAR: Rostagno et al., Tabelas Brasileiras "
                              "para Aves e Suínos"),
    dict(especie="suino", fase_de_vida="crescimento",
         proteina_min_pct=16.0, energia_min_mcal_kg=3.25,
         calcio_min_pct=0.65, calcio_max_pct=0.95, fosforo_min_pct=0.38,
         conversao_alimentar=2.4, ganho_medio_diario_kg=0.75,
         fonte_bibliografica="AJUSTAR: Rostagno et al., Tabelas Brasileiras "
                              "para Aves e Suínos"),
    dict(especie="suino", fase_de_vida="terminacao",
         proteina_min_pct=14.0, energia_min_mcal_kg=3.25,
         calcio_min_pct=0.55, calcio_max_pct=0.90, fosforo_min_pct=0.32,
         conversao_alimentar=3.0, ganho_medio_diario_kg=0.85,
         fonte_bibliografica="AJUSTAR: Rostagno et al., Tabelas Brasileiras "
                              "para Aves e Suínos"),
    dict(especie="ave", fase_de_vida="inicial",
         proteina_min_pct=21.0, energia_min_mcal_kg=2.95,
         calcio_min_pct=0.85, calcio_max_pct=1.10, fosforo_min_pct=0.42,
         conversao_alimentar=1.3, ganho_medio_diario_kg=0.03,
         fonte_bibliografica="AJUSTAR: Rostagno et al. — frango de corte, fase inicial"),
    dict(especie="ave", fase_de_vida="crescimento",
         proteina_min_pct=19.0, energia_min_mcal_kg=3.05,
         calcio_min_pct=0.75, calcio_max_pct=1.00, fosforo_min_pct=0.38,
         conversao_alimentar=1.6, ganho_medio_diario_kg=0.06,
         fonte_bibliografica="AJUSTAR: Rostagno et al. — frango de corte, crescimento"),
    dict(especie="bovino", fase_de_vida="bezerro_cria",
         proteina_min_pct=16.0, energia_min_mcal_kg=2.60,
         calcio_min_pct=0.50, calcio_max_pct=None, fosforo_min_pct=0.30,
         conversao_alimentar=5.5, ganho_medio_diario_kg=0.60,
         fonte_bibliografica="AJUSTAR: NRC Beef Cattle / Embrapa Gado de Corte"),
    dict(especie="bovino", fase_de_vida="recria",
         proteina_min_pct=11.0, energia_min_mcal_kg=2.10,
         calcio_min_pct=0.28, calcio_max_pct=None, fosforo_min_pct=0.18,
         conversao_alimentar=8.0, ganho_medio_diario_kg=0.55,
         fonte_bibliografica="AJUSTAR: NRC Beef Cattle / Embrapa Gado de Corte"),
    dict(especie="bovino", fase_de_vida="terminacao",
         proteina_min_pct=12.5, energia_min_mcal_kg=2.55,
         calcio_min_pct=0.35, calcio_max_pct=None, fosforo_min_pct=0.22,
         conversao_alimentar=6.5, ganho_medio_diario_kg=1.10,
         fonte_bibliografica="AJUSTAR: NRC Beef Cattle / Embrapa Gado de Corte "
                              "(dieta de terminação, engorda intensiva)"),
]


