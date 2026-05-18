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
    return -media * math.log(1-u)


def gen_normal(mu, sigma):

    while True:

        u1 = max(g.uniforme(),1e-10)
        u2 = g.uniforme()

        z = math.sqrt(
            -2*math.log(u1)
        ) * math.cos(
            2*math.pi*u2
        )

        x = mu + sigma*z

        if x>0:
            return x


def gen_tipo():

    u = g.uniforme()

    if u < 0.45:
        return 1

    elif u < 0.70:
        return 2

    elif u < 0.80:
        return 3

    return 4


PRECIOS = {
    1:0,
    2:350,
    3:500,
    4:750
}

JORNADA = 480


class Cliente:

    def __init__(self,id,t):

        self.id=id
        self.tipo_servicio=gen_tipo()


# SIMULACIÓN


class HappyComputing:

    def __init__(self):

        self.reloj=0
        self.id_evento=0
        self.fel=[]
        self.vendedores=2
        self.tecnicos=3
        self.especialista=1
        self.cola_vendedores=deque()
        self.cola_reparacion=deque()
        self.cola_cambios=deque()
        self.ganancia=0
        self.llegadas=0
        self.conteo_servicios={
            1:0,
            2:0,
            3:0,
            4:0
        }


        self.max_cola_vendedores=0
        self.max_cola_reparacion=0
        self.max_cola_cambios=0



    def evento(
            self,
            tiempo,
            tipo,
            cliente=None
    ):

        self.id_evento += 1

        heapq.heappush(
            self.fel,
            (
                tiempo,
                self.id_evento,
                tipo,
                cliente
            )
        )


    def correr(self):

        self.evento(
            gen_exponencial(20),
            "LLEGADA"
        )

        while self.fel:

            tiempo,\
            _,\
            tipo,\
            cliente=heapq.heappop(
                self.fel
            )

            if (
                tiempo>JORNADA
                and
                tipo=="LLEGADA"
            ):
                continue

            self.reloj=tiempo

            if tipo=="LLEGADA":

                self.llegada()

            elif tipo=="FIN_VEND":

                self.fin_vendedor(
                    cliente
                )

            elif tipo=="FIN_TEC":

                self.fin_tecnico(
                    cliente
                )

            elif tipo=="FIN_ESP":

                self.fin_especialista(
                    cliente
                )

        return (

            self.ganancia,
            self.llegadas,
            self.conteo_servicios,
            self.max_cola_vendedores,
            self.max_cola_reparacion,
            self.max_cola_cambios
        )


    def llegada(self):

        self.llegadas += 1

        c=Cliente(
            self.llegadas,
            self.reloj
        )

        self.conteo_servicios[
            c.tipo_servicio
        ]+=1


        self.evento(
            self.reloj+
            gen_exponencial(20),
            "LLEGADA"
        )


        if self.vendedores>0:

            self.vendedores-=1

            self.evento(
                self.reloj+
                gen_normal(
                    5,
                    2
                ),
                "FIN_VEND",
                c
            )

        else:

            self.cola_vendedores.append(
                c
            )

            self.max_cola_vendedores=max(
                self.max_cola_vendedores,
                len(
                    self.cola_vendedores
                )
            )



    def fin_vendedor(
            self,
            c
    ):

        if self.cola_vendedores:

            prox=\
            self.cola_vendedores.popleft()

            self.evento(
                self.reloj+
                gen_normal(
                    5,
                    2
                ),
                "FIN_VEND",
                prox
            )

        else:

            self.vendedores+=1


        if c.tipo_servicio==4:

            self.ganancia+=750


        elif c.tipo_servicio==3:

            self.cambio(c)

        else:

            self.reparacion(c)


    def reparacion(
            self,
            c
    ):

        if self.tecnicos>0:

            self.tecnicos-=1

            self.evento(
                self.reloj+
                gen_exponencial(
                    20
                ),
                "FIN_TEC",
                c
            )

        elif (
                self.especialista>0
                and
                not self.cola_cambios
        ):

            self.especialista-=1

            self.evento(
                self.reloj+
                gen_exponencial(
                    20
                ),
                "FIN_ESP",
                c
            )

        else:

            self.cola_reparacion.append(
                c
            )

            self.max_cola_reparacion=max(
                self.max_cola_reparacion,
                len(
                    self.cola_reparacion
                )
            )


    def cambio(
            self,
            c
    ):

        if self.especialista>0:

            self.especialista-=1

            self.evento(
                self.reloj+
                gen_exponencial(
                    15
                ),
                "FIN_ESP",
                c
            )

        else:

            self.cola_cambios.append(
                c
            )

            self.max_cola_cambios=max(
                self.max_cola_cambios,
                len(
                    self.cola_cambios
                )
            )


    def fin_tecnico(
            self,
            c
    ):

        self.ganancia+=\
        PRECIOS[
            c.tipo_servicio
        ]


        if self.cola_reparacion:

            prox=\
            self.cola_reparacion.popleft()

            self.evento(
                self.reloj+
                gen_exponencial(
                    20
                ),
                "FIN_TEC",
                prox
            )

        else:

            self.tecnicos+=1


    def fin_especialista(
            self,
            c
    ):

        self.ganancia+=\
        PRECIOS[
            c.tipo_servicio
        ]


        if self.cola_cambios:

            prox=\
            self.cola_cambios.popleft()

            self.evento(
                self.reloj+
                gen_exponencial(
                    15
                ),
                "FIN_ESP",
                prox
            )

        elif self.cola_reparacion:

            prox=\
            self.cola_reparacion.popleft()

            self.evento(
                self.reloj+
                gen_exponencial(
                    20
                ),
                "FIN_ESP",
                prox
            )

        else:

            self.especialista+=1


# VALIDACIÓN


def validar_modelo(
        n_replicas=1000
):

    print(
        f"Ejecutando "
        f"{n_replicas} "
        f"simulaciones..."
    )

    total_g=0
    total_l=0

    total_s={
        1:0,
        2:0,
        3:0,
        4:0
    }

    total_qv=0
    total_qr=0
    total_qc=0


    for _ in range(
            n_replicas
    ):

        sim=HappyComputing()

        g,\
        l,\
        s,\
        qv,\
        qr,\
        qc=sim.correr()

        total_g+=g
        total_l+=l

        total_qv+=qv
        total_qr+=qr
        total_qc+=qc

        for k in total_s:

            total_s[k]+=s[k]


    prom_l=total_l/n_replicas
    prom_g=total_g/n_replicas

    err=abs(
        prom_l-24
    )/24*100


    print("\n"+"="*45)

    print(
        "REPORTE VALIDACIÓN"
    )

    print("="*45)

    print(
        f"\n1) ARRIBOS:"
    )

    print(
        f"Promedio: "
        f"{prom_l:.2f}"
    )

    print(
        f"Teórico: 24"
    )

    print(
        f"Error:"
        f"{err:.2f}%"
    )


    print(
        "\n2) "
        "SERVICIOS:"
    )

    teorico={
        1:45,
        2:25,
        3:10,
        4:20
    }

    for k in [1,2,3,4]:

        obs=(
            total_s[k]/
            total_l
        )*100

        print(
        f"Tipo{k}: "
        f"Obs {obs:.2f}% "
        f"| Teor "
        f"{teorico[k]}%"
        )


    print(
        "\n3) GANANCIA:"
    )

    print(
        f"${prom_g:.2f}"
    )

    print(
        "\n4) CONGESTIÓN:"
    )

    print(
        "Cola vendedores:",
        total_qv/
        n_replicas
    )

    print(
        "Cola reparación:",
        total_qr/
        n_replicas
    )

    print(
        "Cola cambios:",
        total_qc/
        n_replicas
    )

    print("="*45)


if __name__=="__main__":

    validar_modelo(1000)