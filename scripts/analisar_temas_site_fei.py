import csv
import os
import re
from collections import defaultdict
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


CAMINHO_INVENTARIO = "dados/inventario_links_fei.csv"
CAMINHO_ANALISE = "dados/analise_temas_fei.csv"
CAMINHO_RESUMO = "dados/resumo_temas_fei.csv"


TEMAS = {
    "Serviços ao aluno / Administrativo": [
        "aluno", "alunos", "secretaria", "serviços", "servicos",
        "atendimento", "requerimento", "solicitação", "solicitacao",
        "portal do aluno", "moodle", "nae", "apoio ao estudante",
        "fretados", "transporte", "campus"
    ],
    "Documentos e validações": [
        "documento", "documentos", "diploma", "histórico", "historico",
        "declaração", "declaracao", "certificado", "validação",
        "validacao", "assinatura eletrônica", "assinatura eletronica",
        "consulta de diplomas", "diploma digital", "currículo", "curriculo"
    ],
    "Financeiro / Bolsas": [
        "tesouraria", "financeiro", "bolsa", "bolsas",
        "mensalidade", "pagamento", "crédito educativo",
        "credito educativo", "desconto", "financiamento"
    ],
    "Estágio e emprego": [
        "estágio", "estagio", "emprego", "carreira", "empresa",
        "vagas", "oportunidades", "termo de compromisso",
        "relatório de estágio", "relatorio de estagio"
    ],
    "Graduação / Ingresso / Cursos": [
        "graduação", "graduacao", "curso", "cursos",
        "vestibular", "transferência", "transferencia",
        "portador de diploma", "provas anteriores",
        "matriz curricular", "disciplina", "disciplinas",
        "administração", "administracao", "ciência da computação",
        "ciencia da computacao", "engenharia", "ciência de dados",
        "ciencia de dados"
    ],
    "Institucional": [
        "história", "historia", "missão", "missao",
        "mantenedora", "legislação", "legislacao",
        "corpo docente", "corpo diretivo", "campus",
        "avaliações institucionais", "avaliacoes institucionais",
        "são bernardo", "sao bernardo", "são paulo", "sao paulo"
    ],
    "Pesquisa / Iniciação / Pós-graduação": [
        "pesquisa", "iniciação científica", "iniciacao cientifica",
        "iniciação tecnológica", "iniciacao tecnologica",
        "iniciação didática", "iniciacao didatica",
        "pibic", "pibiti", "cnpq", "mestrado", "doutorado",
        "pós-graduação", "pos-graduacao", "pós graduação", "pos graduacao"
    ],
    "Projetos / Entidades / Extensão": [
        "aerodesign", "aiche", "atlética", "atletica",
        "clube estudantil", "baja", "fórmula", "formula",
        "robô", "robo", "junior fei", "pastoral",
        "representação estudantil", "representacao estudantil",
        "esporte", "lazer", "concreto", "sampe", "extensão", "extensao"
    ],
    "Notícias / Eventos": [
        "notícia", "noticia", "notícias", "noticias",
        "evento", "eventos", "sala de imprensa", "congresso"
    ]
}

def baixar_html(url):
    url = url.strip()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TCC-FEI-RAG/1.0)"
    }

    resposta = requests.get(url, headers=headers, timeout=8)
    resposta.raise_for_status()

    return resposta.text


def limpar_texto_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    texto = soup.get_text(separator=" ")

    texto = re.sub(r"\s+", " ", texto)
    texto = texto.strip()

    return texto


def normalizar_texto(texto):
    texto = texto.lower()

    substituicoes = {
        "á": "a", "à": "a", "ã": "a", "â": "a",
        "é": "e", "ê": "e",
        "í": "i",
        "ó": "o", "ô": "o", "õ": "o",
        "ú": "u",
        "ç": "c"
    }

    for original, novo in substituicoes.items():
        texto = texto.replace(original, novo)

    return texto


def contar_palavras(texto):
    palavras = re.findall(r"\b\w+\b", texto)
    return len(palavras)


def calcular_score_tema(texto, palavras_chave):
    texto_norm = normalizar_texto(texto)

    score = 0
    termos_encontrados = []

    for termo in palavras_chave:
        termo_norm = normalizar_texto(termo)

        ocorrencias = texto_norm.count(termo_norm)

        if ocorrencias > 0:
            score += ocorrencias
            termos_encontrados.append(f"{termo} ({ocorrencias})")

    return score, "; ".join(termos_encontrados)


def analisar_pagina(registro):
    url = registro["url"]
    titulo = registro.get("titulo", "")

    html = baixar_html(url)
    texto = limpar_texto_html(html)

    qtd_palavras = contar_palavras(texto)
    qtd_caracteres = len(texto)

    scores = {}
    termos_por_tema = {}

    for tema, palavras_chave in TEMAS.items():
        score, termos = calcular_score_tema(texto, palavras_chave)
        scores[tema] = score
        termos_por_tema[tema] = termos

    tema_principal = max(scores, key=scores.get)
    score_principal = scores[tema_principal]

    if score_principal == 0:
        tema_principal = "Sem tema identificado"

    return {
        "id": registro.get("id", ""),
        "titulo": titulo,
        "url": url,
        "tema_sugerido_anterior": registro.get("categoria_sugerida", ""),
        "tema_principal_por_conteudo": tema_principal,
        "score_tema_principal": score_principal,
        "qtd_palavras": qtd_palavras,
        "qtd_caracteres": qtd_caracteres,
        "termos_encontrados_tema_principal": termos_por_tema.get(tema_principal, ""),
        "status_curadoria": "A avaliar",
        "prioridade": "",
        "observacoes": "",
        **{f"score_{tema}": scores[tema] for tema in TEMAS.keys()}
    }


def ler_inventario():
    with open(CAMINHO_INVENTARIO, "r", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_csv(caminho, registros, colunas):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(registros)


def gerar_resumo(registros_analise):
    resumo = defaultdict(lambda: {
        "tema": "",
        "qtd_paginas": 0,
        "total_palavras": 0,
        "total_caracteres": 0,
        "maior_score": 0,
        "pagina_maior_score": "",
        "url_pagina_maior_score": ""
    })

    for item in registros_analise:
        tema = item["tema_principal_por_conteudo"]

        resumo[tema]["tema"] = tema
        resumo[tema]["qtd_paginas"] += 1
        resumo[tema]["total_palavras"] += int(item["qtd_palavras"])
        resumo[tema]["total_caracteres"] += int(item["qtd_caracteres"])

        score = int(item["score_tema_principal"])

        if score > resumo[tema]["maior_score"]:
            resumo[tema]["maior_score"] = score
            resumo[tema]["pagina_maior_score"] = item["titulo"]
            resumo[tema]["url_pagina_maior_score"] = item["url"]

    registros_resumo = []

    for tema, dados in resumo.items():
        qtd_paginas = dados["qtd_paginas"]

        media_palavras = 0
        if qtd_paginas > 0:
            media_palavras = round(dados["total_palavras"] / qtd_paginas, 2)

        registros_resumo.append({
            "tema": tema,
            "qtd_paginas": qtd_paginas,
            "total_palavras": dados["total_palavras"],
            "media_palavras_por_pagina": media_palavras,
            "maior_score": dados["maior_score"],
            "pagina_maior_score": dados["pagina_maior_score"],
            "url_pagina_maior_score": dados["url_pagina_maior_score"],
            "observacao_curadoria": ""
        })

    registros_resumo = sorted(
        registros_resumo,
        key=lambda x: x["total_palavras"],
        reverse=True
    )

    return registros_resumo


def main():
    if not os.path.exists(CAMINHO_INVENTARIO):
        print(f"Arquivo não encontrado: {CAMINHO_INVENTARIO}")
        print("Rode primeiro: python scripts\\inventariar_links_fei.py")
        return

    inventario = ler_inventario()

    registros_analise = []

    print(f"Total de páginas no inventário: {len(inventario)}")

    for indice, registro in enumerate(inventario, start=1):
        url = registro["url"]

        try:
            print(f"Analisando conteúdo {indice}/{len(inventario)}: {url}")

            resultado = analisar_pagina(registro)
            registros_analise.append(resultado)

        except Exception as erro:
            print(f"Erro ao analisar {url}: {erro}")

            registros_analise.append({
                "id": registro.get("id", ""),
                "titulo": registro.get("titulo", ""),
                "url": url,
                "tema_sugerido_anterior": registro.get("categoria_sugerida", ""),
                "tema_principal_por_conteudo": "Erro na análise",
                "score_tema_principal": 0,
                "qtd_palavras": 0,
                "qtd_caracteres": 0,
                "termos_encontrados_tema_principal": "",
                "status_curadoria": "A avaliar",
                "prioridade": "",
                "observacoes": str(erro),
                **{f"score_{tema}": 0 for tema in TEMAS.keys()}
            })

    colunas_analise = [
        "id",
        "titulo",
        "url",
        "tema_sugerido_anterior",
        "tema_principal_por_conteudo",
        "score_tema_principal",
        "qtd_palavras",
        "qtd_caracteres",
        "termos_encontrados_tema_principal",
        "status_curadoria",
        "prioridade",
        "observacoes",
    ] + [f"score_{tema}" for tema in TEMAS.keys()]

    salvar_csv(CAMINHO_ANALISE, registros_analise, colunas_analise)

    resumo = gerar_resumo(registros_analise)

    colunas_resumo = [
        "tema",
        "qtd_paginas",
        "total_palavras",
        "media_palavras_por_pagina",
        "maior_score",
        "pagina_maior_score",
        "url_pagina_maior_score",
        "observacao_curadoria"
    ]

    salvar_csv(CAMINHO_RESUMO, resumo, colunas_resumo)

    print("\nAnálise finalizada.")
    print(f"Arquivo página por página: {CAMINHO_ANALISE}")
    print(f"Arquivo resumo por tema: {CAMINHO_RESUMO}")


if __name__ == "__main__":
    main()