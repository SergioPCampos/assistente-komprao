import os
import streamlit as st
import pandas as pd
import google.generativeai as genai

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Registe os seus talões por texto de forma rápida, sem limites de imagens e totalmente funcional no plano gratuito.")

# Configuração da chave do Gemini a partir dos Secrets do Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Ficheiro local para guardar o histórico de preços
FICHEIRO_HISTORICO = "historico_precos.csv"

# --- Secção de Registo Manual ---
st.subheader("📝 Adicionar Novo Talão ou Produtos")

with st.form("form_registo", clear_on_submit=True):
    nome_talao = st.text_input("Identificação do Talão (ex: Compras Komprão 30/09)")
    detalhes_produtos = st.text_area(
        "Cole ou escreva os itens do talão:",
        placeholder="Ex:\n- Arroz 5kg: R$ 25,90\n- Leite 1L: R$ 5,49\n- Chocolate: R$ 7,50"
    )
    
    submitted = st.form_submit_button("Guardar no Histórico")
    
    if submitted:
        if nome_talao and detalhes_produtos:
            novo_registo = pd.DataFrame({
                "Data": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                "Detalhes": [f"[{nome_talao}] \n{detalhes_produtos}"]
            })
            
            if os.path.exists(FICHEIRO_HISTORICO):
                df_existente = pd.read_csv(FICHEIRO_HISTORICO)
                df_final = pd.concat([df_existente, novo_registo], ignore_index=True)
            else:
                df_final = novo_registo
                
            df_final.to_csv(FICHEIRO_HISTORICO, index=False)
            st.success("Registo guardado com sucesso!")
        else:
            st.warning("Por favor, preencha a identificação e os itens do talão.")

# --- Secção para visualizar histórico guardado ---
st.markdown("---")
st.subheader("📊 Histórico de Compras Guardado")

if os.path.exists(FICHEIRO_HISTORICO):
    df_historico = pd.read_csv(FICHEIRO_HISTORICO)
    st.dataframe(df_historico, use_container_width=True)
    
    if st.button("Limpar Histórico Completo"):
        os.remove(FICHEIRO_HISTORICO)
        st.rerun()
else:
    st.info("Ainda não existem registos guardados no histórico.")

# --- Secção de Chat Interativo com o Histórico ---
st.markdown("---")
st.subheader("💬 Conversar sobre o Histórico de Preços")

if os.path.exists(FICHEIRO_HISTORICO):
    df_chat = pd.read_csv(FICHEIRO_HISTORICO)
    
    pergunta_utilizador = st.text_input("Faça uma pergunta sobre os preços guardados (ex: Onde comprei o leite mais barato?):")
    
    if pergunta_utilizador:
        with st.spinner("A consultar o histórico..."):
            prompt_chat = (
                f"Com base no seguinte histórico de preços em CSV:\n{df_chat.to_string()}\n\n"
                f"Responde à seguinte pergunta do utilizador de forma clara e objetiva: {pergunta_utilizador}"
            )
            
            try:
                # O chat consome apenas texto, gastando uma cota residual e sem bloqueios
                modelo_chat = genai.GenerativeModel('gemini-3.8-flash')
                resposta_chat = modelo_chat.generate_content(prompt_chat)
                st.markdown("**Resposta do Assistente:**")
                st.write(resposta_chat.text)
            except Exception as e:
                erro_str = str(e)
                if "perDay" in erro_str or ("quota" in erro_str.lower() and "day" in erro_str.lower()):
                    st.error("🚨 **Cota Diária Esgotada!** O limite diário de pedidos foi atingido.")
                elif "429" in erro_str or "quota" in erro_str.lower():
                    st.warning("⚠️ Limite atingido. Aguarde um momento e tente novamente.")
                else:
                    st.error(f"⚠️ Erro: {erro_str}")
else:
    st.info("Registe pelo menos um talão para poder conversar sobre o histórico.")
