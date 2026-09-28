import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Envie a foto do seu talão ou etiqueta de preço para registar e monitorizar os valores.")

# Configuração da chave de API e ambiente Vertex AI / Google Cloud
if "GEMINI_API_KEY" in st.secrets:
    os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    # Configura para o SDK aceitar credenciais do Google Cloud se necessário
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
                # Vamos testar o modelo standard ajustado para o projeto
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
                # Se falhar pelo SDK normal, tentamos a chamada direta com a chave AQ
                try:
                    import google.generativeai as gai
                    gai.configure(api_key=st.secrets["GEMINI_API_KEY"])
                    model_alt = gai.GenerativeModel('gemini-1.5-flash')
                    res_alt = model_alt.generate_content([imagem, prompt])
                    
                    st.success("Análise concluída!")
                    st.write(res_alt.text)
                    
                    novo_registo = pd.DataFrame({
                        "Data": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                        "Detalhes": [res_alt.text]
                    })
                    if os.path.exists(FICHEIRO_HISTORICO):
                        df_existente = pd.read_csv(FICHEIRO_HISTORICO)
                        df_final = pd.concat([df_existente, novo_registo], ignore_index=True)
                    else:
                        df_final = novo_registo
                    df_final.to_csv(FICHEIRO_HISTORICO, index=False)
                except Exception as err:
                    st.error(f"Erro detalhado na execução: {err}")

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
    
  
