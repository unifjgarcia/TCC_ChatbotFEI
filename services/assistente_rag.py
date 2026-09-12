import time

from services.buscador_vetorial import buscar_trechos
from services.gerador_llama import gerar_resposta_com_llama, MODELO_LLAMA
from services.gerador_gemini import gerar_resposta_com_gemini, MODELO_GEMINI
from services.registrador_logs import registrar_execucao


def responder_pergunta(pergunta, top_k=3, config_id="C5", modelo_gerador=None):
    inicio = time.time()

    if modelo_gerador is None:
        modelo_gerador = MODELO_LLAMA

    trechos = buscar_trechos(
        pergunta=pergunta,
        top_k=top_k,
        config_id=config_id
    )

    if modelo_gerador == MODELO_GEMINI:
        resposta = gerar_resposta_com_gemini(
            pergunta=pergunta,
            trechos=trechos
        )
    else:
        resposta = gerar_resposta_com_llama(
            pergunta=pergunta,
            trechos=trechos
        )

    fim = time.time()
    tempo_resposta_ms = round((fim - inicio) * 1000, 2)

    registrar_execucao(
        pergunta=pergunta,
        resposta=resposta,
        trechos=trechos,
        top_k=top_k,
        config_id=config_id,
        modelo_gerador=modelo_gerador,
        tempo_resposta_ms=tempo_resposta_ms
    )

    return {
        "encontrado": len(trechos) > 0,
        "resposta": resposta,
        "fontes": trechos,
        "tempo_resposta_ms": tempo_resposta_ms,
        "config_id": config_id,
        "top_k": top_k,
        "modelo_gerador": modelo_gerador
    }