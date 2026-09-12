import streamlit as st

from services.assistente_rag import responder_pergunta


st.set_page_config(
    page_title="Assistente Acadêmico FEI",
    page_icon="🎓",
    layout="centered"
)


st.title("🎓 Assistente Acadêmico FEI")
st.write("Tire suas dúvidas acadêmicas e administrativas com base em fontes públicas da FEI.")

st.info(
    "Este é um protótipo acadêmico. As respostas são geradas a partir da base documental "
    "coletada do portal público da FEI e não substituem os canais oficiais da instituição."
)

st.divider()


with st.sidebar:
    st.header("Configurações do teste")

    config_id = st.selectbox(
        "Configuração de chunking",
        options=["C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"],
        index=4
    )

    top_k = st.selectbox(
        "Quantidade de trechos recuperados",
        options=[3, 5, 8, 10],
        index=1
    )

    modelo_gerador = st.selectbox(
        "Modelo gerador",
        options=["llama3.1:8b", "gemini-3.6-flash"],
        index=0
    )

    st.caption(
        "Nesta versão, o sistema usa recuperação vetorial com ChromaDB "
        "e permite geração local com Llama via Ollama ou geração via Gemini API."
    )

    st.markdown("#### Configuração atual")
    st.write(f"Chunking: `{config_id}`")
    st.write(f"Top-k: `{top_k}`")
    st.write(f"Modelo: `{modelo_gerador}`")

    if st.button("Limpar conversa"):
        st.session_state.mensagens = []
        st.rerun()


if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


if not st.session_state.mensagens:
    st.markdown("#### Exemplos de perguntas")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("- Como funciona o diploma digital?")
        st.markdown("- Onde vejo informações sobre bolsas?")
        st.markdown("- Tem fretado pra FEI?")

    with col2:
        st.markdown("- Como entro em contato com a secretaria?")
        st.markdown("- Onde fica a FEI SBC?")
        st.markdown("- Onde encontro informações sobre estágio?")


for indice_mensagem, mensagem in enumerate(st.session_state.mensagens):
    with st.chat_message(mensagem["tipo"]):
        st.write(mensagem["conteudo"])

        if mensagem["tipo"] == "assistant" and mensagem.get("tempo_resposta_ms"):
            st.caption(f"Tempo de resposta: {mensagem['tempo_resposta_ms']} ms")

        if mensagem["tipo"] == "assistant" and mensagem.get("config_id"):
            st.caption(
                f"Configuração usada: {mensagem['config_id']} | "
                f"Top-k: {mensagem['top_k']} | "
                f"Modelo: {mensagem['modelo_gerador']}"
            )

        if mensagem["tipo"] == "assistant" and mensagem.get("fontes"):
            with st.expander("Ver fontes recuperadas"):
                for indice_fonte, fonte in enumerate(mensagem["fontes"], start=1):
                    st.markdown(f"**Fonte {indice_fonte}: {fonte['titulo']}**")
                    st.markdown(f"Categoria: `{fonte['categoria']}`")
                    st.markdown(f"Documento: `{fonte['doc_id']}`")
                    st.markdown(f"Chunk: `{fonte['chunk_id']}`")
                    st.markdown(f"Configuração: `{fonte.get('config_id', '')}`")
                    st.markdown(f"Chunk size: `{fonte.get('chunk_size', '')}`")
                    st.markdown(f"Chunk overlap: `{fonte.get('chunk_overlap', '')}`")
                    st.markdown(f"URL: {fonte['url']}")

                    distancia = fonte.get("distancia")
                    origem_busca = fonte.get("origem_busca")
                    score_palavra_chave = fonte.get("score_palavra_chave")

                    if distancia is not None:
                        st.markdown(f"Distância vetorial: `{round(float(distancia), 4)}`")

                    if origem_busca:
                        st.markdown(f"Origem da recuperação: `{origem_busca}`")

                    if score_palavra_chave is not None:
                        st.markdown(f"Score palavra-chave: `{score_palavra_chave}`")

                    st.text_area(
                        label=f"Trecho recuperado {indice_fonte}",
                        value=fonte["texto"],
                        height=180,
                        key=f"{indice_mensagem}_{fonte['chunk_id']}_{indice_fonte}"
                    )


pergunta = st.chat_input("Digite sua dúvida acadêmica...")


if pergunta:
    st.session_state.mensagens.append({
        "tipo": "user",
        "conteudo": pergunta
    })

    if modelo_gerador == "llama3.1:8b":
        mensagem_spinner = "Buscando informações na base documental e gerando resposta com Llama local..."
    elif modelo_gerador == "gemini-3.6-flash":
        mensagem_spinner = "Buscando informações na base documental e gerando resposta com Gemini..."
    else:
        mensagem_spinner = "Buscando informações na base documental e gerando resposta..."

    with st.spinner(mensagem_spinner):
        resultado = responder_pergunta(
            pergunta=pergunta,
            top_k=top_k,
            config_id=config_id,
            modelo_gerador=modelo_gerador
        )

    st.session_state.mensagens.append({
        "tipo": "assistant",
        "conteudo": resultado["resposta"],
        "fontes": resultado["fontes"],
        "tempo_resposta_ms": resultado["tempo_resposta_ms"],
        "config_id": resultado["config_id"],
        "top_k": resultado["top_k"],
        "modelo_gerador": resultado["modelo_gerador"]
    })

    st.rerun()