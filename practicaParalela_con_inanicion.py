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

"""
Esta solución propuesta es efectiva, en el sentido que satisface el objetivo de la práctica. 
Sin embargo, hay 1 objetivo que no satisface, que es el de la inanición.

Tenemos 2 tipos de coches (Coches del Norte y Coches del Sur) y los peatones. En total 3 "objetos".
Si de un objeto, no paran de llegar al puente, esta solución no dejaría pasar a los otros 2 objetos restantes.
Para intentar solucionar la inanición, se han añadido unas cotas en el otro archivo que hacen como de 'tope' y que 
no haya demasiados objetos esperando en el puente a poder pasar.

Esta opción no contempla este caso, se contempla en el fichero practica_Paralela_2.py. En cierto modo, este archivo está 'incompleto'.
"""

class Monitor():
    def __init__(self):
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
    
    #definimos los siguientes métodos para evaluar las variables condición. Siempre van a devolver un booleano.
    
    def adelanteNorte(self) ->bool:
        return self.cochesSurDentro.value == 0 and self.peatonesDentro.value == 0
    
    def adelanteSur(self) -> bool:
        return self.cochesNorteDentro.value == 0 and self.peatonesDentro.value == 0
    
    def adelantePeatones(self) -> bool:
        return self.cochesNorteDentro.value == 0 and self.cochesSurDentro.value == 0
    

    def wants_enter_car(self, direction: int) -> None:
        
        """
        Método que nos dice cuándo un determinado coche va a querer entrar al puente. Se pondrá a esperar hasta que le toque pasar.
        La dirección no se tendrá en cuenta, en el sentido de que el código es simétrico si el coche quiere entrar del sur que del norte.
        Empezaremos distinguiendo si es o no del norte.
        En el caso de los coches que vienen por el sur, el caso es análogo => no comentamos dicho caso.
        """
        
        self.mutex.acquire()
        self.patata.value += 1
        
        if direction == NORTH:                                                      #suponemos que el coche que quiere entrar viene del norte 
            self.pasanNorte.wait_for(self.adelanteNorte)                            #esperamos a que no haya ningún objeto de los otros 2 grupos en el puente, y cuando suceda esto, continuamos
            self.cochesNorteDentro.value = self.cochesNorteDentro.value +1          #aumentamos el contador de coches dentro del puente en 1 unidad.
        
        else:
            self.pasanSur.wait_for(self.adelanteSur)
            self.cochesSurDentro.value = self.cochesSurDentro.value +1
        
        self.mutex.release()

    def leaves_car(self, direction: int) -> None:
        self.mutex.acquire() 
        self.patata.value += 1
        
        if direction == NORTH:                                                      #si el coche que quiere salir del puente viene del norte
            self.cochesNorteDentro.value = self.cochesNorteDentro.value -1          #disminuimos en 1 unidad el valor de los coches del norte que hay dentro del puente
            if self.cochesNorteDentro.value == 0:                                   #si al disminuir esta variable (coches del norte dentro del puente) llegamos a 0, entonces...
                self.pasanSur.notify_all()                                          #tenemos que avisar a los coches del sur que ya no hay coches del norte en el puente
                self.pasanPeatones.notify_all()                                     #y, analogamente, avisar a los peatones.
        else:
            self.cochesSurDentro.value = self.cochesSurDentro.value -1
            if self.cochesSurDentro == 0:
                self.pasanNorte.notify_all()
                self.pasanPeatones.notify_all()
        
        self.mutex.release()

    def wants_enter_pedestrian(self) -> None:
        
        """
        Se repite el mismo procedimiento que si el peaton fuese "otro coche", pues el razonamiento serñia análogo ya que
        cuando va a pasar un peaton, no puede haber ningún vehiculo dentro del puente.
        """
        
        self.mutex.acquire()
        self.patata.value += 1
        
        self.pasanPeatones.wait_for(self.adelantePeatones)
        self.peatonesDentro.value = self.peatonesDentro.value + 1
        
        self.mutex.release()

    def leaves_pedestrian(self) -> None:
        self.mutex.acquire()
        self.patata.value += 1
        
        self.peatonesDentro.value = self.peatonesDentro.value -1
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
