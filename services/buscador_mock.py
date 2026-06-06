import json
import os


def carregar_base():
    """
    Carrega a base simulada de respostas a partir do arquivo JSON.
    """

    caminho_arquivo = os.path.join("dados", "respostas_mock.json")

    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    return dados


def buscar_resposta(pergunta):
    """
    Busca uma resposta na base simulada com base nas palavras-chave.

    A função percorre cada categoria do JSON e verifica se alguma
    palavra-chave aparece dentro da pergunta feita pelo aluno.
    """

    base = carregar_base()
    pergunta_normalizada = pergunta.lower()

    for item in base:
        for palavra in item["palavras_chave"]:
            if palavra.lower() in pergunta_normalizada:
                return {
                    "encontrado": True,
                    "categoria": item["categoria"],
                    "resposta": item["resposta"],
                    "fonte": item["fonte"],
                    "trecho_base": item["trecho_base"]
                }

    return {
        "encontrado": False,
        "categoria": "Não identificada",
        "resposta": "Não encontrei uma resposta adequada na base simulada para essa pergunta. Em uma versão futura, o sistema consultaria a base documental completa da instituição.",
        "fonte": "Nenhuma fonte encontrada",
        "trecho_base": "Nenhum trecho foi recuperado para essa pergunta."
    }