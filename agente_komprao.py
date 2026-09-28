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
                # Utilização do modelo correto compatível com a sua credencial
                modelo = genai.GenerativeModel('gemini-3.8-flash')
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
                erro_str = str(e)
                if "429" in erro_str or "quota" in erro_str.lower():
                    st.warning(
                        "⚠️ **Limite de pedidos atingido temporariamente (Plano Gratuito)**\n\n"
                        "Fez vários pedidos num curto espaço de tempo e atingiu o limite de **5 pedidos por minuto** da API gratuita.\n\n"
                        "⏳ *Por favor, aguarde cerca de 10 a 30 segundos e clique novamente para continuar.*"
                    )
                else:
                    st.error(f"⚠️ **Ocorreu um erro na execução:**\n\n{erro_str}")

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

# --- Secção de Chat Interativo com o Histórico ---
st.markdown("---")
st.subheader("💬 Conversar sobre o Histórico de Preços")

if os.path.exists(FICHEIRO_HISTORICO):
    df_chat = pd.read_csv(FICHEIRO_HISTORICO)
    
    pergunta_utilizador = st.text_input("Faça uma pergunta sobre os preços guardados (ex: Qual a diferença de preço de um produto no histórico?):")
    
    if pergunta_utilizador:
        with st.spinner("A consultar o histórico..."):
            prompt_chat = (
                f"Com base no seguinte histórico de preços em CSV:\n{df_chat.to_string()}\n\n"
                f"Responde à seguinte pergunta do utilizador de forma clara e objetiva: {pergunta_utilizador}"
            )
            
            try:
                modelo_chat = genai.GenerativeModel('gemini-3.8-flash')
                resposta_chat = modelo_chat.generate_content(prompt_chat)
                st.markdown("**Resposta do Assistente:**")
                st.write(resposta_chat.text)
            except Exception as e:
                erro_str = str(e)
                if "429" in erro_str or "quota" in erro_str.lower():
                    st.warning(
                        "⚠️ **Limite de pedidos atingido temporariamente (Plano Gratuito)**\n\n"
                        "Atingiu o limite de **5 pedidos por minuto**. Por favor, aguarde alguns segundos e tente novamente."
                    )
                else:
                    st.error(f"⚠️ Erro ao processar a pergunta: {erro_str}")
else:
    st.info("Registe pelo menos um talão para poder conversar sobre o histórico.")
