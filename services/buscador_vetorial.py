from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer


PASTA_CHROMA = "dados/chroma_db_fei"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def carregar_modelo():
    return SentenceTransformer(MODELO_EMBEDDINGS)


@lru_cache(maxsize=1)
def carregar_cliente_chroma():
    return chromadb.PersistentClient(path=PASTA_CHROMA)


def obter_nome_colecao(config_id):
    return f"fei_chunks_{config_id.lower()}"


def buscar_trechos(pergunta, top_k=3, config_id="C5"):
    modelo = carregar_modelo()
    cliente = carregar_cliente_chroma()

    nome_colecao = obter_nome_colecao(config_id)
    colecao = cliente.get_collection(name=nome_colecao)

    embedding_pergunta = modelo.encode([pergunta]).tolist()

    resultados = colecao.query(
        query_embeddings=embedding_pergunta,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    trechos = []

    ids = resultados["ids"][0]
    documentos = resultados["documents"][0]
    metadados = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    for chunk_id, texto, metadata, distancia in zip(
        ids,
        documentos,
        metadados,
        distancias
    ):
        trechos.append({
            "chunk_id": chunk_id,
            "texto": texto,
            "distancia": distancia,
            "doc_id": metadata.get("doc_id"),
            "titulo": metadata.get("titulo"),
            "categoria": metadata.get("categoria"),
            "prioridade": metadata.get("prioridade"),
            "url": metadata.get("url"),
            "config_id": metadata.get("config_id"),
            "chunk_size": metadata.get("chunk_size"),
            "chunk_overlap": metadata.get("chunk_overlap"),
            "ordem_chunk": metadata.get("ordem_chunk")
        })

    return trechos