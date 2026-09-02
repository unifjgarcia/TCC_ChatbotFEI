import csv
import os
import re
from datetime import date

import requests
from bs4 import BeautifulSoup


CAMINHO_FONTES = "dados/fontes_selecionadas.csv"
CAMINHO_METADADOS = "dados/base_documental_metadados.csv"

PASTA_HTML = "documentos/html_bruto"
PASTA_TEXTO = "documentos/textos_limpos"


def limpar_nome_arquivo(texto):
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9]+", "_", texto)
    return texto.strip("_")


def baixar_html(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; TCC-FEI-RAG/1.0)"
    }

    resposta = requests.get(url.strip(), headers=headers, timeout=15)
    resposta.raise_for_status()

    return resposta.text


def limpar_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    texto = soup.get_text(separator="\n")

    linhas = [linha.strip() for linha in texto.splitlines()]
    linhas = [linha for linha in linhas if linha]

    texto_limpo = "\n".join(linhas)

    return texto_limpo


def ler_fontes():
    with open(CAMINHO_FONTES, "r", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def salvar_csv(caminho, registros, colunas):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(registros)


def main():
    os.makedirs(PASTA_HTML, exist_ok=True)
    os.makedirs(PASTA_TEXTO, exist_ok=True)

    fontes = ler_fontes()
    registros = []

    print(f"Total de fontes selecionadas: {len(fontes)}")

    for fonte in fontes:
        doc_id = fonte["id"]
        titulo = fonte["titulo"]
        categoria = fonte["categoria"]
        prioridade = fonte["prioridade"]
        url = fonte["url"]

        try:
            print(f"Coletando {doc_id}: {titulo}")

            html = baixar_html(url)
            texto_limpo = limpar_html(html)

            nome_base = f"{doc_id}_{limpar_nome_arquivo(titulo)[:60]}"

            caminho_html = os.path.join(PASTA_HTML, f"{nome_base}.html")
            caminho_texto = os.path.join(PASTA_TEXTO, f"{nome_base}.txt")

            with open(caminho_html, "w", encoding="utf-8") as arquivo:
                arquivo.write(html)

            with open(caminho_texto, "w", encoding="utf-8") as arquivo:
                arquivo.write(texto_limpo)

            registros.append({
                "id": doc_id,
                "titulo": titulo,
                "categoria": categoria,
                "prioridade": prioridade,
                "tipo_documento": "HTML",
                "origem": "Portal institucional FEI",
                "url": url,
                "data_acesso": date.today().isoformat(),
                "status_validacao": fonte["status_validacao"],
                "caminho_html": caminho_html,
                "caminho_texto": caminho_texto,
                "qtd_caracteres": len(texto_limpo),
                "qtd_linhas": len(texto_limpo.splitlines()),
                "observacoes": fonte["observacoes"]
            })

        except Exception as erro:
            print(f"Erro ao coletar {doc_id} - {url}: {erro}")

            registros.append({
                "id": doc_id,
                "titulo": titulo,
                "categoria": categoria,
                "prioridade": prioridade,
                "tipo_documento": "HTML",
                "origem": "Portal institucional FEI",
                "url": url,
                "data_acesso": date.today().isoformat(),
                "status_validacao": "Erro na coleta",
                "caminho_html": "",
                "caminho_texto": "",
                "qtd_caracteres": 0,
                "qtd_linhas": 0,
                "observacoes": str(erro)
            })

    colunas = [
        "id",
        "titulo",
        "categoria",
        "prioridade",
        "tipo_documento",
        "origem",
        "url",
        "data_acesso",
        "status_validacao",
        "caminho_html",
        "caminho_texto",
        "qtd_caracteres",
        "qtd_linhas",
        "observacoes"
    ]

    salvar_csv(CAMINHO_METADADOS, registros, colunas)

    print("\nColeta finalizada.")
    print(f"Metadados salvos em: {CAMINHO_METADADOS}")


if __name__ == "__main__":
    main()