import pandas as pd
import chromadb

from sentence_transformers import SentenceTransformer


CAMINHO_CHUNKS = "dados/chunks_documentais_langchain.csv"
PASTA_CHROMA = "dados/chroma_db_fei"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


def preparar_metadados(linha):
    return {
        "doc_id": str(linha["doc_id"]),
        "titulo": str(linha["titulo"]),
        "categoria": str(linha["categoria"]),
        "prioridade": str(linha["prioridade"]),
        "url": str(linha["url"]),
        "config_id": str(linha["config_id"]),
        "chunk_size": int(linha["chunk_size"]),
        "chunk_overlap": int(linha["chunk_overlap"]),
        "ordem_chunk": int(linha["ordem_chunk"]),
        "qtd_caracteres_chunk": int(linha["qtd_caracteres_chunk"]),
    }


def main():
    print("Lendo chunks...")
    df = pd.read_csv(CAMINHO_CHUNKS)

    print(f"Total de chunks: {len(df)}")

    print("\nCarregando modelo de embeddings local...")
    print(f"Modelo: {MODELO_EMBEDDINGS}")
    modelo = SentenceTransformer(MODELO_EMBEDDINGS)

    cliente = chromadb.PersistentClient(path=PASTA_CHROMA)

    configs = sorted(df["config_id"].unique())

    for config_id in configs:
        nome_colecao = f"fei_chunks_{config_id.lower()}"
        df_config = df[df["config_id"] == config_id].copy()

        print("\n-----------------------------")
        print(f"Configuração: {config_id}")
        print(f"Coleção: {nome_colecao}")
        print(f"Chunks: {len(df_config)}")

        try:
            cliente.delete_collection(name=nome_colecao)
            print("Coleção antiga removida.")
        except Exception:
            print("Nenhuma coleção antiga encontrada.")

        colecao = cliente.create_collection(name=nome_colecao)

        textos = df_config["texto_chunk"].astype(str).tolist()
        ids = df_config["chunk_id"].astype(str).tolist()
        metadados = [
            preparar_metadados(linha)
            for _, linha in df_config.iterrows()
        ]

        print("Gerando embeddings...")
        embeddings = modelo.encode(
            textos,
            show_progress_bar=True
        ).tolist()

        print("Gravando no ChromaDB...")
        colecao.add(
            ids=ids,
            documents=textos,
            metadatas=metadados,
            embeddings=embeddings
        )

        print(f"Coleção criada com {colecao.count()} chunks.")

    print("\nTodas as bases vetoriais foram criadas.")
    print(f"Pasta: {PASTA_CHROMA}")


if __name__ == "__main__":
    main()