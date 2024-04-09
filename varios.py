## Obtención de datos poblacionales del artículo https://www.ambito.com/informacion-general/ciudad-buenos-aires/datos-del-censo-2022-cual-es-la-comuna-mas-habitada-la-n5641890
## Contrastado con https://www.indec.gob.ar/ftp/cuadros/poblacion/cnphv2022_resultados_provisionales.pdf
## Obtenemos que falta la información de la Comuna 2

# with open('data/poblacion_comuna.txt', 'r', encoding='utf-8') as f:
#     texto = f.readlines()

# texto = "".join(texto)

# patron = r"Comuna (\d+).*?(\d{3}(?:\.\d{3})*)"

# resultados = re.findall(patron, texto)
# data = []

# for comuna, cantidad in resultados:
#     cantidad = cantidad.replace(".", "") # Eliminar los puntos de los números de habitantes
#     data.append({"Comuna": int(comuna), "Poblacion": int(cantidad)})

# data.append({"Comuna": 2, "Poblacion": 158368})

# data_pob_comunas = pd.DataFrame(data)



import folium

m = folium.Map

import pandas as pd

url = (
    "https://raw.githubusercontent.com/python-visualization/folium/main/examples/data"
)
state_geo = f"{url}/us-states.json"
state_unemployment = f"{url}/US_Unemployment_Oct2012.csv"
state_data = pd.read_csv(state_unemployment)

print(state_geo)

