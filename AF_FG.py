### Carga de librerias ###
import pandas as pd


### Definicion de funciones ###
def Load_data(file_name):
    """
    Carga información desde un archivo Excel. 
    Se generan 2 dataframes:
        Uno que incorpora el número de períodos mayores, usualmente años (df_num).
        Otro en el cual se almacenan los datos mismos (df_data).
    """
    
    # Getting info from excel to a dataframe
    print ("Importing from: "+str(file_name)+" into Data as DataFrame")

    df_num=pd.read_excel(file_name, sheet_name ="Data", header=0, nrows=1, index_col="ID", na_values=["-9999"])
    df_data=pd.read_excel(file_name, sheet_name ="Data", header=3, index_col="ID", na_values=["-9999"])

    return df_num, df_data

def Add_Obs_data_probs(df, df_yr):
    """
    Agrega las probabildiades de los datos en escala temporal del período mayor.
    Considera como representativo el punto medio del intervalo para asignar la
    probabilidad. La transformación a período mayor coniste en considerar que
    N_p (períodos o observaciones independientes) se obtuvieron en N_a ("años") y,
    por lo tanto, se calcula la probabilidad de superar en el "año" un valor dado
    como la probabilidad conjunta de los periodos menores.
    """
    # df: columna de datos observados.
    # df_yr: numero de años/periodos representados por la estacion.

    df = df.dropna() #se remueven datos nulos.
    N_p = df.count()  # Número total de observaciones (no nulas).
    N_a = df_yr.iloc[0]  # Número de años (o períodos mayores). Puede ser igual a N_p, pero a veces son distintos por datos faltantes.

    # Se calcula la probabilidad de no excendencia para cada dato:
    # Crea un nuevo DataFrame con:
    # - Los datos originales
    # - Probabilidad de no excedencia P calculada con fórmula de Gringorten (o similar)
    df = pd.DataFrame({
        "Datos": df,
        "P": ((df.rank(method="first", ascending=True) * 2 - 1) / (2 * N_p)) ** (N_p / N_a)
    })
    """
    Al calcular P, se le asigna distintas pbb a los valores 0, solo porque al ordenarlos algunos quedarán en posiciones superiores
    a otros, pero esto es solo un tema de ordenar.
    Te queda como tarea: averigua que tratamiento se debe hacer con los valores 0 antes de este paso.
    """

    # Prepara la salida como diccionario
    dict_out = {}
    dict_out["Obs_data"] = df
    dict_out["Observaciones"] = N_p
    dict_out["Years"] = N_a
    return dict_out

def Fit_distribs(dict_obs_data):
    """
    
    """
    df_Obs=dict_obs_data["Obs_data"]
    N_p=dict_obs_data["Observaciones"]
    N_a=dict_obs_data["Years"] 

    T_Table=np.array(T)     #Periodos de retorno a evaluar en un np.array
    P_Table=1.0 - 1.0/T_Table

# PARAMETROS DEL ANÁLISIS DE FRECUENCIA
# Periodos de retorno a evaluar:
T=[2,5,10,20,25,50,100,200,500,1000,10000]

### Definir nombres de archivos ###
file_name = 'Data.xlsx'                 #Planilla con data a analizar
Res_file_name = 'AF Results.xlsx'    #Planilla de resultados

### Cargar data en DataFrame ###
Data_yr, Data = Load_data(file_name)

### Probando Add_Obs_data_probs:
for station in Data.columns.values:
    
    print ("\nWorking on: "+station)
    WB_name=station+" "+Res_file_name

    # Se ocupa Add_Obs_data_probs para calcular la pbb de no excedencia de cada valor por Gringorten.
    dict_obs_data = Add_Obs_data_probs(Data[station],Data_yr[station])

    # Exporting obs data and their probabilities
    print("        Exporting Pexc data...", end="")
    with pd.ExcelWriter(WB_name, engine='openpyxl', mode='w') as writer:
        dict_obs_data["Obs_data"].to_excel(writer, sheet_name="Info", startrow=2)
    print("done")

