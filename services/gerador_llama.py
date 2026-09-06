from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

MODELO_LLAMA = "llama3.1:8b"


def montar_contexto(trechos):
    partes = []

    for indice, trecho in enumerate(trechos, start=1):
        partes.append(
            f"""
Fonte {indice}
Título: {trecho["titulo"]}
Categoria: {trecho["categoria"]}
URL: {trecho["url"]}
Trecho:
{trecho["texto"]}
"""
        )

    return "\n".join(partes)


def gerar_resposta_com_llama(pergunta, trechos):
    if not trechos:
        return (
            "Não encontrei informações suficientes na base documental da FEI "
            "para responder essa pergunta."
        )

    contexto = montar_contexto(trechos)

    prompt = ChatPromptTemplate.from_messages([
       (
    "system",
    """
Você é um assistente virtual acadêmico da FEI.

Sua função é responder dúvidas acadêmicas e administrativas com base exclusivamente no contexto recuperado da base documental.

Regras obrigatórias:
- Responda em português do Brasil.
- Use apenas as informações presentes no contexto recuperado.
- Não use conhecimento externo.
- Não invente informações.
- Responda exatamente ao que foi perguntado pelo usuário.
- Não inclua informações adicionais apenas porque elas aparecem no contexto.
- Priorize a informação mais direta e relevante para a pergunta.
- Se a pergunta for simples, responda de forma curta e objetiva.
- Se a pergunta pedir um procedimento, responda em etapas.
- Se a pergunta pedir comparação, organize a resposta comparando os pontos relevantes.
- Se o contexto recuperado não responder diretamente à pergunta, diga que não encontrou informação suficiente na base documental.
- Não exponha detalhes técnicos como chunk, embedding, ChromaDB, distância vetorial ou LangChain.
- Não diga que acessa dados pessoais, Portal do Aluno ou sistemas internos.
- Quando necessário, informe que a resposta deve ser confirmada nos canais oficiais da FEI.
"""
        ),
        (
            "human",
            """
Pergunta do usuário:
{pergunta}

Contexto recuperado:
{contexto}

Resposta:
"""
        )
    ])

    llm = ChatOllama(
        model=MODELO_LLAMA,
        temperature=0.2
    )

    chain = prompt | llm

    resposta = chain.invoke({
        "pergunta": pergunta,
        "contexto": contexto
    })

    return resposta.content.strip()