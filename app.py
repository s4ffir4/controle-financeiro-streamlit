import streamlit as st
import psycopg2
import pandas as pd
import plotly.express as px
from datetime import date

st.set_page_config(
    page_title="Controle Financeiro",
    page_icon="💰",
    layout="wide"
)

def conectar():
    return psycopg2.connect(
        host=st.secrets["ep-withered-mode-aphvlwsr-pooler.c-7.us-east-1.aws.neon.tech"],
        database=st.secrets["neondb"],
        user=st.secrets["neondb_owner"],
        password=st.secrets["npg_Lw6hfs0Elt"],
        port=st.secrets["5432"],
        sslmode="require"
    )

def cadastrar_usuario(nome, email, senha):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha)
            VALUES (%s, %s, %s)
            """,
            (nome, email, senha)
        )
        conn.commit()
        st.success("Usuário cadastrado com sucesso!")

    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao cadastrar usuário: {e}")

    finally:
        cursor.close()
        conn.close()

def autenticar(email, senha):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, nome
        FROM usuarios
        WHERE email = %s AND senha = %s
        """,
        (email, senha)
    )

    usuario = cursor.fetchone()

    cursor.close()
    conn.close()

    return usuario

def registrar_movimentacao(usuario_id, tipo, categoria, descricao, valor, data_movimentacao):
    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO movimentacoes (
                usuario_id,
                tipo,
                categoria,
                descricao,
                valor,
                data_movimentacao
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                usuario_id,
                tipo,
                categoria,
                descricao,
                valor,
                data_movimentacao
            )
        )

        conn.commit()
        st.success("Movimentação registrada com sucesso!")

    except Exception as e:
        conn.rollback()
        st.error(f"Erro ao registrar movimentação: {e}")

    finally:
        cursor.close()
        conn.close()

def buscar_movimentacoes(usuario_id):
    conn = conectar()

    query = """
        SELECT
            id,
            tipo,
            categoria,
            descricao,
            valor,
            data_movimentacao
        FROM movimentacoes
        WHERE usuario_id = %s
        ORDER BY data_movimentacao DESC
    """

    df = pd.read_sql_query(query, conn, params=(usuario_id,))

    conn.close()

    return df

if "logado" not in st.session_state:
    st.session_state.logado = False

if "usuario_id" not in st.session_state:
    st.session_state.usuario_id = None

if "usuario_nome" not in st.session_state:
    st.session_state.usuario_nome = None

def tela_login():
    st.title("💰 Controle Financeiro Pessoal")
    st.subheader("Login")

    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar"):
        usuario = autenticar(email, senha)

        if usuario:
            st.session_state.logado = True
            st.session_state.usuario_id = usuario[0]
            st.session_state.usuario_nome = usuario[1]
            st.rerun()
        else:
            st.error("E-mail ou senha inválidos.")

def tela_cadastro():
    st.subheader("Criar conta")

    nome = st.text_input("Nome completo")
    email = st.text_input("E-mail de cadastro")
    senha = st.text_input("Senha de cadastro", type="password")

    if st.button("Cadastrar"):
        if nome and email and senha:
            cadastrar_usuario(nome, email, senha)
        else:
            st.warning("Preencha todos os campos.")

def tela_nova_movimentacao():
    st.subheader("Nova movimentação")

    tipo = st.selectbox("Tipo", ["entrada", "saida"])

    categoria = st.selectbox(
        "Categoria",
        [
            "Salário",
            "Alimentação",
            "Transporte",
            "Moradia",
            "Lazer",
            "Saúde",
            "Educação",
            "Outros"
        ]
    )

    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor", min_value=0.01, step=10.0)
    data_movimentacao = st.date_input("Data", value=date.today())

    if st.button("Salvar movimentação"):
        registrar_movimentacao(
            st.session_state.usuario_id,
            tipo,
            categoria,
            descricao,
            valor,
            data_movimentacao
        )

def tela_dashboard():
    st.subheader("Dashboard financeiro")

    df = buscar_movimentacoes(st.session_state.usuario_id)

    if df.empty:
        st.info("Nenhuma movimentação cadastrada.")
        return

    total_entradas = df[df["tipo"] == "entrada"]["valor"].sum()
    total_saidas = df[df["tipo"] == "saida"]["valor"].sum()
    saldo = total_entradas - total_saidas

    col1, col2, col3 = st.columns(3)

    col1.metric("Entradas", f"R$ {total_entradas:,.2f}")
    col2.metric("Saídas", f"R$ {total_saidas:,.2f}")
    col3.metric("Saldo", f"R$ {saldo:,.2f}")

    st.markdown("### Movimentações")
    st.dataframe(df, use_container_width=True)

    resumo_categoria = (
        df.groupby(["categoria", "tipo"])["valor"]
        .sum()
        .reset_index()
    )

    grafico_barra = px.bar(
        resumo_categoria,
        x="categoria",
        y="valor",
        color="tipo",
        barmode="group",
        title="Movimentações por categoria"
    )

    st.plotly_chart(grafico_barra, use_container_width=True)

    resumo_tipo = (
        df.groupby("tipo")["valor"]
        .sum()
        .reset_index()
    )

    grafico_pizza = px.pie(
        resumo_tipo,
        names="tipo",
        values="valor",
        title="Entradas x Saídas"
    )

    st.plotly_chart(grafico_pizza, use_container_width=True)

def app_principal():
    st.sidebar.title("Menu")
    st.sidebar.write(f"Usuário: {st.session_state.usuario_nome}")

    menu = st.sidebar.radio(
        "Navegação",
        ["Dashboard", "Nova movimentação"]
    )

    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.session_state.usuario_id = None
        st.session_state.usuario_nome = None
        st.rerun()

    if menu == "Dashboard":
        tela_dashboard()

    elif menu == "Nova movimentação":
        tela_nova_movimentacao()

if not st.session_state.logado:
    aba1, aba2 = st.tabs(["Login", "Criar conta"])

    with aba1:
        tela_login()

    with aba2:
        tela_cadastro()

else:
    app_principal()
