# practica_paralela_2
En este proyecto vamos a encontrar 3 archivos: 2 de ellos son archivos Python y el otro de ellos es un archivo .pdf

En el archivo .pdf, tenemos la solución al problema del puente de Ambite en papel, mediante el uso de monitores.
Este puente se encuentra en el río Tajuña, y por él cruzan tanto peatones como vehiculos, sin embargo es tan estrecho
que no pueden pasar 2 vehículos en direcciones contrarias ni peatones simultaneamente. Además, para garantizar la seguridad 
en el puente, se exige que si en algún momento están pasando peatones, no pasen coches por el puente porque podría ser peligroso.
En el archivo pdf, nos encontramos con el pseudocódigo que nos da la solución al problema del puente, junto a la correspondiente 
demostración matemática de que la solución propuesta es segura, no hay inanición (nos aseguramos que todo el mundo acceda y pase 
el puente) y la ausencia de deadlocks (que nuestro programa se quede "congelado").

Por otro lado, usando la plantilla que nos dió Luis Llana, la única cosa que quedaba por hacer era completar la definicion de
la clase monitor. En el archivo practicaParalela_con_inanicion.py, tenemos usa solucion al problema del puente pero que, sin embargo, al
intentar demostrar la exixtencia de inanicion no era posible, así pues tenemos el archivo practicaParalela_2.py que tiene el mismo contenido
que practicaParalela_con_inanicion.py, pero añadiendo una variable global (cota) que, lo que representa es la necesidad de dar prioridad
a un determinado grupo de vehículos (o peatones) para que accedan el puente, y notificar al resto.
