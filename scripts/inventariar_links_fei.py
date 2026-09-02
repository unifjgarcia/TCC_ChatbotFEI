import csv
import os
from datetime import date
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


URL_BASE = "https://portal.fei.edu.br"
PASTA_DADOS = "dados"
CAMINHO_INVENTARIO = "dados\inventario_links_fei.csv"


PALAVRAS_SERVICOS_ALUNO = [
    "aluno",
    "secretaria",
    "tesouraria",
    "bolsa",
    "bolsas",
    "estagio",
    "estágio",
    "biblioteca",
    "diploma",
    "documento",
    "documentos",
    "portal",
    "moodle",
    "calendario",
    "calendário",
    "manual",
    "matricula",
    "matrícula",
]

PALAVRAS_CURSOS_GRADUACAO = [
    "curso",
    "graduacao",
    "graduação",
    "ciencia-da-computacao",
    "engenharia",
    "administracao",
    "ciencia-de-dados",
]

PALAVRAS_INSTITUCIONAL = [
    "corpo-diretivo",
    "corpo-docente",
    "avaliacoes-institucionais",
    "campus",
    "historia",
    "mantenedora",
    "cpa",
    "legislacao",
]

PALAVRAS_FORA_ESCOPO = [
    "aerodesign",
    "aiche",
    "atletica",
    "atlética",
    "alumni",
    "clube",
    "concreto",
    "cursinho",
    "produtividade",
    "cnpq",
]


def baixar_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TCC-FEI-RAG/1.0)"
    }

    resposta = requests.get(url, headers=headers, timeout=20)
    resposta.raise_for_status()

    return resposta.text


def extrair_titulo(soup, url):
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return url


def normalizar_url(url):
    url = url.strip()
    url = url.split("#")[0]
    url = url.rstrip("/")
    return url


def url_eh_do_site_fei(url):
    dominio = urlparse(url).netloc
    return dominio == "portal.fei.edu.br"


def classificar_url(url, titulo):
    texto = f"{url} {titulo}".lower()

    if any(palavra in texto for palavra in [
        "secretaria",
        "servicos",
        "serviços",
        "nae",
        "nucleo-de-apoio",
        "fretados",
        "transferencia",
        "portador",
        "biblioteca",
        "moodle",
        "portal",
        "aluno",
        "fale-conosco"
    ]):
        return "Serviços ao aluno / Administrativo"

    if any(palavra in texto for palavra in [
        "tesouraria",
        "bolsas",
        "bolsa",
        "credito",
        "crédito",
        "financeiro"
    ]):
        return "Financeiro / Bolsas"

    if any(palavra in texto for palavra in [
        "estagio",
        "estágio",
        "emprego"
    ]):
        return "Estágio e emprego"

    if any(palavra in texto for palavra in [
        "diploma",
        "documento",
        "documentos",
        "validacao",
        "validação",
        "consulta-diplomas",
        "curriculos",
        "currículos"
    ]):
        return "Documentos e validações"

    if any(palavra in texto for palavra in [
        "graduacao",
        "graduação",
        "curso",
        "ciencia-da-computacao",
        "administracao",
        "engenharia",
        "ciencia-de-dados",
        "transferencia-portador",
        "provas-anteriores"
    ]):
        return "Cursos / Graduação / Ingresso"

    if any(palavra in texto for palavra in [
        "iniciacao",
        "iniciação",
        "pibic",
        "pibiti",
        "cnpq",
        "pesquisa",
        "mestrado",
        "doutorado",
        "programas-de-iniciacao",
        "vagas-de-iniciacao"
    ]):
        return "Pesquisa / Pós-graduação"

    if any(palavra in texto for palavra in [
        "corpo-diretivo",
        "corpo-docente",
        "avaliacoes-institucionais",
        "campus",
        "historia",
        "mantenedora",
        "missao",
        "legislacao",
        "cpa"
    ]):
        return "Institucional"

    if any(palavra in texto for palavra in [
        "aerodesign",
        "aiche",
        "atletica",
        "atlética",
        "alumni",
        "clube",
        "concreto",
        "baja",
        "formula",
        "robo",
        "maratona",
        "junior-fei",
        "pastoral",
        "esporte",
        "lazer",
        "compositos",
        "sampe"
    ]):
        return "Projetos / Entidades / Provável fora do escopo"

    if any(palavra in texto for palavra in [
        "noticia",
        "noticias",
        "eventos",
        "sala-de-imprensa"
    ]):
        return "Notícias / Eventos"

    return "Para validação"

def coletar_links_da_pagina(html, url_origem):
    soup = BeautifulSoup(html, "html.parser")
    links = set()

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()

        if not href:
            continue

        url_completa = urljoin(url_origem, href)
        url_completa = normalizar_url(url_completa)

        if url_eh_do_site_fei(url_completa):
            links.add(url_completa)

    return links


def main():
    os.makedirs(PASTA_DADOS, exist_ok=True)

    print("Coletando links da página inicial...")
    html_inicial = baixar_html(URL_BASE)

    links_encontrados = coletar_links_da_pagina(html_inicial, URL_BASE)

    # Inclui a página inicial também
    links_encontrados.add(URL_BASE)

    registros = []

    for indice, url in enumerate(sorted(links_encontrados), start=1):
        try:
            print(f"Analisando {indice}: {url}")

            html = baixar_html(url)
            soup = BeautifulSoup(html, "html.parser")
            titulo = extrair_titulo(soup, url)

            categoria_sugerida = classificar_url(url, titulo)

            registros.append({
                "id": f"LINK{indice:03d}",
                "titulo": titulo,
                "url": url,
                "categoria_sugerida": categoria_sugerida,
                "status_curadoria": "A avaliar",
                "prioridade": "",
                "responsavel_validacao": "",
                "observacoes": "",
                "data_mapeamento": date.today().isoformat()
            })

        except Exception as erro:
            registros.append({
                "id": f"LINK{indice:03d}",
                "titulo": "",
                "url": url,
                "categoria_sugerida": "Erro na leitura",
                "status_curadoria": "A avaliar",
                "prioridade": "",
                "responsavel_validacao": "",
                "observacoes": str(erro),
                "data_mapeamento": date.today().isoformat()
            })

    colunas = [
        "id",
        "titulo",
        "url",
        "categoria_sugerida",
        "status_curadoria",
        "prioridade",
        "responsavel_validacao",
        "observacoes",
        "data_mapeamento"
    ]

    with open(CAMINHO_INVENTARIO, "w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(registros)

    print("\nInventário finalizado.")
    print(f"Total de links mapeados: {len(registros)}")
    print(f"Arquivo gerado: {CAMINHO_INVENTARIO}")


if __name__ == "__main__":
    main()