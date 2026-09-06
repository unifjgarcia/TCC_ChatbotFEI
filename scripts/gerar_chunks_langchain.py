import csv
import os

from langchain_text_splitters import RecursiveCharacterTextSplitter


CAMINHO_METADADOS = "dados/base_documental_metadados.csv"
CAMINHO_CHUNKS = "dados/chunks_documentais_langchain.csv"


CONFIGURACOES_CHUNKING = [
    {"config_id": "C1", "chunk_size": 500, "chunk_overlap": 0},
    {"config_id": "C2", "chunk_size": 500, "chunk_overlap": 100},
    {"config_id": "C3", "chunk_size": 500, "chunk_overlap": 200},
    {"config_id": "C4", "chunk_size": 800, "chunk_overlap": 0},
    {"config_id": "C5", "chunk_size": 800, "chunk_overlap": 100},
    {"config_id": "C6", "chunk_size": 800, "chunk_overlap": 200},
    {"config_id": "C7", "chunk_size": 1200, "chunk_overlap": 0},
    {"config_id": "C8", "chunk_size": 1200, "chunk_overlap": 100},
    {"config_id": "C9", "chunk_size": 1200, "chunk_overlap": 200},
]


def ler_metadados():
    with open(CAMINHO_METADADOS, "r", encoding="utf-8-sig") as arquivo:
        leitor = csv.DictReader(arquivo)
        return list(leitor)


def ler_texto(caminho):
    with open(caminho, "r", encoding="utf-8") as arquivo:
        return arquivo.read()


def salvar_csv(caminho, registros, colunas):
    with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(registros)


def criar_splitter(chunk_size, chunk_overlap):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "? ",
            "! ",
            "; ",
            ", ",
            " ",
            ""
        ]
    )


def main():
    if not os.path.exists(CAMINHO_METADADOS):
        print(f"Arquivo não encontrado: {CAMINHO_METADADOS}")
        print("Rode primeiro: python scripts\\coletar_fontes_selecionadas.py")
        return

    metadados = ler_metadados()
    registros_chunks = []

    print(f"Total de documentos nos metadados: {len(metadados)}")

    for documento in metadados:
        doc_id = documento["id"]
        titulo = documento["titulo"]
        categoria = documento["categoria"]
        prioridade = documento["prioridade"]
        url = documento["url"]
        caminho_texto = documento["caminho_texto"]

        if not caminho_texto or not os.path.exists(caminho_texto):
            print(f"Pulando {doc_id}: texto não encontrado.")
            continue

        texto = ler_texto(caminho_texto).strip()

        if not texto:
            print(f"Pulando {doc_id}: texto vazio.")
            continue

        print(f"Gerando chunks para {doc_id}: {titulo}")

        for config in CONFIGURACOES_CHUNKING:
            splitter = criar_splitter(
                chunk_size=config["chunk_size"],
                chunk_overlap=config["chunk_overlap"]
            )

            chunks = splitter.split_text(texto)

            for indice, chunk in enumerate(chunks, start=1):
                registros_chunks.append({
                    "chunk_id": f"{doc_id}_{config['config_id']}_{indice:04d}",
                    "doc_id": doc_id,
                    "titulo": titulo,
                    "categoria": categoria,
                    "prioridade": prioridade,
                    "url": url,
                    "config_id": config["config_id"],
                    "chunk_size": config["chunk_size"],
                    "chunk_overlap": config["chunk_overlap"],
                    "ordem_chunk": indice,
                    "qtd_caracteres_chunk": len(chunk),
                    "texto_chunk": chunk
                })

    colunas = [
        "chunk_id",
        "doc_id",
        "titulo",
        "categoria",
        "prioridade",
        "url",
        "config_id",
        "chunk_size",
        "chunk_overlap",
        "ordem_chunk",
        "qtd_caracteres_chunk",
        "texto_chunk"
    ]

    salvar_csv(CAMINHO_CHUNKS, registros_chunks, colunas)

    print("\nChunking com LangChain finalizado.")
    print(f"Arquivo gerado: {CAMINHO_CHUNKS}")
    print(f"Total de chunks gerados: {len(registros_chunks)}")


if __name__ == "__main__":
    main()