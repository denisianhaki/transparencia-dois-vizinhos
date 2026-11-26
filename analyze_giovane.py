import pandas as pd

df = pd.read_csv('data/processed/diarias_consolidada.csv', encoding='utf-8-sig', sep=';', decimal=',', dtype=str)
giovane = df[df.apply(lambda r: 'GIOVANE' in str(r.values).upper(), axis=1)].copy()

giovane['ValorEmpenho'] = pd.to_numeric(giovane['ValorEmpenho'].str.replace(',','.'), errors='coerce')
giovane['NumeroDiarias'] = pd.to_numeric(giovane['NumeroDiarias'], errors='coerce')

print("=== RESUMO GERAL ===")
print("Total empenhos:", len(giovane))
print("Total valor: R$", round(giovane['ValorEmpenho'].sum(), 2))
print("Total diarias:", giovane['NumeroDiarias'].sum())
print("Empenho apos viagem:", giovane['EmpenhoAposViagem'].eq('True').sum(), "de", len(giovane))
print("Inclui fim de semana:", giovane['IncluiFimDeSemana'].eq('True').sum(), "de", len(giovane))

print()
print("=== POR MES ===")
por_mes = giovane.groupby('MesEmpenho')['ValorEmpenho'].agg(['sum','count'])
por_mes.columns = ['Valor','Empenhos']
print(por_mes.to_string())

print()
print("=== DESTINOS ===")
print(giovane['Destino'].value_counts().to_string())

print()
print("=== TIPO OBJETIVO ===")
print(giovane['TipoObjetivo'].value_counts().to_string())

print()
print("=== PORTARIAS USADAS ===")
print(giovane['LeiConcessao'].value_counts().to_string())

print()
print("=== EMPENHOS APOS VIAGEM ===")
apos = giovane[giovane['EmpenhoAposViagem']=='True']
print(apos[['DataEmpenho','DataInicialViagem','DataFinalViagem','ValorEmpenho','Destino']].to_string())

print()
print("=== VIAGENS FIM DE SEMANA ===")
fds = giovane[giovane['IncluiFimDeSemana']=='True']
print(fds[['DataEmpenho','DataInicialViagem','DataFinalViagem','ValorEmpenho','Destino','Objetivo']].to_string())

print()
print("=== OBJETIVOS DECLARADOS ===")
for i, row in giovane.iterrows():
    obj = str(row.get('Objetivo',''))
    if obj and obj != 'nan' and len(obj) > 5:
        print(f"  Empenho {row['Empenho']} | {row['DataInicialViagem']} | R${row['ValorEmpenho']} | Destino: {row['Destino']}")
        print(f"  OBJETIVO: {obj[:300]}")
        print()
