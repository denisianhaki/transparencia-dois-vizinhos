import pandas as pd

df = pd.read_csv('data/processed/diarias_consolidada.csv', encoding='utf-8-sig', sep=';', decimal=',', dtype=str)

giovane = df[df.apply(lambda r: 'GIOVANE' in str(r.values).upper(), axis=1)].copy()
prefeito = df[df.apply(lambda r: 'TURATTO' in str(r.values).upper() or 'LUIS CARLOS' in str(r.values).upper(), axis=1)].copy()

giovane['ValorEmpenho'] = pd.to_numeric(giovane['ValorEmpenho'].str.replace(',','.'), errors='coerce')
prefeito['ValorEmpenho'] = pd.to_numeric(prefeito['ValorEmpenho'].str.replace(',','.'), errors='coerce')

print("=== PREFEITO TURATTO - VIAGENS ===")
print(f"Total empenhos: {len(prefeito)}")
print(f"Total valor: R$ {prefeito['ValorEmpenho'].sum():,.2f}")
print()
print(prefeito[['DataEmpenho','DataInicialViagem','DataFinalViagem','ValorEmpenho','Destino','Objetivo']].to_string())

print()
print("=== CRUZAMENTO: MESMAS DATAS DE VIAGEM ===")
# Comparar DataInicialViagem de ambos
g_datas = set(giovane['DataInicialViagem'].dropna().unique())
p_datas = set(prefeito['DataInicialViagem'].dropna().unique())
coincidentes = g_datas.intersection(p_datas)
print(f"Datas de inicio de viagem em comum: {len(coincidentes)}")
print("Datas coincidentes:")
for d in sorted(coincidentes):
    g_rows = giovane[giovane['DataInicialViagem']==d][['ValorEmpenho','Destino','Objetivo']]
    p_rows = prefeito[prefeito['DataInicialViagem']==d][['ValorEmpenho','Destino','Objetivo']]
    print(f"\n  Data: {d}")
    print(f"  GIOVANE: R${g_rows['ValorEmpenho'].sum():.2f} | Destino: {g_rows['Destino'].values}")
    print(f"  PREFEITO: R${p_rows['ValorEmpenho'].sum():.2f} | Destino: {p_rows['Destino'].values}")
    if not g_rows['Objetivo'].isna().all():
        print(f"  Obj Giovane: {g_rows['Objetivo'].values}")
    if not p_rows['Objetivo'].isna().all():
        print(f"  Obj Prefeito: {p_rows['Objetivo'].values}")

print()
print("=== VALOR TOTAL DUPLO NAS VIAGENS COINCIDENTES ===")
total_g = 0
total_p = 0
for d in coincidentes:
    total_g += giovane[giovane['DataInicialViagem']==d]['ValorEmpenho'].sum()
    total_p += prefeito[prefeito['DataInicialViagem']==d]['ValorEmpenho'].sum()
print(f"Giovane nessas viagens: R$ {total_g:,.2f}")
print(f"Prefeito nessas viagens: R$ {total_p:,.2f}")
print(f"Total gasto em viagens duplicadas: R$ {total_g+total_p:,.2f}")
