import pandas as pd

def load_data(c,v):
    compras = pd.read_excel(c)
    vendas = pd.read_excel(v)
    return compras, vendas

def preprocess(compras, vendas):
    df = vendas.merge(compras, on="Item", how="left")
    df["Lucro"] = df["Valor_Venda"] - df["Valor_Custo"]
    df["Margem_%"] = df["Lucro"] / df["Valor_Venda"]
    return df
