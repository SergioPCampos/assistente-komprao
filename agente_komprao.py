import os
import streamlit as st
import pandas as pd
import google.generativeai as genai
from PIL import Image

# Configuração da página
st.set_page_config(page_title="Assistente de Preços - Komprão", page_icon="🛒", layout="centered")

st.title("🛒 Assistente de Preços - Komprão")
st.write("Envie uma ou mais fotos de talões ou etiquetas de preço para registar e monitorizar os valores.")

# Configuração da chave do Gemini a partir dos Secrets do Streamlit
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# Ficheiro local para guardar o histórico de preços
FICHEIRO_HISTORICO = "historico_precos.csv"

# Carregar imagens do utilizador (permite múltiplos ficheiros)
fotos_upload = st.file_uploader(
    "Carregar fotos dos talões ou produtos", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if fotos_upload:
    st.info(f"Foram carregados {len(fotos_upload)} ficheiro(s). Clique abaixo para iniciar a análise individual.")
    
    if st.button("Analisar e Registar Todos os Talões"):
        barrinha_progresso = st.progress(0)
        total_fotos = len(fotos_upload)
        
        for index, foto_upload in enumerate(fotos_upload):
            imagem = Image.open(foto_upload)
            st.image(imagem, caption=f"A analisar: {foto_upload.name}", use_container_width=True)
            
            with st.spinner(f"A processar o talão {index + 1} de {total_fotos} ({foto_upload.name})..."):
                prompt = (
                    "Analisa esta imagem de um talão de compras ou etiqueta de preço do supermercado Komprão. "
                    "Extrai os dados de forma limpa e estruturada, indicando o nome do produto, a quantidade e o preço unitário ou total. "
                    "Retorna a resposta numa lista clara."
                )
                
                try:
                    # Utilização do modelo compatível
                    modelo = genai.GenerativeModel('gemini-3.8-flash')
                    resposta = modelo.generate_content([imagem, prompt])
                    
                    st.success(f"Análise de '{foto_upload.name}' concluída com sucesso!")
                    st.write(resposta.text)
                    
                    # Guardar o resultado individual no histórico CSV
                    novo_registo = pd.DataFrame({
                        "Data": [pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")],
                        "Detalhes": [f"[{foto_upload.name}] \n{resposta.text}"]
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
                            f"⚠️ **Limite de pedidos atingido (Plano Gratuito)**\n\n"
                            f"Atingiu o limite de 5 pedidos por minuto ao processar '{foto_upload.name}'. "
                            "⏳ *Aguarde alguns segundos antes de enviar mais talões.*"
                        )
                        break # Interrompe o ciclo para evitar bloquear mais
                    else:
                        st.error(f"⚠️ Erro ao processar '{foto_upload.name}': {erro_str}")
            
            # Atualizar barra de progresso
            barrinha_progresso.progress((index + 1) / total_fotos)
            
        st.success("🎉 Processamento de todos os talões concluído!")

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
