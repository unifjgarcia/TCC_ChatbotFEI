import streamlit as st

st.set_page_config(
    page_title="Assistente Acadêmico FEI",
    page_icon="🎓",
    layout="centered"
)

st.title("🎓 Assistente Acadêmico FEI")
st.write("Protótipo demonstrativo para suporte a dúvidas acadêmicas e administrativas.")

pergunta = st.text_input("Digite sua dúvida:")

if st.button("Enviar pergunta"):
    if pergunta.strip() == "":
        st.warning("Digite uma pergunta antes de enviar.")
    else:
        st.success("Pergunta recebida com sucesso!")
        st.write("Sua pergunta foi:")
        st.info(pergunta)