import streamlit as st

from services.buscador_mock import buscar_resposta


st.set_page_config(
    page_title="Assistente Acadêmico FEI",
    page_icon="🎓",
    layout="centered"
)


st.title("🎓 Assistente Acadêmico FEI")
st.write("Tire suas dúvidas acadêmicas e administrativas de forma simples.")

st.divider()


# Cria uma lista para armazenar as mensagens da conversa
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []


# Mostra todas as mensagens anteriores na tela
for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["tipo"]):
        st.write(mensagem["conteudo"])


# Campo de entrada do chat
pergunta = st.chat_input("Digite sua dúvida acadêmica...")


if pergunta:
    # Salva a pergunta do usuário no histórico
    st.session_state.mensagens.append({
        "tipo": "user",
        "conteudo": pergunta
    })

    # Busca a resposta na base simulada
    resultado = buscar_resposta(pergunta)
    resposta = resultado["resposta"]

    # Salva a resposta do assistente no histórico
    st.session_state.mensagens.append({
        "tipo": "assistant",
        "conteudo": resposta
    })

    # Atualiza a tela para mostrar a nova conversa
    st.rerun()