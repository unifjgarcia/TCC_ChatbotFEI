import csv
import os
import re
from collections import defaultdict

import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


CAMINHO_INVENTARIO = "dados/inventario_links_fei.csv"
CAMINHO_ANALISE = "dados/analise_temas_semantica_fei.csv"
CAMINHO_RESUMO = "dados/resumo_temas_semantica_fei.csv"


# Modelo multilíngue, melhor para português do que modelos só em inglês
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


TEMAS = {
    "Serviços ao aluno / Administrativo": """
    Páginas relacionadas a serviços de apoio ao estudante, atendimento acadêmico,
    secretaria, solicitações administrativas, canais de atendimento, portal do aluno,
    Moodle, suporte ao estudante, NAE, transporte, fretados, biblioteca e orientação
    geral para alunos da instituição.
    """,

    "Documentos e validações": """
    Páginas relacionadas a documentos acadêmicos, diplomas, diploma digital,
    validação eletrônica de documentos, consulta de diplomas, certificados,
    declarações, histórico escolar, comprovantes, currículos e documentos oficiais
    emitidos ou validados pela instituição.
    """,

    "Financeiro / Bolsas": """
    Páginas relacionadas a tesouraria, financeiro, bolsas de estudo, crédito educativo,
    mensalidades, pagamentos, descontos, financiamento estudantil e informações
    financeiras gerais disponíveis publicamente para estudantes.
    """,

    "Estágio e emprego": """
    Páginas relacionadas a estágio, emprego, carreira, vagas, oportunidades profissionais,
    empresas, setor de estágios, empregabilidade, termo de compromisso, relatórios de
    estágio e apoio institucional à inserção profissional dos estudantes.
    """,

    "Graduação / Ingresso / Cursos": """
    Páginas relacionadas a cursos de graduação, formas de ingresso, vestibular,
    transferência, portador de diploma, provas anteriores, matriz curricular,
    disciplinas, administração, ciência da computação, ciência de dados, engenharias
    e informações sobre cursos oferecidos pela instituição.
    """,

    "Institucional": """
    Páginas relacionadas à instituição FEI, sua história, missão, mantenedora,
    legislação, corpo docente, corpo diretivo, avaliações institucionais, campi,
    unidades de São Bernardo do Campo e São Paulo, estrutura institucional e
    informações gerais sobre a universidade.
    """,

    "Pesquisa / Iniciação / Pós-graduação": """
    Páginas relacionadas a pesquisa acadêmica, iniciação científica, iniciação
    tecnológica, iniciação didática, PIBIC, PIBITI, CNPq, mestrado, doutorado,
    pós-graduação, programas de pesquisa, vagas de iniciação e produção científica.
    """,

    "Projetos / Entidades / Extensão": """
    Páginas relacionadas a projetos estudantis, entidades, equipes de competição,
    extensão universitária, Atlética, Aerodesign, Baja, Fórmula FEI, Robô FEI,
    AIChE, Clube Estudantil, Pastoral, Representação Estudantil, esporte, lazer,
    atividades extracurriculares e grupos organizados de estudantes.
    """,

    "Notícias / Eventos": """
    Páginas relacionadas a notícias, eventos, comunicados, sala de imprensa,
    congressos, divulgação institucional, agenda de eventos e publicações temporais
    ou informativas do portal.
    """
}


def baixar_html(url):
    url = url.strip()

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TCC-FEI-RAG/1.0)"
    }

    resposta = requests.get(url, headers=headers, timeout=12)
    resposta.raise_for_status()

    return resposta.text


def extrair_titulo(soup, url):
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return url


def limpar_texto_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    texto = soup.get_text(separator=" ")
    texto = re.sub(r"\s+", " ", texto)
    texto = texto.strip()

    return texto


def limitar_texto(texto, limite_caracteres=6000):
    """
    Limita o texto para evitar páginas grandes demais.
    Para classificação temática, os primeiros milhares de caracteres costumam ser suficientes.
    """
    return texto[:limite_caracteres]


def contar_palavras(texto):
    palavras = re.findall(r"\b\w+\b", texto)
    return len(palavras)


def ler_inventario():
    with open(CAMINHO_INVENTARIO, "r", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_csv(caminho, registros, colunas):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(registros)


def gerar_resumo(registros):
    resumo = defaultdict(lambda: {
        "tema": "",
        "qtd_paginas": 0,
        "total_palavras": 0,
        "soma_similaridade": 0.0,
        "maior_similaridade": 0.0,
        "pagina_maior_similaridade": "",
        "url_pagina_maior_similaridade": ""
    })

    for item in registros:
        tema = item["tema_principal_semantico"]

        resumo[tema]["tema"] = tema
        resumo[tema]["qtd_paginas"] += 1
        resumo[tema]["total_palavras"] += int(item["qtd_palavras"])
        resumo[tema]["soma_similaridade"] += float(item["similaridade_principal"])

        similaridade = float(item["similaridade_principal"])

        if similaridade > resumo[tema]["maior_similaridade"]:
            resumo[tema]["maior_similaridade"] = similaridade
            resumo[tema]["pagina_maior_similaridade"] = item["titulo"]
            resumo[tema]["url_pagina_maior_similaridade"] = item["url"]

    registros_resumo = []

    for tema, dados in resumo.items():
        qtd_paginas = dados["qtd_paginas"]

        media_palavras = 0
        media_similaridade = 0

        if qtd_paginas > 0:
            media_palavras = round(dados["total_palavras"] / qtd_paginas, 2)
            media_similaridade = round(dados["soma_similaridade"] / qtd_paginas, 4)

        registros_resumo.append({
            "tema": tema,
            "qtd_paginas": qtd_paginas,
            "total_palavras": dados["total_palavras"],
            "media_palavras_por_pagina": media_palavras,
            "media_similaridade": media_similaridade,
            "maior_similaridade": round(dados["maior_similaridade"], 4),
            "pagina_maior_similaridade": dados["pagina_maior_similaridade"],
            "url_pagina_maior_similaridade": dados["url_pagina_maior_similaridade"],
            "observacao_curadoria": ""
        })

    registros_resumo = sorted(
        registros_resumo,
        key=lambda x: x["qtd_paginas"],
        reverse=True
    )

    return registros_resumo


def main():
    if not os.path.exists(CAMINHO_INVENTARIO):
        print(f"Arquivo não encontrado: {CAMINHO_INVENTARIO}")
        print("Rode primeiro: python scripts\\inventariar_links_fei.py")
        return

    print("Carregando modelo de embeddings...")
    print(f"Modelo: {MODELO_EMBEDDINGS}")

    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    nomes_temas = list(TEMAS.keys())
    descricoes_temas = [TEMAS[tema] for tema in nomes_temas]

    print("Gerando embeddings dos temas...")
    embeddings_temas = modelo.encode(descricoes_temas)

    inventario = ler_inventario()

    print(f"Total de páginas no inventário: {len(inventario)}")

    registros_analise = []

    for indice, registro in enumerate(inventario, start=1):
        url = registro["url"].strip()

        try:
            print(f"Analisando semanticamente {indice}/{len(inventario)}: {url}")

            html = baixar_html(url)
            soup = BeautifulSoup(html, "html.parser")

            titulo = registro.get("titulo", "").strip()

            if not titulo:
                titulo = extrair_titulo(soup, url)

            texto = limpar_texto_html(html)
            texto_para_embedding = limitar_texto(texto)

            qtd_palavras = contar_palavras(texto)
            qtd_caracteres = len(texto)

            if qtd_palavras < 20:
                registros_analise.append({
                    "id": registro.get("id", ""),
                    "titulo": titulo,
                    "url": url,
                    "tema_sugerido_anterior": registro.get("categoria_sugerida", ""),
                    "tema_principal_semantico": "Pouco conteúdo textual",
                    "similaridade_principal": 0,
                    "segundo_tema_semantico": "",
                    "similaridade_segundo_tema": 0,
                    "qtd_palavras": qtd_palavras,
                    "qtd_caracteres": qtd_caracteres,
                    "status_curadoria": "A avaliar",
                    "prioridade": "",
                    "observacoes": "Página com pouco conteúdo textual extraído",
                    **{f"sim_{tema}": 0 for tema in nomes_temas}
                })
                continue

            embedding_pagina = modelo.encode([texto_para_embedding])

            similaridades = cosine_similarity(embedding_pagina, embeddings_temas)[0]

            ranking = sorted(
                zip(nomes_temas, similaridades),
                key=lambda x: x[1],
                reverse=True
            )

            tema_principal, sim_principal = ranking[0]
            segundo_tema, sim_segundo = ranking[1]

            valores_similaridade = {
                f"sim_{tema}": round(float(sim), 4)
                for tema, sim in zip(nomes_temas, similaridades)
            }

            registros_analise.append({
                "id": registro.get("id", ""),
                "titulo": titulo,
                "url": url,
                "tema_sugerido_anterior": registro.get("categoria_sugerida", ""),
                "tema_principal_semantico": tema_principal,
                "similaridade_principal": round(float(sim_principal), 4),
                "segundo_tema_semantico": segundo_tema,
                "similaridade_segundo_tema": round(float(sim_segundo), 4),
                "qtd_palavras": qtd_palavras,
                "qtd_caracteres": qtd_caracteres,
                "status_curadoria": "A avaliar",
                "prioridade": "",
                "observacoes": "",
                **valores_similaridade
            })

        except Exception as erro:
            print(f"Erro ao analisar {url}: {erro}")

            registros_analise.append({
                "id": registro.get("id", ""),
                "titulo": registro.get("titulo", ""),
                "url": url,
                "tema_sugerido_anterior": registro.get("categoria_sugerida", ""),
                "tema_principal_semantico": "Erro na análise",
                "similaridade_principal": 0,
                "segundo_tema_semantico": "",
                "similaridade_segundo_tema": 0,
                "qtd_palavras": 0,
                "qtd_caracteres": 0,
                "status_curadoria": "A avaliar",
                "prioridade": "",
                "observacoes": str(erro),
                **{f"sim_{tema}": 0 for tema in nomes_temas}
            })

    colunas_analise = [
        "id",
        "titulo",
        "url",
        "tema_sugerido_anterior",
        "tema_principal_semantico",
        "similaridade_principal",
        "segundo_tema_semantico",
        "similaridade_segundo_tema",
        "qtd_palavras",
        "qtd_caracteres",
        "status_curadoria",
        "prioridade",
        "observacoes",
    ] + [f"sim_{tema}" for tema in nomes_temas]

    salvar_csv(CAMINHO_ANALISE, registros_analise, colunas_analise)

    resumo = gerar_resumo(registros_analise)

    colunas_resumo = [
        "tema",
        "qtd_paginas",
        "total_palavras",
        "media_palavras_por_pagina",
        "media_similaridade",
        "maior_similaridade",
        "pagina_maior_similaridade",
        "url_pagina_maior_similaridade",
        "observacao_curadoria"
    ]

    salvar_csv(CAMINHO_RESUMO, resumo, colunas_resumo)

    print("\nAnálise semântica finalizada.")
    print(f"Arquivo página por página: {CAMINHO_ANALISE}")
    print(f"Arquivo resumo por tema: {CAMINHO_RESUMO}")


if __name__ == "__main__":
    main()