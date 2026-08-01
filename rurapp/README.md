# Backend — Sistema de Gestão Nutricional e Sanitária

Backend Flask + SQLite com os dois módulos do projeto, agora incluindo
gestão de lotes/pais, custos por kg de ganho de peso, e uma base de
ingredientes mais completa (volumosos, ureia, óleo de soja etc.).

## ⚠️ MUITO IMPORTANTE — leia antes de rodar

Como o banco de dados ganhou tabelas e campos novos, o arquivo antigo
`rurapp.db` (se você já rodou uma versão anterior) **não é compatível**
com este código. Antes de rodar pela primeira vez:

1. Pare o servidor antigo (CTRL+C na janela do terminal, se estiver rodando)
2. **Apague o arquivo `rurapp.db`** (fica dentro da pasta `rurapp`, no
   Explorador de Arquivos — é só selecionar e apertar Delete)
3. Rode `python app.py` de novo — ele cria um banco novo, do zero, já
   com a estrutura atualizada
4. Rode `python seed_exigencias.py` de novo pra repopular os dados de exemplo

(Isso significa que qualquer animal/pesagem de teste que você já tinha
cadastrado vai ser perdido — tudo bem, era só dado de teste mesmo.)

## O que mudou nesta versão

**Prioridade 1 — Cálculo de ração mais completo**
- Base de ingredientes ampliada: volumosos (silagem de milho, cana,
  feno), concentrados energéticos e proteicos, minerais, e um aditivo
  NPN (ureia pecuária — só pra ruminantes, com aviso de manejo)
- Campo `restrito_a_especies` no ingrediente: alguns ingredientes (ureia,
  óleo de soja, sal mineral bovino) só entram na conta pra espécies
  compatíveis — o sistema filtra isso automaticamente
- Cada exigência nutricional agora tem `conversao_alimentar` (kg de
  ração / kg de peso ganho) e `ganho_medio_diario_kg` — isso permite
  estimar quanto o animal deve ganhar de peso com aquela dieta

**Prioridade 2 — Lotes e genealogia**
- Nova tabela de **Lotes** (`/api/lotes`) pra agrupar animais
- Animal ganhou: `codigo_identificacao` (brinco/chip), `nome`, `lote_id`,
  `mae_id`, `pai_id` — tudo opcional, pra não quebrar cadastros antigos
- `PUT /api/animais/<id>` pra editar qualquer campo do animal depois

**Prioridade 3 — Custos e custo por kg ganho**
- Toda vez que você calcula a ração, o sistema salva como a "dieta atual"
  do animal (`GET /api/animais/<id>/dieta-atual`)
- Nova tabela de **custos adicionais** (mão de obra, remédio, frete...),
  lançável por animal ou por lote inteiro
- `GET /api/animais/<id>/resumo-custos` — junta o custo da ração +
  custos extras e calcula o **custo por kg de peso realmente ganho**
  (usando o histórico de pesagens de verdade, não só a estimativa)

## Estrutura

```
rurapp/
├── app.py
├── models.py
├── optimizer.py
├── seed_exigencias.py
├── requirements.txt
└── routes/
    ├── manejo.py    # animais, pesagens, sanidade
    ├── racao.py     # ingredientes, exigências, otimização
    ├── lotes.py     # NOVO: gestão de lotes
    └── custos.py    # NOVO: custos adicionais e resumo por kg ganho
```

## Como rodar

```bash
cd rurapp
pip install -r requirements.txt
python app.py                   # cria rurapp.db (novo, do zero — ver aviso acima)
```

Em outro terminal:
```bash
python seed_exigencias.py       # popula ingredientes/exigências de exemplo
```

## Principais endpoints novos

| Método | Rota | Descrição |
|---|---|---|
| GET/POST | `/api/lotes` | listar / criar lote |
| GET | `/api/lotes/<id>` | detalhe do lote + animais dele |
| PUT/DELETE | `/api/lotes/<id>` | editar / remover lote |
| PUT | `/api/animais/<id>` | editar dados do animal (lote, pai, mãe, código...) |
| GET | `/api/animais/<id>/dieta-atual` | última ração calculada pro animal |
| POST | `/api/custos` | lançar um custo (animal ou lote) |
| GET | `/api/animais/<id>/custos` | custos lançados direto no animal |
| GET | `/api/animais/<id>/resumo-custos` | **custo total por kg ganho** |

### Exemplo — criar animal já com lote e pai/mãe
```bash
curl.exe -X POST http://localhost:5000/api/animais -H "Content-Type: application/json" -d "{\"nome_identificador\": \"Porco 2\", \"codigo_identificacao\": \"BR-0045\", \"nome\": \"Bacon\", \"especie\": \"suino\", \"data_nascimento\": \"2026-05-01\", \"lote_id\": 1, \"mae_id\": 1}"
```

### Exemplo — lançar um custo de mão de obra pro lote inteiro
```bash
curl.exe -X POST http://localhost:5000/api/custos -H "Content-Type: application/json" -d "{\"descricao\": \"Diaria mao de obra\", \"categoria\": \"mao_de_obra\", \"valor\": 80, \"lote_id\": 1}"
```

## ⚠️ Antes de apresentar na banca

Os valores nutricionais em `seed_exigencias.py` (proteína, energia,
cálcio, fósforo, conversão alimentar, ganho médio diário) são
**valores típicos de referência**, calibrados só pra o sistema
funcionar de ponta a ponta sem dar erro. Pra ter embasamento científico
real, substitua pelos das tabelas oficiais:
- Rostagno et al. — *Tabelas Brasileiras para Aves e Suínos* (UFV)
- Embrapa (circulares técnicas por espécie/fase)
- NRC — *Nutrient Requirements of Beef Cattle / Swine / Poultry*
- Valadares Filho et al. / BR-CORTE — *Tabelas Brasileiras de
  Composição de Alimentos para Bovinos*

E preencha `fonte_bibliografica` de cada exigência com a citação exata.

**Sobre a ureia**: o limite de inclusão (1% da mistura) e o texto de
aviso em `observacao_uso` são ilustrativos. Antes de usar esse dado
publicamente, confirme com uma fonte técnica (Embrapa tem boletins
específicos sobre uso de NPN em bovinos) — é um insumo que exige
cuidado real no manejo (introdução gradual, nunca em jejum).
