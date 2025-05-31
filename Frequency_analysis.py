### Carga de librerias ###
import pandas as pd


### Definicion de funciones ###
def Load_data(file_name):
    """
    Carga información desde un archivo Excel. 
    Se generan 2 dataframes:
        Uno que incorpora el número de períodos mayores (usualmente años).
        Otro en el cual se almacenan los datos mismos.
    """
    
    # Getting info from excel to a dataframe
    print ("Importing from: "+str(file_name)+" into Data as DataFrame")

    df_num=pd.read_excel(file_name, sheet_name ="Data", header=0, nrows=1, index_col="ID", na_values=["-9999"])
    df_data=pd.read_excel(file_name, sheet_name ="Data", header=3, index_col="ID", na_values=["-9999"])

    return df_num, df_data

def Add_Obs_data_probs(df, df_yr):
    """
    
    """
    # df: columna de datos observados.
    # df_yr: numero de años/periodos representados por la estacion.

    df = df.dropna() #se remueven datos nulos.
    N_p = df.count()  # Número total de observaciones (no nulas).
    N_a = df_yr.iloc[0]  # Número de años (o períodos mayores). Puede ser igual a N_p, pero a veces son distintos por datos faltantes.

    # Se calcula la probabilidad de excendencia para cada dato:
    # Crea un nuevo DataFrame con:
    # - Los datos originales
    # - Probabilidad de excedencia P calculada con fórmula de Gringorten (o similar)
    df = pd.DataFrame({
        "Datos": df,
        "P": ((df.rank(method="first", ascending=True) * 2 - 1) / (2 * N_p)) ** (N_p / N_a)
    })

    # Prepara la salida como diccionario
    dict_out = {}
    dict_out["Obs_data"] = df
    dict_out["Observaciones"] = N_p
    dict_out["Years"] = N_a
    return dict_out


### Definir nombre del archivo con la data a procesar ###
file_name = 'Data.xlsx'

### Cargar data en DataFrame ###
Data_yr, Data = Load_data(file_name)

### Probando Add_Obs_data_probs (aca quedé 31 de mayo)

