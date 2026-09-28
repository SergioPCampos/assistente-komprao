import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Envie a foto do seu talão ou etiqueta de preço para registar e monitorizar os valores.")

# Configuração da chave do Gemini a partir dos Secrets do Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Ficheiro local para guardar o histórico de preços
FICHEIRO_HISTORICO = "historico_precos.csv"

# Carregar imagem do utilizador
foto_upload = st.file_uploader("Carregar foto do talão ou produto", type=["jpg", "jpeg", "png"])

if foto_upload is not None:
    imagem = Image.open(foto_upload)
    st.image(imagem, caption="Foto enviada", use_container_width=True)
    
    if st.button("Analisar e Registar Preços"):
        with st.spinner("A analisar a imagem com inteligência artificial..."):
            prompt = (
                "Analisa esta imagem de um talão de compras ou etiqueta de preço do supermercado Komprão. "
                "Extrai os dados de forma limpa e estruturada, indicando o nome do produto, a quantidade e o preço unitário ou total. "
                "Retorna a resposta numa lista clara."
            )
            
            try:
                # Utilização do modelo multimodal estável com a biblioteca clássica
                modelo = genai.GenerativeModel('gemini-1.5-flash')
                resposta = modelo.generate_content([imagem, prompt])
                
                st.success("Análise concluída!")
                st.write(resposta.text)
                
                # Guardar o resultado no histórico CSV
                novo_registo = pd.DataFrame({
                    "Data": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                    "Detalhes": [resposta.text]
                })
                
                if os.path.exists(FICHEIRO_HISTORICO):
                    df_existente = pd.read_csv(FICHEIRO_HISTORICO)
                    df_final = pd.concat([df_existente, novo_registo], ignore_index=True)
                else:
                    df_final = novo_registo
                    
                df_final.to_csv(FICHEIRO_HISTORICO, index=False)
                
            except Exception as e:
                st.error(f"Ocorreu um erro ao comunicar com a inteligência artificial: {e}")

# Secção para visualizar histórico guardado
st.markdown("---")
st.subheader("📊 Histórico de Compras Guardado")

if os.path.exists(FICHEIRO_HISTORICO):
    df_historico = pd.read_csv(FICHEIRO_HISTORICO)
    st.dataframe(df_historico)
    
    if st.button("Limpar Histórico"):
        os.remove(FICHEIRO_HISTORICO)
        st.rerun()
else:
    st.info("Ainda não existem registos guardados no histórico.")