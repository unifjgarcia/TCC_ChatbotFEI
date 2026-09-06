import csv
import os
from datetime import datetime


CAMINHO_LOGS = "dados/logs_execucoes.csv"


COLUNAS = [
    "timestamp",
    "pergunta",
    "resposta",
    "top_k",
    "config_id",
    "modelo_gerador",
    "tempo_resposta_ms",
    "fonte_1_titulo",
    "fonte_1_url",
    "fonte_1_distancia",
    "fonte_2_titulo",
    "fonte_2_url",
    "fonte_2_distancia",
    "fonte_3_titulo",
    "fonte_3_url",
    "fonte_3_distancia",
    "fonte_4_titulo",
    "fonte_4_url",
    "fonte_4_distancia",
    "fonte_5_titulo",
    "fonte_5_url",
    "fonte_5_distancia",
]


def registrar_execucao(
    pergunta,
    resposta,
    trechos,
    top_k,
    config_id,
    modelo_gerador,
    tempo_resposta_ms
):
    os.makedirs("dados", exist_ok=True)

    arquivo_existe = os.path.exists(CAMINHO_LOGS)

    linha = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "pergunta": pergunta,
        "resposta": resposta,
        "top_k": top_k,
        "config_id": config_id,
        "modelo_gerador": modelo_gerador,
        "tempo_resposta_ms": tempo_resposta_ms,
    }

    for i in range(1, 6):
        if i <= len(trechos):
            trecho = trechos[i - 1]
            linha[f"fonte_{i}_titulo"] = trecho.get("titulo")
            linha[f"fonte_{i}_url"] = trecho.get("url")
            linha[f"fonte_{i}_distancia"] = trecho.get("distancia")
        else:
            linha[f"fonte_{i}_titulo"] = ""
            linha[f"fonte_{i}_url"] = ""
            linha[f"fonte_{i}_distancia"] = ""

    with open(CAMINHO_LOGS, "a", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=COLUNAS)

        if not arquivo_existe:
            writer.writeheader()

        writer.writerow(linha)