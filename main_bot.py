def busca_arreglo(busca):#el peor ejemplo
    print(f"Buscando arreglo : {busca}")
    arreglo_palabras = ["rojo","verde", "azul"]

    for item in arreglo_palabras:
        print(f"Palabra : {item}")
        if item == busca:
            print("palabra encontrada")
            return "encontrada en el arreglo"
    return "no se encontro en el arreglo"


def busca_in_file(busca):
    file = open ('palabra.txt', 'r')
    if busca in file.read():
        print("lo encontre en file read")
        return 1
    file= open('groserias.txt', 'r')
    if busca in file.read():
        print("\n\t\t LO ENCONTRE CON FILE READ ")
        return 3
    file.close()
    return False

def buscar_with_file(busca):
    with open ('palabras.txt') as file:
        data = True
        while data:
            data = file.readline()
            print(data)
        
###texto = "mi casa es green"

###texto_analizar = texto.split()
###print(texto_analizar)
