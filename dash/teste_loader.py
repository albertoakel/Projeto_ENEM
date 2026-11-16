from dash_utils.data_loader import carregar_dados

# Carrega os dados da referência ESC
dados = carregar_dados("PA", referencia="ESC")

df_painel = dados["painel"]
df_faixa = dados["faixa"]

print("PAINEL:")
print(df_painel.columns.tolist())

print("\nFAIXA:")
print(df_faixa.columns.tolist())

print("\nAMOSTRA FAIXA:")
print(df_faixa.head())