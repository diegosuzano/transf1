import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta
import os

# Configurações
EXCEL_PATH = "Controle Transferencia.xlsx"
SHEET_NAME = "Basae"
FUSO_HORARIO = timezone(timedelta(hours=-3))  # UTC-3

campos_tempo = [
    "Entrada na Fábrica", "Encostou na doca Fábrica", "Início carregamento",
    "Fim carregamento", "Faturado", "Amarração carga", "Saída do pátio",
    "Entrada CD", "Encostou na doca CD", "Início Descarregamento CD",
    "Fim Descarregamento CD", "Saída CD"
]

# Inicializa session_state para os campos de tempo
for campo in campos_tempo:
    if campo not in st.session_state:
        st.session_state[campo] = ""

st.set_page_config(page_title="Registro Transferência", layout="centered")
st.title("🚚 Registro de Transferência de Carga")

pagina = st.selectbox("📌 Escolha uma opção", ["Tela Inicial", "Lançar Novo Controle", "Editar Lançamentos Incompletos", "Em Operação"])

if pagina == "Tela Inicial":
    st.subheader("Bem-vindo ao Sistema de Controle de Transferência")
    st.write("Use o menu acima para navegar entre as opções disponíveis:")
    st.write("- **Lançar Novo Controle**: Para registrar um novo controle de transferência")
    st.write("- **Editar Lançamentos Incompletos**: Para editar registros que ainda não foram finalizados")
    st.write("- **Em Operação**: Para visualizar os registros que estão em processo")
    
    # Opção de download da planilha mantida na tela inicial
    if os.path.exists(EXCEL_PATH):
        with open(EXCEL_PATH, "rb") as f:
            st.download_button(
                label="📥 Baixar Planilha Atual",
                data=f,
                file_name=EXCEL_PATH,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("Nenhuma planilha encontrada ainda. Crie o primeiro registro para gerar a planilha.")

elif pagina == "Lançar Novo Controle":
    st.subheader("Dados do Veículo")
    data = st.date_input("Data", value=datetime.now(FUSO_HORARIO).date())
    placa = st.text_input("Placa do caminhão")
    conferente = st.text_input("Nome do conferente")

    st.subheader("Fábrica")
    for campo in campos_tempo[:7]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(campo, value=st.session_state[campo], disabled=True, key=f"txt_{campo}")
        with col2:
            if st.button(f"Registrar {campo}", key=f"btn_{campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                # NÃO CHAMAR st.experimental_rerun() aqui!

    st.subheader("Centro de Distribuição (CD)")
    for campo in campos_tempo[7:]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input(campo, value=st.session_state[campo], disabled=True, key=f"txt_{campo}")
        with col2:
            if st.button(f"Registrar {campo}", key=f"btn_{campo}"):
                st.session_state[campo] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                # NÃO CHAMAR st.experimental_rerun() aqui!

    if st.button("✅ Salvar Registro"):
        nova_linha = {
            "Data": data.strftime("%Y-%m-%d"),
            "Placa do caminhão": placa,
            "Nome do conferente": conferente,
            **{campo: st.session_state[campo] for campo in campos_tempo},
        }
        try:
            if os.path.exists(EXCEL_PATH):
                df_existente = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
                df_novo = pd.concat([df_existente, pd.DataFrame([nova_linha])], ignore_index=True)
            else:
                df_novo = pd.DataFrame([nova_linha])

            with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                df_novo.to_excel(writer, sheet_name=SHEET_NAME, index=False)

            st.success("✅ Registro salvo com sucesso!")

            # Limpa campos depois de salvar
            for campo in campos_tempo:
                st.session_state[campo] = ""

        except Exception as e:
            st.error("Erro ao salvar planilha localmente:")
            st.text(str(e))

elif pagina == "Editar Lançamentos Incompletos":
    st.subheader("✏️ Edição de Registros Incompletos")

    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtrar apenas registros onde 'Saída CD' está vazia
        incompletos = df[(pd.isna(df['Saída CD'])) | (df['Saída CD'] == "")]

        if not incompletos.empty:
            # Criar opções do selectbox mostrando a placa
            opcoes = []
            for idx in incompletos.index:
                placa = incompletos.loc[idx, 'Placa do caminhão']
                data = incompletos.loc[idx, 'Data']
                opcoes.append(f"Índice {idx} - Placa: {placa} - Data: {data}")
            
            opcao_selecionada = st.selectbox("Selecione um registro para editar:", opcoes)
            idx = int(opcao_selecionada.split(" - ")[0].replace("Índice ", ""))
            
            registro = incompletos.loc[idx]
            
            st.write(f"**Editando registro da placa: {registro['Placa do caminhão']}**")
            
            # Inicializa session_state para os campos editáveis se ainda não existirem
            for coluna in df.columns:
                if f"edit_{coluna}" not in st.session_state:
                    st.session_state[f"edit_{coluna}"] = str(registro[coluna]) if not pd.isna(registro[coluna]) else ""

            for coluna in df.columns:
                valor = registro[coluna]
                if pd.isna(valor) or valor == "":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        # Usar o valor do session_state para o text_input
                        st.text_input(f"{coluna}", value=st.session_state[f"edit_{coluna}"], key=f"edit_{coluna}")
                    with col2:
                        if coluna in campos_tempo:
                            # Callback para o botão 'Agora'
                            def update_time(col):
                                st.session_state[f"edit_{col}"] = datetime.now(FUSO_HORARIO).strftime("%Y-%m-%d %H:%M:%S")
                            st.button(f"⏰ Agora", key=f"btn_now_{coluna}", on_click=update_time, args=(coluna,))
                else:
                    st.text_input(f"{coluna}", value=str(valor), disabled=True, key=f"readonly_{coluna}")

            if st.button("💾 Salvar preenchimento"):
                for coluna in df.columns:
                    if pd.isna(registro[coluna]) or registro[coluna] == "": # Apenas atualiza campos que estavam vazios
                        novo_valor = st.session_state[f"edit_{coluna}"]
                        if novo_valor.strip() != "":
                            df.at[idx, coluna] = novo_valor

                with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl", mode="w") as writer:
                    df.to_excel(writer, sheet_name=SHEET_NAME, index=False)

                st.success("✅ Registro atualizado com sucesso!")
                # Limpa os campos editáveis do session_state para a próxima edição
                for coluna in df.columns:
                    if f"edit_{coluna}" in st.session_state:
                        del st.session_state[f"edit_{coluna}"]
                st.experimental_rerun()
        else:
            st.info("✅ Todos os registros estão completos!")
    else:
        st.error("❌ Planilha não encontrada.")

elif pagina == "Em Operação":
    st.subheader("🚛 Registros em Operação")
    
    if os.path.exists(EXCEL_PATH):
        df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME, engine="openpyxl")
        # Filtrar registros onde 'Saída CD' está vazia (em operação)
        em_operacao = df[(pd.isna(df['Saída CD'])) | (df['Saída CD'] == "")]
        
        if not em_operacao.empty:
            # Função para calcular diferença de tempo
            def calcular_tempo(inicio, fim):
                if pd.isna(inicio) or pd.isna(fim) or inicio == "" or fim == "":
                    return ""
                try:
                    inicio_dt = pd.to_datetime(inicio)
                    fim_dt = pd.to_datetime(fim)
                    diff = fim_dt - inicio_dt
                    horas = int(diff.total_seconds() // 3600)
                    minutos = int((diff.total_seconds() % 3600) // 60)
                    return f"{horas:02d}:{minutos:02d}"
                except:
                    return ""
            
            # Função para encontrar o último campo preenchido (status)
            def obter_status(registro):
                for campo in reversed(campos_tempo):
                    if not pd.isna(registro[campo]) and registro[campo] != "":
                        return campo
                return "Não iniciado"
            
            # Preparar dados para exibição
            dados_operacao = []
            for idx in em_operacao.index:
                registro = em_operacao.loc[idx]
                
                # Calcular tempos
                tempo_carregamento = calcular_tempo(registro.get('Início carregamento'), registro.get('Fim carregamento'))
                tempo_total_fabrica = calcular_tempo(registro.get('Entrada na Fábrica'), registro.get('Saída do pátio'))
                tempo_percurso_cd = calcular_tempo(registro.get('Saída do pátio'), registro.get('Entrada CD'))
                tempo_descarregamento_cd = calcular_tempo(registro.get('Início Descarregamento CD'), registro.get('Fim Descarregamento CD'))
                tempo_total_cd = calcular_tempo(registro.get('Entrada CD'), registro.get('Saída CD'))
                
                dados_operacao.append({
                    'Placa': registro.get('Placa do caminhão', ''),
                    'Status': obter_status(registro),
                    'Tempo Carregamento': tempo_carregamento,
                    'Tempo Total Fábrica': tempo_total_fabrica,
                    'Tempo Percurso Para CD': tempo_percurso_cd,
                    'Tempo Descarregamento CD': tempo_descarregamento_cd,
                    'Tempo Total CD': tempo_total_cd
                })
            
            # Exibir tabela
            df_operacao = pd.DataFrame(dados_operacao)
            st.dataframe(df_operacao, use_container_width=True)
            
        else:
            st.info("📋 Nenhum registro em operação no momento.")
    else:
        st.error("❌ Planilha não encontrada.")
