import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Envie os seus talões. Para respeitar o plano gratuito da API, cada talão pode ser analisado individualmente com um clique, evitando bloqueios.")

# Configuração da chave do Gemini a partir dos Secrets do Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Ficheiro local para guardar o histórico de preços
FICHEIRO_HISTORICO = "historico_precos.csv"

# Carregar imagens do utilizador (múltiplos ficheiros permitidos)
fotos_upload = st.file_uploader(
    "Carregar fotos dos talões ou produtos", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if fotos_upload:
    st.markdown("---")
    st.subheader("📋 Ficheiros Carregados Prontos para Análise")
    st.info("Clique no botão abaixo de cada talão para fazer a leitura com calma, um de cada vez.")
    
    # Percorrer cada foto carregada e dar-lhe um espaço próprio com botão individual
    for index, foto_file in enumerate(fotos_upload):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            imagem = Image.open(foto_file)
            st.image(imagem, caption=foto_file.name, use_container_width=True)
            
        with col2:
            st.markdown(f"**Ficheiro:** `{foto_file.name}`")
            
            # Botão individual para cada talão
            if st.button(f"🔍 Analisar Talão {index + 1}", key=f"btn_{index}"):
                with st.spinner(f"A analisar '{foto_file.name}'..."):
                    prompt = (
                        "Analisa esta imagem de um talão de compras ou etiqueta de preço do supermercado Komprão. "
                        "Extrai os dados de forma limpa e estruturada, indicando o nome do produto, a quantidade e o preço unitário ou total. "
                        "Retorna a resposta numa lista clara."
                    )
                    
                    try:
                        modelo = genai.GenerativeModel('gemini-3.8-flash')
                        resposta = modelo.generate_content([imagem, prompt])
                        
                        st.success("Análise concluída com sucesso!")
                        st.markdown(resposta.text)
                        
                        # Guardar o resultado individual no histórico CSV
                        novo_registo = pd.DataFrame({
                            "Data": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                            "Detalhes": [f"[{foto_file.name}] \n{resposta.text}"]
                        })
                        
                        if os.path.exists(FICHEIRO_HISTORICO):
                            df_existente = pd.read_csv(FICHEIRO_HISTORICO)
                            df_final = pd.concat([df_existente, novo_registo], ignore_index=True)
                        else:
                            df_final = novo_registo
                            
                        df_final.to_csv(FICHEIRO_HISTORICO, index=False)
                        
                    except Exception as e:
                        erro_str = str(e)
                        if "429" in erro_str or "quota" in erro_str.lower() or "ResourceExhausted" in erro_str:
                            st.warning(
                                "⚠️ **Limite de pedidos atingido (Plano Gratuito)**\n\n"
                                "Atingiu o limite momentâneo da API. Aguarde 30 segundos e clique novamente no botão deste talão."
                            )
                        else:
                            st.error(f"⚠️ Erro ao processar: {erro_str}")
        
        st.markdown("---")

# Secção para visualizar histórico guardado
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
    
    pergunta_utilizador = st.text_input("Faça uma pergunta sobre os preços guardados:")
    
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
                if "429" in erro_str or "quota" in erro_str.lower() or "ResourceExhausted" in erro_str:
                    st.warning("⚠️ Limite atingido. Aguarde alguns segundos e tente novamente.")
                else:
                    st.error(f"⚠️ Erro: {erro_str}")
else:
    st.info("Registe pelo menos um talão para poder conversar sobre o histórico.")
