### Carga de librerias ###
import pandas as pd
import numpy as np
import math
import scipy.stats as st
import sys
import warnings

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

def Fit_distribs(dict_obs_data): #POR COMPLETAR!
    """
    Entrega estimaciones de cada distribución seleccionada para datos 
    observados, tabla requerida y los gráficos por hacer.
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

    aux = np.column_stack((P_Obs,Y_Obs))    #Se arma matriz 2D, primera columna con P_Obs y segunda columna con Y_Obs.
    aux = np.sort(aux,0)                    #Se ordena cada columna de menor a mayor de manera independiente (se rompe la relación).

    P_Obs=aux[:,0]
    Y_Obs=aux[:,1]

    # setting data for distribution estimates    
    if positives_only:
        print ("positives values only")
        # if positives only, filter data and adjust probabilities for estimates
        Y_to_fit=df_Obs[df_Obs[df_Obs.columns.values[0]]>0][df_Obs.columns.values[0]].values
        """
        Al hacer positives_only igual a True, obtenemos la serie Y_to_fit en donde se desechan valores negativos y nulos.
        En este punto el codigo sí descarta los valores 0.
        Y_to_fit tiene la serie de datos sin los valores 0 y sin valores negativos.
        """

        # if positives only, transform probabilities to lookup in distributions
        N_Tot=len(Y_Obs)
        N_Pos=len(Y_to_fit)

        P_Obs_to_Dist=1.-(1.-P_Obs)*(N_Tot+0.)/N_Pos      
        P_Grid_to_Dist=1.-(1.-P_Grid)*(N_Tot+0.)/N_Pos
        P_Table_to_Dist=1.-(1.-P_Table)*(N_Tot+0.)/N_Pos

        """
        Hasta el momento en el codigo se han determinado probabilidades de excedencia considerando la muestra total, incluyendo valores
        ceros.
        Como en esta función se descartan los valores 0, entonces se deben corregir las probabilidades de excendencia para reflejar el 
        nuevo tamaño de la muestra. Por eso, se hace una transformación para que la posición/probabilidad de cada dato positivo siga 
        siendo consistente con la muestra original.
        La formula:
            P_corr = 1 - (1 - P_original) * (N_Tot / N_Pos)
        hace lo siguiente:

        1. - P_original: Obtiene la probabilidad de no excedencia (probabilidad acumulada hasta el dato).
        Multiplica por N_Tot/N_Pos: Reescala la probabilidad para reflejar que ahora hay menos datos (solo positivos).
        1 - ...: Vuelve a transformar a probabilidad de excedencia.
        Esto "estira" la probabilidad para que la distribución ajustada a los positivos siga representando correctamente la posición 
        de cada valor en la muestra original.

        Esto es interesante: con Gringorten se asignan probabilidades de no excedencia para cada dato. Luego, estas probabilidades
        con corregidas de acuerdo a los nuevos valores no-nulos que tenemos.
        """
    
    else:
        print ("all values")
        Y_to_fit=Y_Obs

        N_Tot=len(Y_Obs)
        N_Pos=len(Y_to_fit)

        P_Obs_to_Dist=P_Obs
        P_Grid_to_Dist=P_Grid
        P_Table_to_Dist=P_Table

    # Se consolida información de probabilidades
    P_to_Dist=np.concatenate((P_Grid_to_Dist,P_Obs_to_Dist,P_Table_to_Dist))
    P_to_Dist=np.sort(P_to_Dist)

    """
    En P_to_Dist se tiene un solo vector con todas las probabilidades a usar.
    """

    # # Ajustando probabilidades para que correspondan al período mayor (ajuste de duración)
    P_to_Dist_p=P_to_Dist**(N_a/N_p)
    P_Obs_to_Dist_p=P_Obs_to_Dist**(N_a/N_p)
    P_Table_to_Dist_p=P_Table_to_Dist**(N_a/N_p)
    
    # Se unen los vectores de probabilidades originales en un solo array y se ordena este
    # array de menor a mayor.
    P_to_Chart=np.concatenate((P_Grid,P_Obs,P_Table))
    P_to_Chart=np.sort(P_to_Chart)

    # Se crea df_Chart:
    df_Chart=pd.DataFrame(P_to_Chart, columns=["P"])
    df_Chart["Data"]=""

    # creating R2 DataFrame, filtered observed data 
    df_R2=pd.DataFrame(P_Obs, columns=["P"])
    df_R2["Data"]=Y_Obs

    # creating Table DataFrame 
    df_Table=pd.DataFrame(P_Table, columns=["P"])
    df_Table["T"]=T_Table

    """
    Tengo que entender mejor lo que hace esta funcion a partir de aca.
    """

    #   adapted from: https://stackoverflow.com/questions/6620471/fitting-empirical-distribution-to-theoretical-ones-with-scipy-python
    
    i=1
    print ("        ", end="") # Con end="" no se agrega un salto de linea al final (que viene por defecto con print). El cursor queda al final de los espacios impresos, listo para imprimir en la misma linea.

    n= len(DISTRIBUTIONS)

    for dist in DISTRIBUTIONS:
        distribution=getattr(st, dist)

        # sets console text to show progress and current distribution
        if i==1:
            message=str(i)+" of "+str(n)+" ("+str(distribution.name)+")"
            digits=len(message)
            print(message, end="")
      
        else:
            digits_old=digits
            fill=" " * (20-len(str(distribution.name)))
            message=str(i)+" of "+str(n)+" ("+str(distribution.name)+")"+fill
            digits=len(message)
            delete="\b" * (digits_old)
            print("{0}{1:{2}}".format(delete, message, digits), end="")
            sys.stdout.flush()
        i=i+1

        """
        distribution = getattr(st, dist) -> Obtiene el objeto de la distribución:

        Mensaje de progreso (primera vez):
        Si es la primera iteración (i==1):
        - Construye un mensaje como 1 of 6 (norm) y lo imprime directo.
        - Guarda cuántos caracteres imprimió (digits).
        
        Mensaje de progreso (resto de iteraciones):
        Para las siguientes distribuciones:

        - Calcula cuántos caracteres tenía el mensaje anterior (digits_old).
        - Prepara un "relleno" de espacios para mantener alineado el mensaje aunque cambie la longitud del nombre de la distribución.
        - Construye el nuevo mensaje de progreso (ejemplo: 2 of 6 (lognorm)).
        - Calcula la longitud del nuevo mensaje (digits).
        - Prepara una cadena de retroceso (\b) para borrar el mensaje anterior en la consola.
        - Imprime el mensaje usando el retroceso para "sobreescribir" el anterior, manteniendo la actualización en la misma línea.
        - Usa sys.stdout.flush() para asegurarse de que se vea en la consola de inmediato.
        
        Incrementa el contador:
        i=i+1

        ¿Qué efecto tiene todo esto?
        - Cuando ejecutas el script en una terminal, verás solo UNA línea que va actualizando con el estado del bucle, como por ejemplo:

        1 of 6 (norm)

        Luego se reemplaza por:

        2 of 6 (lognorm)

        Y así sucesivamente. En la consola se vera una linea que cambia, no muchas lineas nuevas.
        El texto se sobrescribe gracias al uso de los caracteres de retroceso (\b), así que solo ves el estado actual del progreso.
        Si lo ejecutas en un entorno gráfico o IDE, puede que veas los mensajes uno debajo del otro, pero en una terminal estándar verás solo UNA línea que se va “actualizando”.
        """

def Fitting(datos, distribution):
    #ACA QUEDE (05/07). AL RETOMAR SIGUE CON LA IMPLEMENTACION DE ESTA FUNCION Y LUEGO CONTINUA CON EL ENTENDIMIENTO DE Fit_distribs

        

 



# SETEO DE PARAMETROS INICIALES
positives_only = True       # Si es True, se controla que el ajuste de distribuciones y calculos se hace solo con datos positivos,
                            # ignorando ceros y negativos.

    

# PARAMETROS DEL ANÁLISIS DE FRECUENCIA
# Periodos de retorno a evaluar:
T=[2,5,10,20,25,50,100,200,500,1000,10000]
# Numero de ordenes de magnitud de los periodos de retorno:
OOM=math.ceil(math.log10(max(T)))
"""
math.ceil devuelve el menor entero mayor o igual a x.
math.ceil(3.2) devuelve 4.
    
"""

### DEFINICION NOMBRES DE ARCHIVOS ###
file_name = 'Data.xlsx'                 #Planilla con data a analizar
Res_file_name = 'AF Results.xlsx'    #Planilla de resultados

### Cargar data en DataFrame ###
Data_yr, Data = Load_data(file_name)

### Distribuciones a evaluar ###
DISTRIBUTIONS = [
    "norm",        ###### las clasicas
    "lognorm",     ###### las clasicas
    "gamma",       ###### las clasicas
    "pearson3",    ###### las clasicas
    # "loggamma",    ###### las clasicas
    "gumbel_r",    ###### las clasicas
#    "halfcauchy",  ###### otras
#    "invgamma",    ###### otras
#    "exponweib",   ###### otras
#    "burr",        ###### otras
#    "betaprime",   ###### otras
#    "ncf",         ###### otras
#    "exponnorm",   ###### otras
#    "exponpow",    ###### otras
#   "genextreme",  ###### otras
#    "powerlaw",    ###### otras
    "gengamma",    ###### otras
#   "ncx2",        ###### otras
#    "nct",         ###### otras
#    "mielke",      ###### otras
#    "invgauss",    ###### otras
#    "erlang",      ###### otras
#    "nakagami",    ###### otras
#    "logistic",    ###### otras
#    "uniform",     ###### otras
#    "frechet_r",    ###### otras
#    "frechet_l",    ###### otras
#    "weibull_min",  ###### otras
#    "weibull_max",  ###### otras
    ]

SELECT_N_DIST = len(DISTRIBUTIONS)

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

    # Fitting distributions
    dict_station_results = Fit_distribs(dict_obs_data)

    # creating worksheets
    print("        Exporting FA data...", end="")
    with pd.ExcelWriter(WB_name, engine='openpyxl', mode='w') as writer:
        # Exporting R2 and chart AF info (Chart info includes Table info)
        R2_T = dict_station_results["R2"].transpose()
        R2_T.to_excel(writer, sheet_name="FA", startrow=2)
        dict_station_results["Chart_data"].to_excel(writer, sheet_name="FA", startrow=10)
    print("done")

    N_dist_selection_by_r2=int(min(SELECT_N_DIST, len(dict_station_results["R2"])-2))

    dict_station_results_S=R2_selection(dict_station_results, N_dist_selection_by_r2)
    Selected_distribs=dict_station_results_S["Table_data"].columns.values[2:]

    



 

