from functools import lru_cache
import re
import unicodedata

import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer


PASTA_CHROMA = "dados/chroma_db_fei"
CAMINHO_CHUNKS = "dados/chunks_documentais_langchain.csv"
MODELO_EMBEDDINGS = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"


@lru_cache(maxsize=1)
def carregar_modelo():
    return SentenceTransformer(MODELO_EMBEDDINGS)


@lru_cache(maxsize=1)
def carregar_cliente_chroma():
    return chromadb.PersistentClient(path=PASTA_CHROMA)


@lru_cache(maxsize=1)
def carregar_chunks_csv():
    df = pd.read_csv(CAMINHO_CHUNKS)
    df["texto_chunk"] = df["texto_chunk"].astype(str)
    df["titulo"] = df["titulo"].astype(str)
    df["categoria"] = df["categoria"].astype(str)
    df["url"] = df["url"].astype(str)
    df["chunk_id"] = df["chunk_id"].astype(str)
    df["config_id"] = df["config_id"].astype(str)
    return df


def obter_nome_colecao(config_id):
    return f"fei_chunks_{config_id.lower()}"


def normalizar_texto(texto):
    texto = str(texto).lower()

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def extrair_termos_busca(pergunta):
    pergunta_normalizada = normalizar_texto(pergunta)

    palavras_ignoradas = {
        "a", "o", "os", "as", "um", "uma", "uns", "umas",
        "de", "da", "do", "das", "dos",
        "em", "no", "na", "nos", "nas",
        "para", "pra", "por", "com", "sem",
        "que", "qual", "quais", "como", "onde",
        "tem", "existe", "possui", "sobre",
        "eu", "me", "meu", "minha", "meus", "minhas",
        "fei"
    }

    termos = []

    for palavra in pergunta_normalizada.split():
        if len(palavra) >= 3 and palavra not in palavras_ignoradas:
            termos.append(palavra)

    return termos


def calcular_score_palavra_chave(pergunta, linha):
    termos = extrair_termos_busca(pergunta)

    if not termos:
        return 0

    titulo = normalizar_texto(linha["titulo"])
    categoria = normalizar_texto(linha["categoria"])
    texto = normalizar_texto(linha["texto_chunk"])

    score = 0

    for termo in termos:
        if termo in titulo:
            score += 5

        if termo in categoria:
            score += 3

        if termo in texto:
            score += 1

    return score


def buscar_por_palavra_chave(pergunta, config_id, limite=20):
    df = carregar_chunks_csv()
    df_config = df[df["config_id"] == config_id].copy()

    resultados = []

    for _, linha in df_config.iterrows():
        score = calcular_score_palavra_chave(pergunta, linha)

        if score > 0:
            resultados.append({
                "chunk_id": linha["chunk_id"],
                "texto": linha["texto_chunk"],
                "distancia": None,
                "doc_id": linha["doc_id"],
                "titulo": linha["titulo"],
                "categoria": linha["categoria"],
                "prioridade": linha["prioridade"],
                "url": linha["url"],
                "config_id": linha["config_id"],
                "chunk_size": int(linha["chunk_size"]),
                "chunk_overlap": int(linha["chunk_overlap"]),
                "ordem_chunk": int(linha["ordem_chunk"]),
                "score_palavra_chave": score,
                "origem_busca": "palavra-chave"
            })

    resultados = sorted(
        resultados,
        key=lambda item: item["score_palavra_chave"],
        reverse=True
    )

    return resultados[:limite]


def buscar_por_vetor(pergunta, top_k, config_id):
    modelo = carregar_modelo()
    cliente = carregar_cliente_chroma()

    nome_colecao = obter_nome_colecao(config_id)
    colecao = cliente.get_collection(name=nome_colecao)

    embedding_pergunta = modelo.encode([pergunta]).tolist()

    quantidade_busca = max(top_k, 20)

    resultados = colecao.query(
        query_embeddings=embedding_pergunta,
        n_results=quantidade_busca,
        include=["documents", "metadatas", "distances"]
    )

    trechos = []

    ids = resultados["ids"][0]
    documentos = resultados["documents"][0]
    metadados = resultados["metadatas"][0]
    distancias = resultados["distances"][0]

    textos_originais = obter_textos_originais_por_chunk(config_id)

    for chunk_id, texto, metadata, distancia in zip(
        ids,
        documentos,
        metadados,
        distancias
    ):
        texto_original = textos_originais.get(chunk_id, texto)

        trechos.append({
            "chunk_id": chunk_id,
            "texto": texto_original,
            "distancia": distancia,
            "doc_id": metadata.get("doc_id"),
            "titulo": metadata.get("titulo"),
            "categoria": metadata.get("categoria"),
            "prioridade": metadata.get("prioridade"),
            "url": metadata.get("url"),
            "config_id": metadata.get("config_id"),
            "chunk_size": metadata.get("chunk_size"),
            "chunk_overlap": metadata.get("chunk_overlap"),
            "ordem_chunk": metadata.get("ordem_chunk"),
            "score_palavra_chave": calcular_score_palavra_chave(pergunta, {
                "titulo": metadata.get("titulo", ""),
                "categoria": metadata.get("categoria", ""),
                "texto_chunk": texto_original
            }),
            "origem_busca": "vetorial"
        })

    return trechos


def obter_textos_originais_por_chunk(config_id):
    df = carregar_chunks_csv()
    df_config = df[df["config_id"] == config_id]

    return dict(
        zip(
            df_config["chunk_id"].astype(str),
            df_config["texto_chunk"].astype(str)
        )
    )


def combinar_resultados(resultados_vetoriais, resultados_palavra_chave, top_k):
    combinados = {}

    for posicao, item in enumerate(resultados_vetoriais, start=1):
        chunk_id = item["chunk_id"]

        score_vetorial = max(0, 30 - posicao)
        score_keyword = item.get("score_palavra_chave") or 0

        item["score_final"] = score_vetorial + (score_keyword * 3)
        item["origem_busca"] = "vetorial"

        combinados[chunk_id] = item

    for item in resultados_palavra_chave:
        chunk_id = item["chunk_id"]

        score_keyword = item.get("score_palavra_chave") or 0
        score_final = score_keyword * 6

        if chunk_id in combinados:
            combinados[chunk_id]["score_final"] += score_final
            combinados[chunk_id]["origem_busca"] = "hibrida"
            combinados[chunk_id]["score_palavra_chave"] = max(
                combinados[chunk_id].get("score_palavra_chave") or 0,
                score_keyword
            )
        else:
            item["score_final"] = score_final
            combinados[chunk_id] = item

    lista_final = list(combinados.values())

    lista_final = sorted(
        lista_final,
        key=lambda item: item.get("score_final", 0),
        reverse=True
    )

    return lista_final[:top_k]


def buscar_trechos(pergunta, top_k=3, config_id="C5"):
    resultados_vetoriais = buscar_por_vetor(
        pergunta=pergunta,
        top_k=top_k,
        config_id=config_id
    )

    resultados_palavra_chave = buscar_por_palavra_chave(
        pergunta=pergunta,
        config_id=config_id,
        limite=20
    )

    resultados_finais = combinar_resultados(
        resultados_vetoriais=resultados_vetoriais,
        resultados_palavra_chave=resultados_palavra_chave,
        top_k=top_k
    )

    return resultados_finais