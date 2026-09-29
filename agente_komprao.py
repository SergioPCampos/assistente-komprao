import os
import time
import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Envie os seus talões para análise individual e registo automático no histórico.")

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
    
    # Percorrer cada foto carregada (sem mostrar a imagem no ecrã)
    for index, foto_file in enumerate(fotos_upload):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"📄 **Ficheiro:** `{foto_file.name}`")
            
        with col2:
            # Botão individual para cada talão
            analisar_clicado = st.button(f"🔍 Analisar", key=f"btn_{index}")
            
        if analisar_clicado:
            imagem = Image.open(foto_file)
            prompt = (
                "Analisa esta imagem de um talão de compras ou etiqueta de preço do supermercado Komprão. "
                "Extrai os dados de forma limpa e estruturada, indicando o nome do produto, a quantidade e o preço unitário ou total. "
                "Retorna a resposta numa lista clara."
            )
            
            sucesso = False
            tentativa = 0
            max_tentativas = 2
            
            while not sucesso and tentativa < max_tentativas:
                try:
                    with st.spinner(f"A analisar '{foto_file.name}' com gemini-3.8-flash..."):
                        # Modelo correto exigido pela API atual
                        modelo = genai.GenerativeModel('gemini-3.8-flash')
                        resposta = modelo.generate_content([imagem, prompt])
                        
                        st.success(f"Análise de '{foto_file.name}' concluída com sucesso!")
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
                        sucesso = True
                        
                except Exception as e:
                    erro_str = str(e)
                    # Deteção se a cota diária ou limite total esgotou
                    if "perDay" in erro_str or ("quota" in erro_str.lower() and "day" in erro_str.lower()):
                        st.error(
                            "🚨 **Cota Diária Esgotada!**\n\n"
                            "A cota gratuita de requisições diárias para este modelo esgotou-se. "
                            "O serviço voltará a ficar disponível apenas amanhã."
                        )
                        break
                    elif "429" in erro_str or "quota" in erro_str.lower() or "ResourceExhausted" in erro_str:
                        tentativa += 1
                        if tentativa < max_tentativas:
                            aviso_placeholder = st.empty()
                            for segundos in range(15, 0, -1):
                                aviso_placeholder.warning(
                                    f"⚠️ **Limite de requisições atingido**\n\n"
                                    f"A aguardar limpeza da janela da API: **{segundos} segundos**..."
                                )
                                time.sleep(1)
                            aviso_placeholder.empty()
                        else:
                            st.error("⚠️ O limite foi atingido repetidamente. É provável que a cota diária tenha chegado ao fim.")
                    else:
                        st.error(f"⚠️ Erro ao processar: {erro_str}")
                        break
        
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
                if "perDay" in erro_str or ("quota" in erro_str.lower() and "day" in erro_str.lower()):
                    st.error("🚨 **Cota Diária Esgotada!** O limite diário de pedidos foi atingido.")
                elif "429" in erro_str or "quota" in erro_str.lower():
                    st.warning("⚠️ Limite atingido. Aguarde um momento e tente novamente.")
                else:
                    st.error(f"⚠️ Erro: {erro_str}")
else:
    st.info("Registe pelo menos um talão para poder conversar sobre o histórico.")
