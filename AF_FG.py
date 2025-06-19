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
    Importante: 
        - Este codigo desecha los valores nulos (o #N/A), pero sigue considerando los valores 0. De hecho
        a cada valor 0 se le asigna un valor de P por Gringorten
        - Cuando tiene valores nulos, el termino N_p/N_a es distinto de 1.
        - Hasta el momento, este codigo no descarta los valores cero antes de hacer cualquier analisis.
    """

    # Prepara la salida como diccionario
    dict_out = {}
    dict_out["Obs_data"] = df
    dict_out["Observaciones"] = N_p
    dict_out["Years"] = N_a
    return dict_out

def probs(exp):
    """
    genera vectores de probabilidades y períodos de retorno "equiespaciados"
    hasta cierto orden de magnitud "exp".
    Los espaciamientos se controlan en el vector "dec"
    
    """
    import numpy as np

    #    print ("    Setting probabilities")
    dec = np.array([1.5, 2.0, 3.0, 4.0, 5.0, 7.5, 10.0])
    """
    -   Estos valores están elegidos intencionalmente para crear una serie de divisiones dentro de cada orden de magnitud en el eje de 
        períodos de retorno.
    -   Es una práctica común en hidrología y análisis de frecuencia usar subdivisiones logarítmicas (por ejemplo, “subdivisión decadal”).
    -   Los valores permiten generar períodos de retorno como: 1.5, 2, 3, 4, 5, 7.5, y 10 veces una potencia de 10 
        (por ejemplo: 15, 20, 30, 40, 50, 75, 100, etc).
    -   Así, no solo tienes los enteros "10, 100, 1000", sino también valores intermedios que hacen el gráfico más útil y la tabla 
        más completa.
    """
    dec = -np.sort(-dec)    #Técnica para ordenar de mayor a menor. np.sort ordena por defecto de menor a mayor
    exp = 10.0**(exp-np.arange(1.,exp+1,1.))
    """
    -   Esta función genera un array con las potencias de 10 para cada orden de magnitud desde el máxima hacia abajo.
        * Si exp = 4: np.arange(1.,5.,1.) da [1,2,3,4]
        * exp-np.arange(1.,exp+1,1.) da [3,2,1,0]
        * 10.**[3,2,1,0] da [1000, 100, 10, 1]
    El proposito de este array generado es crear subdivisiones entre decadas para graficar y tabular de manera mas detallada los T
    intermedios.
    """
    T1=np.outer(dec,exp)
    T2=T1.T.flatten()
    T3=T2[T2>=2]
    """
    - T1:   Calcula todos los posibles períodos de retorno intermedios combinando cada valor de dec con cada potencia de 10 en exp,
            generando así una matriz de períodos de retorno "equiespaciados" en escala logarítmica.
    - T2:   Transpone la matriz T1 y la aplana en un solo vector para obtener una lista unidimensional de todos los períodos de 
            retorno generados.
    - T3:   Filtra los períodos de retorno generados, quedándose solo con aquellos mayores o iguales a 2 años.
    """
    P_l=1./T3               #Se calcula la probabilidad de excedencia para cada T.
    P_h=np.sort(1-P_l)      #Se calcula la probabilidad de no excedencia para cada T.

    # Calcula los períodos de retorno asociados a cada probabilidad de excedencia (T_l) y no excedencia (T_h)
    T_l = 1 / P_l
    T_h = 1 / (1 - P_h)

    # Concatena las probabilidades de excedencia (excepto el último valor para evitar duplicados) y las de no excedencia,
    # y hace lo mismo para los períodos de retorno asociados. Redondea las probabilidades según el orden de magnitud para
    # asegurar precisión, y los períodos de retorno a 3 decimales. Esto genera una grilla simétrica y continua de valores,
    # útil para graficar o tabular curvas de frecuencia.
    """
    Recordar que en python al utilizar [0:-1] estamos diciendo que tome todos los valores del array desde la posición cero excepto
    el que se encuentra en la última posición. Si quisieramos tomarlos todos, podríamos usar [:], [0:] ó simplemente no explicitar
    ningun indice (se nos devolvera todo el array).
    En Python, la notación [n:m] significa: toma todos los valores del array desde la posición n (incluida) hasta la posición m (excluida),
    es decir, incluye el elemento en la posición n y termina en el elemento m-1.
    """
    P = np.round(np.concatenate((P_l[0:-1], P_h)), int(round(np.log(exp[0])) + 3))
    T = np.round(np.concatenate((T_l[0:-1], T_h)), 3)

    return P, T



    

def Fit_distribs(dict_obs_data):
    """
    
    """
    df_Obs=dict_obs_data["Obs_data"]
    N_p=dict_obs_data["Observaciones"]
    N_a=dict_obs_data["Years"] 

    T_Table=np.array(T)         #Periodos de retorno a evaluar en un np.array
    P_Table=1.0 - 1.0/T_Table   #Se determina la probabilidad de no excedencia para cada T.
    P_Grid, T_Grid = probs(OOM) #Con funcion probs se genera grilla equiespaciada de P y T.

    print ("    Fitting distributions for ", end="")
    
    # sorting records by probability
    Y_Obs=df_Obs[df_Obs.columns.values[0]].values
    P_Obs=df_Obs[df_Obs.columns.values[1]].values



    #ACA QUEDÉ

# PARAMETROS DEL ANÁLISIS DE FRECUENCIA
# Periodos de retorno a evaluar:
T=[2,5,10,20,25,50,100,200,500,1000,10000]
# Numero de ordenes de magnitud de los periodos de retorno:
OOM=math.ceil(math.log10(max(T)))
"""
math.ceil devuelve el menor entero mayor o igual a x.
math.ceil(3.2) devuelve 4.
    
"""

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

