import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

MODELO_GEMINI = "gemini-3.6-flash"


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


def gerar_resposta_com_gemini(pergunta, trechos):
    if not trechos:
        return (
            "Não encontrei informações suficientes na base documental da FEI "
            "para responder essa pergunta."
        )

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return (
            "A chave da Gemini API não foi encontrada. Verifique se o arquivo .env "
            "possui a variável GEMINI_API_KEY."
        )

    contexto = montar_contexto(trechos)

    prompt = f"""
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
- Quando a pergunta envolver dados objetivos, como endereço, telefone, prazo, valor, horário, e-mail ou documento, preserve esses dados completos exatamente como aparecem no contexto.
Pergunta do usuário:
{pergunta}

Contexto recuperado:
{contexto}

Resposta:
"""

    client = genai.Client(api_key=api_key)

    resposta = client.models.generate_content(
        model=MODELO_GEMINI,
        contents=prompt
    )

    if not resposta.text:
        return "Não foi possível gerar uma resposta com o Gemini."

    return resposta.text.strip()