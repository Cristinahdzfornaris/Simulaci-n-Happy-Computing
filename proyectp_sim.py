import heapq
import math
from collections import deque


class Generador:
    def __init__(self, semilla=12345):
        self.x = semilla
        self.a = 1664525
        self.c = 1013904223
        self.m = 2**32

    def uniforme(self):
        self.x = (self.a * self.x + self.c) % self.m
        return self.x / self.m

g = Generador()

# DISTRIBUCIONES

def gen_exponencial(media):
    u = g.uniforme()
    return -media * math.log(1 - u)

def gen_normal(mu, sigma):
    while True:
        u1 = g.uniforme()
        u2 = g.uniforme()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        x = mu + sigma * z
        if x > 0: return x

def gen_tipo():
    u = g.uniforme()
    if u < 0.45: return 1   
    elif u < 0.70: return 2 
    elif u < 0.80: return 3
    return 4               

# LÓGICA DEL TALLER

PRECIOS = {1: 0, 2: 350, 3: 500, 4: 750}
JORNADA = 480

class Cliente:
    def __init__(self, id, t):
        self.id = id
        self.tipo_servicio = gen_tipo()

class HappyComputing:
    def __init__(self):
        self.reloj = 0
        self.id_evento = 0
        self.fel = []
        self.vendedores = 2
        self.tecnicos = 3
        self.especialista = 1
        self.cola_vendedores = deque()
        self.cola_reparacion = deque()
        self.cola_cambios = deque()
        self.ganancia = 0
        self.llegadas = 0
        self.conteo_servicios = {1:0, 2:0, 3:0, 4:0}

    def evento(self, tiempo, tipo, cliente=None):
        self.id_evento += 1
        heapq.heappush(self.fel, (tiempo, self.id_evento, tipo, cliente))

    def correr(self):
        self.evento(gen_exponencial(20), "LLEGADA")
        while self.fel:
            tiempo, _, tipo, cliente = heapq.heappop(self.fel)
            if tiempo > JORNADA and tipo == "LLEGADA": continue
            self.reloj = tiempo
            if tipo == "LLEGADA": self.llegada()
            elif tipo == "FIN_VEND": self.fin_vendedor(cliente)
            elif tipo == "FIN_TEC": self.fin_tecnico(cliente)
            elif tipo == "FIN_ESP": self.fin_especialista(cliente)
        return self.ganancia, self.llegadas, self.conteo_servicios

    def llegada(self):
        self.llegadas += 1
        c = Cliente(self.llegadas, self.reloj)
        self.conteo_servicios[c.tipo_servicio] += 1
        self.evento(self.reloj + gen_exponencial(20), "LLEGADA")
        if self.vendedores > 0:
            self.vendedores -= 1
            self.evento(self.reloj + gen_normal(5, 2), "FIN_VEND", c)
        else:
            self.cola_vendedores.append(c)

    def fin_vendedor(self, c):
        if self.cola_vendedores:
            prox = self.cola_vendedores.popleft()
            self.evento(self.reloj + gen_normal(5, 2), "FIN_VEND", prox)
        else:
            self.vendedores += 1

        if c.tipo_servicio == 4: self.ganancia += PRECIOS[4]
        elif c.tipo_servicio == 3: self.cambio(c)
        else: self.reparacion(c)

    def reparacion(self, c):
        if self.tecnicos > 0:
            self.tecnicos -= 1
            self.evento(self.reloj + gen_exponencial(20), "FIN_TEC", c)
        elif self.especialista > 0 and not self.cola_cambios:
            self.especialista -= 1
            self.evento(self.reloj + gen_exponencial(20), "FIN_ESP", c)
        else:
            self.cola_reparacion.append(c)

    def cambio(self, c):
        if self.especialista > 0:
            self.especialista -= 1
            self.evento(self.reloj + gen_exponencial(15), "FIN_ESP", c)
        else:
            self.cola_cambios.append(c)

    def fin_tecnico(self, c):
        self.ganancia += PRECIOS[c.tipo_servicio]
        if self.cola_reparacion:
            prox = self.cola_reparacion.popleft()
            self.evento(self.reloj + gen_exponencial(20), "FIN_TEC", prox)
        else:
            self.tecnicos += 1

    def fin_especialista(self, c):
        self.ganancia += PRECIOS[c.tipo_servicio]
        if self.cola_cambios:
            prox = self.cola_cambios.popleft()
            self.evento(self.reloj + gen_exponencial(15), "FIN_ESP", prox)
        elif self.cola_reparacion:
            prox = self.cola_reparacion.popleft()
            self.evento(self.reloj + gen_exponencial(20), "FIN_ESP", prox)
        else:
            self.especialista += 1


def validar_modelo(n_replicas=1000):
    print(f"Iniciando proceso de validación con {n_replicas} réplicas...")
    
    total_ganancia = 0
    total_llegadas = 0
    total_servicios = {1:0, 2:0, 3:0, 4:0}

    for _ in range(n_replicas):
        sim = HappyComputing()
        g_dia, l_dia, s_dia = sim.correr()
        total_ganancia += g_dia
        total_llegadas += l_dia
        for k in total_servicios:
            total_servicios[k] += s_dia[k]

    # Cálculos promedio
    avg_llegadas = total_llegadas / n_replicas
    avg_ganancia = total_ganancia / n_replicas
    
    # 1. Validación de Arribos
    error_llegadas = abs(avg_llegadas - 24) / 24 * 100

    # 2. Validación de Mix de Servicios
    print("\n" + "="*40)
    print("REPORTE DE VALIDACIÓN ESTADÍSTICA")
    print("="*40)
    print(f"1. ARRIBOS: Promedio {avg_llegadas:.2f} (Teórico: 24.0)")
    print(f"   Error relativo: {error_llegadas:.2f}%")
    
    print("\n2. MIX DE SERVICIOS (Frecuencia Observada vs Teórica):")
    probs_teoricas = {1: 0.45, 2: 0.25, 3: 0.10, 4: 0.20}
    for k in [1,2,3,4]:
        obs = (total_servicios[k] / total_llegadas) * 100
        teor = probs_teoricas[k] * 100
        print(f"   Tipo {k}: Obs {obs:5.2f}% | Teor {teor:5.2f}% | Dif {abs(obs-teor):5.2f}%")

    # 3. Validación de Ganancia
    ganancia_teorica_max = 6900
    print(f"\n3. GANANCIA: Promedio Diario ${avg_ganancia:.2f}")
    print(f"   Referencia Teórica Máxima: ${ganancia_teorica_max:.2f}")
    print(f"   (La diferencia se debe a clientes que no terminan su proceso al cierre)")
    print("="*40)

if __name__ == "__main__":
    validar_modelo(1000)
