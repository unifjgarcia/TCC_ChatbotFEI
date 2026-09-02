import os
import re
from datetime import date
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


URL_BASE = "https://portal.fei.edu.br/"
PALAVRAS_RELEVANTES = [
    "aluno",
    "alunos",
    "secretaria",
    "tesouraria",
    "financeiro",
    "matricula",
    "matrícula",
    "bolsas",
    "estagio",
    "estágio",
    "biblioteca",
    "calendario",
    "calendário",
    "documentos",
    "diploma",
    "manual",
    "regulamento",
    "graduacao",
    "graduação",
    "portal",
    "moodle",
]

PASTA_HTML = "documentos/html_bruto"
PASTA_TEXTO = "documentos/textos_limpos"
CAMINHO_CSV = "dados/fontes_documentais.csv"

def link_eh_relevante(url):
    url_minuscula = url.lower()

    return any(palavra in url_minuscula for palavra in PALAVRAS_RELEVANTES)

def limpar_nome_arquivo(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def extrair_titulo(soup, url):
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return url


def limpar_html(html):
    soup = BeautifulSoup(html, "html.parser")

    # Remove elementos que normalmente não ajudam na base documental
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    titulo = extrair_titulo(soup, "Sem título")

    texto = soup.get_text(separator="\n")

    linhas = [linha.strip() for linha in texto.splitlines()]
    linhas = [linha for linha in linhas if linha]

    texto_limpo = "\n".join(linhas)

    return titulo, texto_limpo


def url_eh_do_site_fei(url):
    dominio = urlparse(url).netloc
    return dominio == "portal.fei.edu.br"


def coletar_links_internos(html, url_origem):
    soup = BeautifulSoup(html, "html.parser")

    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        if not href:
            continue

        url_completa = urljoin(url_origem, href)

        # Remove espaços, âncoras e barra final duplicada
        url_completa = url_completa.strip()
        url_completa = url_completa.split("#")[0]
        url_completa = url_completa.rstrip("/")

        if url_eh_do_site_fei(url_completa):
            links.add(url_completa)

    return sorted(links)

def baixar_pagina(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TCC-FEI-RAG/1.0)"
    }

    resposta = requests.get(url, headers=headers, timeout=20)
    resposta.raise_for_status()

    return resposta.text


def salvar_documento(doc_id, url, html):
    soup = BeautifulSoup(html, "html.parser")
    titulo = extrair_titulo(soup, url)

    _, texto_limpo = limpar_html(html)

    nome_base = f"{doc_id}_{limpar_nome_arquivo(titulo)[:60]}"

    caminho_html = os.path.join(PASTA_HTML, f"{nome_base}.html")
    caminho_texto = os.path.join(PASTA_TEXTO, f"{nome_base}.txt")

    with open(caminho_html, "w", encoding="utf-8") as arquivo:
        arquivo.write(html)

    with open(caminho_texto, "w", encoding="utf-8") as arquivo:
        arquivo.write(texto_limpo)

    return {
        "id": doc_id,
        "titulo": titulo,
        "categoria": "A classificar",
        "tipo_documento": "HTML",
        "origem": "Portal institucional FEI",
        "url": url,
        "data_acesso": date.today().isoformat(),
        "status_validacao": "Pendente",
        "caminho_html": caminho_html,
        "caminho_texto": caminho_texto,
        "observacoes": "Coleta inicial por scraping com BeautifulSoup"
    }


def main():
    os.makedirs(PASTA_HTML, exist_ok=True)
    os.makedirs(PASTA_TEXTO, exist_ok=True)
    os.makedirs("dados", exist_ok=True)

    print(f"Coletando página inicial: {URL_BASE}")

    html_inicial = baixar_pagina(URL_BASE)

    links = coletar_links_internos(html_inicial, URL_BASE)

    # Para não coletar o site inteiro de primeira, vamos limitar.
    url_base_normalizada = URL_BASE.rstrip("/")

    links_filtrados = [
        link for link in links
        if link != url_base_normalizada and link_eh_relevante(link)
    ]

    links_para_coletar = [url_base_normalizada] + links_filtrados[:30]

    registros = []

    for indice, url in enumerate(links_para_coletar, start=1):
        doc_id = f"DOC{indice:03d}"

        try:
            print(f"Coletando {doc_id}: {url}")

            html = baixar_pagina(url)
            registro = salvar_documento(doc_id, url, html)
            registros.append(registro)

        except Exception as erro:
            print(f"Erro ao coletar {url}: {erro}")

    df = pd.DataFrame(registros)
    df.to_csv(CAMINHO_CSV, index=False, encoding="utf-8-sig")

    print("\nColeta finalizada.")
    print(f"Total de documentos coletados: {len(registros)}")
    print(f"Metadados salvos em: {CAMINHO_CSV}")


if __name__ == "__main__":
    main()