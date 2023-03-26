#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Solution to the one-way tunnel

@author: alvarocamarafernandez
"""

import time
import random
from multiprocessing import Lock, Condition, Process
from multiprocessing import Value

SOUTH = 1
NORTH = 0

NCARS = 60
NPED = 10
TIME_CARS_NORTH = 0.5  # a new car enters each 0.5s
TIME_CARS_SOUTH = 0.5  # a new car enters each 0.5s
TIME_PED = 5 # a new pedestrian enters each 5s
TIME_IN_BRIDGE_CARS = (1, 0.5) # normal 1s, 0.5s
TIME_IN_BRIDGE_PEDESTRIAN = (30, 10) # normal 1s, 0.5s

#cotas: Estas cotas nos ayudarán a saber a quién tendremos que dar prioridad a la hora de dejar pasar a la gente.
#por ejemplo, si tenemos 3 coches (o mas) en el norte esperando, hay que darles prioridad para que pasen puesto que se están acumulando demasiados.

COTA_COCHES_NORTE = 3
COTA_COCHES_SUR = 3
COTA_PEATONES = 2

class Monitor():
    def __init__(self): #introducirmos aquí las variables que tenemos que inicializar.
        """
        Necesitamos meter un Lock() por la definicion de monitor. 
        Es decir, si varias operaciones de un mismo monitor son llamadas por un mismo proceso => este lock garantiza que no se ejecuten a la vez (hay exclusión mutua)
        Pero, sin embargo, si se llaman a operaciones de distintos monitores => las ejecuciones de estas operaciones pueden entremezclarse por ser distintos monitores.
        Cada vez que ejecutamos un método
        """
        self.mutex = Lock() 
        self.patata = Value('i', 0)
        
        #inicializamos los coches en cada una de las direcciones y los peatones a 0 -> inicialmente no tenemos ni coches ni peatones.
        self.cochesNorteDentro = Value('i', 0)                  #numero de coches provenientes del NORTE dentro del puente
        self.cochesSurDentro = Value('i', 0)                    #numero de coches provenientes del SUR dentro del puente
        self.peatonesDentro = Value('i', 0)                     #numero de peatones dentro del puente.
        
        #inicializamos las variables condicion, que son una funcion del multiprocessing. Estas expresiones deben evaluarse como verdaderas o falsas.
        self.pasanNorte = Condition(self.mutex)                 #condición que evalúa si pasan coches del Norte
        self.pasanSur = Condition(self.mutex)                   #condición que evalúa si pasan coches del Sur
        self.pasanPeatones = Condition(self.mutex)              #condición que evalúa si pasan peatones.
        
        #añadimos para evitar la inanición: pondremos una especie de 'cota' para que cuando haya demasiados esperando, se les de prioridad de algun modo
        self.cochesNorteEsperando = Value('i', 0)               #numero de coches en el norte esperando para entrar
        self.cochesSurEsperando = Value('i', 0)                 #numero de coches en el sur esperando para entrar
        self.peatonesEsperando = Value('i', 0)                  #numero de peatones esperando para entrar
        
            #Finalmente, añadimos sus correspondientes variables de condicion y, analogamente, deben evaluarse como verdaderas o falsas.
        self.esperanNorte = Condition(self.mutex)               #para saber si los coches del norte podrían pasar o todavia no (indica, en cierto modo, la prioridad)
        self.esperanSur = Condition(self.mutex)                 #para saber si los coches del sur podrían pasar o todavia no
        self.esperanPeatones = Condition(self.mutex)            #para saber si los peatones podrían pasar o todavia no
    
    #definimos los siguientes métodos para evaluar las variables condición. Siempre van a devolver un booleano.
    
    def adelanteNorte(self) ->bool:
        return self.cochesSurDentro.value == 0 and self.peatonesDentro.value == 0
    
    def adelanteSur(self) -> bool:
        return self.cochesNorteDentro.value == 0 and self.peatonesDentro.value == 0
    
    def adelantePeatones(self) -> bool:
        return self.cochesNorteDentro.value == 0 and self.cochesSurDentro.value == 0
    
    def esperandoCochesNorte(self) ->bool:
        return self.cochesSurEsperando.value <= COTA_COCHES_SUR and self.peatonesEsperando.value <= COTA_PEATONES
    
    def esperandoCochesSur(self) -> bool:
        return self.cochesNorteEsperando.value <= COTA_COCHES_NORTE and self.peatonesEsperando.value <= COTA_PEATONES
    
    def esperandoPeatones(self) -> bool:
        return self.cochesNorteEsperando.value <= COTA_COCHES_NORTE and self.cochesSurEsperando.value <= COTA_COCHES_SUR
    
    def wants_enter_car(self, direction: int) -> None: #esto indica que direccion es un entero y que no vamos a devolver nada
    
    
        """
        Método que nos dice cuándo un determinado coche va a querer entrar al puente. Se pondrá a esperar hasta que le toque pasar.
        La dirección no se tendrá en cuenta, en el sentido de que el código es simétrico si el coche quiere entrar del sur que del norte.
        Empezaremos distinguiendo si es o no del norte.
        En el caso de los coches que vienen por el sur, el caso es análogo => no comentamos dicho caso.
        """
        
        self.mutex.acquire() #solo puede ejecutarse 1 método a la vez por cómo son los monitores, por eso se pone este Lock inicial en cada uno de los métodos que se definen
        self.patata.value += 1
        
        if direction == NORTH:                                                      #suponemos que el coche que quiere entrar viene del norte
            self.cochesNorteEsperando.value = self.cochesNorteEsperando.value + 1   #incrementamos el contador de coches que hay esperando en 1 unidad
            
            self.esperanNorte.wait_for(self.esperandoCochesNorte)                   #tenemos que asegurarnos de que no hay mas coches del sur (ni peatones) de la cuenta para darles permiso y que pasen
            self.pasanNorte.wait_for(self.adelanteNorte)                            #cuando ya sabemos que pueden pasar los del norte (nadie tiene preferencia), 
                                                                                    #tenemos que esperar a que no haya ningun coche proveniente del sur ni ningun peatón
            
            self.cochesNorteDentro.value = self.cochesNorteDentro.value + 1         #una vez ya puedan pasar los coches del norte, 
                                                                                    #aumentamos el contador de coches en 1 unidad
            self.cochesNorteEsperando.value = self.cochesNorteEsperando.value - 1   #y bajamos el contador de vehículos del norte esperando en 1 unidad 
                                                                                    #(pues está pasando el puente y ya no espera)
            
            
            if self.cochesNorteEsperando.value <= COTA_COCHES_NORTE:                #si llegamos al caso en el que el numero de coches que hay esperando
                                                                                    #en el norte es menor que la cota que hemos puesto inicialmente
                
                self.pasanSur.notify_all()                                          #tenemos que notificar de esto a los coches que hay en el Sur
                self.pasanPeatones.notify_all()                                     #y tenemos que notificar también a los peatones
        
        
        else:
            self.cochesSurEsperando.value = self.cochesSurEsperando.value + 1 
            
            self.esperanSur.wait_for(self.esperandoCochesSur)
            self.pasanSur.wait_for(self.adelanteSur)
            
            self.cochesSurDentro.value = self.cochesSurDentro.value + 1
            self.cochesSurEsperando.value = self.cochesSurEsperando.value - 1
            
            
            if self.cochesSurEsperando.value <= COTA_COCHES_NORTE:
                
                self.pasanPeatones.notify_all()
                self.pasanNorte.notify_all()

        self.mutex.release()

    def leaves_car(self, direction: int) -> None: #un determinado coche en una direccion quiere (va a) salir del puente.
        self.mutex.acquire() 
        self.patata.value += 1
        
        if direction == NORTH:                                                      #si el coche que quiere salir del puente viene del norte
            self.cochesNorteDentro.value = self.cochesNorteDentro.value -1          #disminuimos en 1 unidad el valor de los coches del norte que hay dentro del puente
            
            if self.cochesNorteDentro.value == 0:                                   #si al disminuir esta variable (coches del norte dentro del puente) llegamos a 0, entonces...
                self.pasanSur.notify_all()                                          #tenemos que avisar a los coches del sur que ya no hay coches del norte en el puente
                self.pasanPeatones.notify_all()                                     #y, analogamente, avisar a los peatones.
                
        else:
            self.cochesSurDentro.value = self.cochesSurDentro.value -1
            
            if self.cochesSurDentro.value == 0:
                self.pasanNorte.notify_all()
                self.pasanPeatones.notify_all()
        
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None: #un peatón quiere entrar en el puente
        """
        Se repite el mismo procedimiento que si el peaton fuese "otro coche", pues el razonamiento serñia análogo ya que
        cuando va a pasar un peaton, no puede haber ningún vehiculo dentro del puente.
        """
        self.mutex.acquire()
        self.patata.value += 1
        
        self.peatonesEsperando.value = self.peatonesEsperando.value +1
        
        self.esperanPeatones.wait_for(self.esperandoPeatones)
        self.pasanPeatones.wait_for(self.adelantePeatones)
        
        self.peatonesDentro.value = self.peatonesDentro.value + 1
        self.peatonesEsperando.value = self.peatonesEsperando.value -1
        
        if self.peatonesEsperando.value <= COTA_PEATONES:
            self.esperanNorte.notify_all()
            self.esperanSur.notify_all()
        
        self.mutex.release()

    def leaves_pedestrian(self) -> None: #un peaton quiere salir del puente
        self.mutex.acquire()
        self.patata.value += 1
        
        self.peatonesDentro.value = self.peatonesDentro.value - 1
        if self.peatonesDentro.value == 0:
            self.pasanNorte.notify_all()
            self.pasanSur.notify_all()
        
        self.mutex.release()

    def __repr__(self) -> str:
        return f'Monitor: {self.patata.value}'


#completamos estas funciones, para darles un delay a los coches o peatores respectivamente. Suponemos que un peaton tarda mas en cruzar que un coche (delay mas alto)
def delay_car_north(factor = 0.15) -> None:
    time.sleep(random.random() * factor)

def delay_car_south(factor = 0.15) -> None:
    time.sleep(random.random() * factor)

def delay_pedestrian(factor = 0.3) -> None:
    time.sleep(random.random() * factor)

def car(cid: int, direction: int, monitor: Monitor)  -> None:
    print(f"car {cid} heading {direction} wants to enter. {monitor}")
    monitor.wants_enter_car(direction)
    print(f"car {cid} heading {direction} enters the bridge. {monitor}")
    if direction==NORTH :
        delay_car_north()
    else:
        delay_car_south()
    print(f"car {cid} heading {direction} leaving the bridge. {monitor}")
    monitor.leaves_car(direction)
    print(f"car {cid} heading {direction} out of the bridge. {monitor}")

def pedestrian(pid: int, monitor: Monitor) -> None:
    print(f"pedestrian {pid} wants to enter. {monitor}")
    monitor.wants_enter_pedestrian()
    print(f"pedestrian {pid} enters the bridge. {monitor}")
    delay_pedestrian()
    print(f"pedestrian {pid} leaving the bridge. {monitor}")
    monitor.leaves_pedestrian()
    print(f"pedestrian {pid} out of the bridge. {monitor}")



def gen_pedestrian(monitor: Monitor) -> None:
    pid = 0
    plst = []
    for _ in range(NPED):
        pid += 1
        p = Process(target=pedestrian, args=(pid, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/TIME_PED))

    for p in plst:
        p.join()

def gen_cars(direction: int, time_cars, monitor: Monitor) -> None:
    cid = 0
    plst = []
    for _ in range(NCARS):
        cid += 1
        p = Process(target=car, args=(cid, direction, monitor))
        p.start()
        plst.append(p)
        time.sleep(random.expovariate(1/time_cars))

    for p in plst:
        p.join()

def main():
    monitor = Monitor()
    gcars_north = Process(target=gen_cars, args=(NORTH, TIME_CARS_NORTH, monitor))
    gcars_south = Process(target=gen_cars, args=(SOUTH, TIME_CARS_SOUTH, monitor))
    gped = Process(target=gen_pedestrian, args=(monitor,))
    gcars_north.start()
    gcars_south.start()
    gped.start()
    gcars_north.join()
    gcars_south.join()
    gped.join()
    # print("Ya no hay mas gente esperando ni dentro del puente.")


if __name__ == '__main__':
    main()
