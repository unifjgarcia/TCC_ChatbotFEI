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


pergunta = st.chat_input("Digite sua dúvida acadêmica...")


if pergunta:
    resultado = buscar_resposta(pergunta)

    with st.chat_message("user"):
        st.write(pergunta)

    with st.chat_message("assistant"):
        st.write(resultado["resposta"])