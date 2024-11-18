from typing import List, Set, Tuple, Dict, Optional
from enum import Enum
import numpy as np
from numpy.typing import NDArray

class TipoMovimiento(str, Enum):
    NORMAL = "normal"
    ENROQUE = "enroque"
    EN_PASSANT = "en_passant" 
    PROMOCION = "promocion"

class MovimientoAjedrez:
    """Clase para representar un movimiento con toda su información"""
    def __init__(self, desde: str, hasta: str, tipo: TipoMovimiento,
                 info_adicional: Optional[str] = None):
        self.desde = desde
        self.hasta = hasta
        self.tipo = tipo
        self.info_adicional = info_adicional

    def __str__(self) -> str:
        if self.tipo == TipoMovimiento.NORMAL:
            return f"{self.desde} {self.hasta}"
        elif self.tipo == TipoMovimiento.PROMOCION:
            return f"{self.desde} {self.hasta}={self.info_adicional}"
        elif self.tipo == TipoMovimiento.EN_PASSANT:
            return f"{self.desde} {self.hasta} e.p."
        else:  # ENROQUE
            return self.info_adicional  # O-O o O-O-O

    def __eq__(self, other):
        if not isinstance(other, MovimientoAjedrez):
            return False
        return (self.desde == other.desde and
                self.hasta == other.hasta and
                self.tipo == other.tipo and
                self.info_adicional == other.info_adicional)

class MovimientosTablero:
    """Clase optimizada para cálculos comunes"""
    __slots__ = []
    COLUMNAS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    @staticmethod
    def notacion_a_posicion(notacion: str) -> Tuple[int, int]:
        """Convierte notación algebraica a índices de matriz"""
        col = MovimientosTablero.COLUMNAS.index(notacion[0].lower())
        fila = 8 - int(notacion[1])
        return (fila, col)

    @staticmethod
    def posicion_a_notacion(fila: int, col: int) -> str:
        """Convierte índices de matriz a notación algebraica"""
        return f"{MovimientosTablero.COLUMNAS[col]}{8-fila}"

    @staticmethod
    def dentro_tablero(fila: int, col: int) -> bool:
        """Verifica si una posición está dentro del tablero"""
        return 0 <= fila < 8 and 0 <= col < 8

    @staticmethod
    def obtener_direccion_color(color: str) -> int:
        """Dirección de movimiento para peones"""
        return -1 if color == 'B' else 1

    @staticmethod
    def obtener_fila_inicial(color: str) -> int:
        """Fila inicial para peones"""
        return 6 if color == 'B' else 1

class Pieza:
    __slots__ = ['color', 'numero', 'id', 'movida', 'gestor']

    def __init__(self, color: str, numero: int, gestor):
        self.color = color
        self.numero = numero
        self.id = f"{color}{self.__class__.__name__[0]}{numero}"
        self.movida = False
        self.gestor = gestor

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        raise NotImplementedError

    def obtener_hijos(self, pos_actual: Tuple[int, int],
                     tablero: NDArray) -> List[str]:
        raise NotImplementedError

    def _verificar_camino_libre(self,
                              desde: Tuple[int, int],
                              hasta: Tuple[int, int],
                              tablero: NDArray,
                              incluir_destino: bool = True) -> bool:
        """Verifica que no hay piezas en el camino entre dos posiciones"""
        f_desde, c_desde = desde
        f_hasta, c_hasta = hasta

        # Calculamos la dirección del movimiento
        df = 0 if f_desde == f_hasta else (f_hasta - f_desde) // abs(f_hasta - f_desde)
        dc = 0 if c_desde == c_hasta else (c_hasta - c_desde) // abs(c_hasta - c_desde)

        # Verificamos cada casilla en el camino
        f, c = f_desde + df, c_desde + dc
        while (f, c) != (f_hasta, c_hasta):
            if tablero[f][c] != '...':
                return False
            f, c = f + df, c + dc

        # Verificamos el destino si es necesario
        if incluir_destino:
            pieza_destino = tablero[f_hasta][c_hasta]
            return pieza_destino == '...' or pieza_destino[0] != self.color

        return True

    def obtener_movimientos_especiales(self, pos_actual: Tuple[int, int],
                                     tablero: NDArray) -> List[MovimientoAjedrez]:
        """Método base para movimientos especiales"""
        return []

    def obtener_movimientos(self, pos_actual: Tuple[int, int],
                            tablero: NDArray) -> List[MovimientoAjedrez]:
        """Método base que combina movimientos normales y especiales"""
        movimientos = []
        
        # Movimientos normales
        pos_actual_not = MovimientosTablero.posicion_a_notacion(pos_actual[0], pos_actual[1])
        movs_normales = self.obtener_hijos(pos_actual, tablero)
        for mov in movs_normales:
            desde, hasta = mov.split()
            movimientos.append(MovimientoAjedrez(desde, hasta, TipoMovimiento.NORMAL))
            print(f"{desde} -> {hasta}")  # Debug
        
        # Movimientos especiales
        movs_especiales = self.obtener_movimientos_especiales(pos_actual, tablero)
        if movs_especiales:  # Verificar que hay movimientos especiales
            for mov in movs_especiales:
                movimientos.append(mov)
                print(f"Movimiento especial {mov.desde} -> {mov.hasta}")  # Debug
        
        return movimientos
    
class Peon(Pieza):
    __slots__ = ['direccion', 'fila_inicial', 'movimiento_doble_reciente']

    def __init__(self, color: str, numero: int, gestor):
        super().__init__(color, numero, gestor)
        self.direccion = MovimientosTablero.obtener_direccion_color(color)
        self.fila_inicial = MovimientosTablero.obtener_fila_inicial(color)
        self.movimiento_doble_reciente = False

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        df = f_hasta - f_desde
        if (self.color == 'B' and df >= 0) or (self.color == 'N' and df <= 0):
            return False

        # Movimiento vertical
        if c_desde == c_hasta:
            if tablero[f_hasta][c_hasta] != '...':
                return False
            # Un paso
            if abs(df) == 1:
                return True
            # Dos pasos iniciales
            if f_desde == self.fila_inicial and abs(df) == 2:
                f_intermedia = (f_desde + f_hasta) // 2
                return tablero[f_intermedia][c_desde] == '...'
            return False

        # Captura diagonal
        if abs(c_hasta - c_desde) == 1 and abs(df) == 1:
            pieza_destino = tablero[f_hasta][c_hasta]
            return pieza_destino != '...' and pieza_destino[0] != self.color

        return False

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        # Movimiento hacia adelante
        nueva_f = f + self.direccion
        if MovimientosTablero.dentro_tablero(nueva_f, c) and tablero[nueva_f][c] == '...':
            movimientos.append(
                f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, c)}"
            )

            # Movimiento inicial doble
            if not self.movida and f == self.fila_inicial:
                nueva_f = f + 2 * self.direccion
                if MovimientosTablero.dentro_tablero(nueva_f, c) and tablero[nueva_f][c] == '...':
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, c)}"
                    )

        # Capturas diagonales
        for dc in [-1, 1]:
            nueva_f = f + self.direccion
            nuevo_c = c + dc
            if MovimientosTablero.dentro_tablero(nueva_f, nuevo_c):
                pieza = tablero[nueva_f][nuevo_c]
                if pieza != '...' and pieza[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nuevo_c)}"
                    )

        return movimientos

    def obtener_movimientos_especiales(self, pos_actual: Tuple[int, int],
                                     tablero: NDArray) -> List[MovimientoAjedrez]:
        movimientos = []
        f, c = pos_actual
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        # Verificar promoción
        nueva_f = f + self.direccion
        if MovimientosTablero.dentro_tablero(nueva_f, c):
            if ((self.color == 'B' and nueva_f == 0) or
                (self.color == 'N' and nueva_f == 7)):
                # Promoción en movimiento normal
                if tablero[nueva_f][c] == '...':
                    for pieza in ['Q', 'T', 'A', 'C']:
                        movimientos.append(
                            MovimientoAjedrez(
                                pos_actual_not,
                                MovimientosTablero.posicion_a_notacion(nueva_f, c),
                                TipoMovimiento.PROMOCION,
                                pieza
                            )
                        )

                # Promoción en capturas diagonales
                for dc in [-1, 1]:
                    nuevo_c = c + dc
                    if MovimientosTablero.dentro_tablero(nueva_f, nuevo_c):
                        pieza_destino = tablero[nueva_f][nuevo_c]
                        if pieza_destino != '...' and pieza_destino[0] != self.color:
                            for pieza in ['Q', 'T', 'A', 'C']:
                                movimientos.append(
                                    MovimientoAjedrez(
                                        pos_actual_not,
                                        MovimientosTablero.posicion_a_notacion(nueva_f, nuevo_c),
                                        TipoMovimiento.PROMOCION,
                                        pieza
                                    )
                                )

        # Verificar en passant
        if ((self.color == 'B' and f == 3) or    # Blancas en fila 5
            (self.color == 'N' and f == 4)):     # Negras en fila 4
            
            # Verificar peones enemigos adyacentes
            for dc in [-1, 1]:
                if MovimientosTablero.dentro_tablero(f, c + dc):
                    pieza_id = tablero[f][c + dc]
                    if pieza_id.startswith('BP' if self.color == 'N' else 'NP'):
                        peon_enemigo = self.gestor.get_pieza(pieza_id)
                        if peon_enemigo and peon_enemigo.movimiento_doble_reciente:
                            nueva_f = f + self.direccion
                            movimientos.append(
                                MovimientoAjedrez(
                                    pos_actual_not,
                                    MovimientosTablero.posicion_a_notacion(nueva_f, c + dc),
                                    TipoMovimiento.EN_PASSANT
                                )
                            )

        return movimientos

class Torre(Pieza):
    __slots__ = []
    DIRECCIONES = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # derecha, abajo, izquierda, arriba

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        if f_desde != f_hasta and c_desde != c_hasta:
            return False

        return self._verificar_camino_libre((f_desde, c_desde), (f_hasta, c_hasta), tablero)

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        for df, dc in self.DIRECCIONES:
            nueva_f, nueva_c = f, c
            for _ in range(1, 8):
                nueva_f += df
                nueva_c += dc

                if not MovimientosTablero.dentro_tablero(nueva_f, nueva_c):
                    break

                pieza_destino = tablero[nueva_f][nueva_c]
                if pieza_destino == '...':
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                    continue

                if pieza_destino[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                break

        return movimientos

class Caballo(Pieza):
    __slots__ = []
    MOVIMIENTOS = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        df = abs(f_hasta - f_desde)
        dc = abs(c_hasta - c_desde)
        if not ((df == 2 and dc == 1) or (df == 1 and dc == 2)):
            return False

        pieza_destino = tablero[f_hasta][c_hasta]
        return pieza_destino == '...' or pieza_destino[0] != self.color

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        for df, dc in self.MOVIMIENTOS:
            nueva_f = f + df
            nueva_c = c + dc

            if MovimientosTablero.dentro_tablero(nueva_f, nueva_c):
                pieza_destino = tablero[nueva_f][nueva_c]
                if pieza_destino == '...' or pieza_destino[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )

        return movimientos

class Alfil(Pieza):
    __slots__ = []
    DIRECCIONES = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        if abs(f_hasta - f_desde) != abs(c_hasta - c_desde):
            return False

        return self._verificar_camino_libre((f_desde, c_desde), (f_hasta, c_hasta), tablero)

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        for df, dc in self.DIRECCIONES:
            nueva_f, nueva_c = f, c
            for _ in range(1, 8):
                nueva_f += df
                nueva_c += dc

                if not MovimientosTablero.dentro_tablero(nueva_f, nueva_c):
                    break

                pieza_destino = tablero[nueva_f][nueva_c]
                if pieza_destino == '...':
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                    continue

                if pieza_destino[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                break

        return movimientos
    
class Queen(Pieza):
    """Implementación de la Queen de ajedrez"""
    __slots__ = []
    DIRECCIONES = [
        (0, 1),   # derecha
        (0, -1),  # izquierda
        (1, 0),   # abajo
        (-1, 0),  # arriba
        (1, 1),   # diagonal abajo-derecha
        (1, -1),  # diagonal abajo-izquierda
        (-1, 1),  # diagonal arriba-derecha
        (-1, -1)  # diagonal arriba-izquierda
    ]

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        df = abs(f_hasta - f_desde)
        dc = abs(c_hasta - c_desde)

        # Movimiento en línea recta o diagonal
        if not (df == 0 or dc == 0 or df == dc):
            return False

        return self._verificar_camino_libre((f_desde, c_desde), (f_hasta, c_hasta), tablero)

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        for df, dc in self.DIRECCIONES:
            nueva_f, nueva_c = f, c
            for _ in range(1, 8):
                nueva_f += df
                nueva_c += dc

                if not MovimientosTablero.dentro_tablero(nueva_f, nueva_c):
                    break

                pieza_destino = tablero[nueva_f][nueva_c]
                if pieza_destino == '...':
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                    continue

                if pieza_destino[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )
                break

        return movimientos

class Rey(Pieza):
    __slots__ = []
    DIRECCIONES = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

    def puede_mover(self, desde: str, hasta: str, tablero: NDArray) -> bool:
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(hasta)

        if not MovimientosTablero.dentro_tablero(f_hasta, c_hasta):
            return False

        df = abs(f_hasta - f_desde)
        dc = abs(c_hasta - c_desde)
        if df > 1 or dc > 1:
            return False

        pieza_destino = tablero[f_hasta][c_hasta]
        return pieza_destino == '...' or pieza_destino[0] != self.color

    def obtener_hijos(self, pos_actual: Tuple[int, int], tablero: NDArray) -> List[str]:
        f, c = pos_actual
        movimientos = []
        pos_actual_not = MovimientosTablero.posicion_a_notacion(f, c)

        for df, dc in self.DIRECCIONES:
            nueva_f = f + df
            nueva_c = c + dc

            if MovimientosTablero.dentro_tablero(nueva_f, nueva_c):
                pieza_destino = tablero[nueva_f][nueva_c]
                if pieza_destino == '...' or pieza_destino[0] != self.color:
                    movimientos.append(
                        f"{pos_actual_not} {MovimientosTablero.posicion_a_notacion(nueva_f, nueva_c)}"
                    )

        return movimientos


    def obtener_movimientos_especiales(self, pos_actual: Tuple[int, int],
                                    tablero: NDArray) -> List[MovimientoAjedrez]:
        """Implementa el enroque"""
        if self.movida:  # Si el rey ya se movió, no puede enrocar
            return []

        movimientos = []
        f, c = pos_actual
        

        # Configuración para enroque según color
        if self.color == 'B':
            fila_rey = 7
            torre_corto_id = 'BT2'  # Torre del lado del rey (h1)
            torre_largo_id = 'BT1'  # Torre del lado de la reina (a1)
        else:
            fila_rey = 0
            torre_corto_id = 'NT2'  # Torre del lado del rey (h8)
            torre_largo_id = 'NT1'  # Torre del lado de la reina (a8)

        # Verificar enroque corto
        torre_corta = tablero[fila_rey][7]
        if torre_corta == torre_corto_id:
            torre = self.gestor.get_pieza(torre_corto_id)
            if torre and not torre.movida and self._verificar_enroque(tablero, fila_rey, 4, 7):
                enroque_corto = MovimientoAjedrez(
                    MovimientosTablero.posicion_a_notacion(fila_rey, 4),
                    MovimientosTablero.posicion_a_notacion(fila_rey, 6),
                    TipoMovimiento.ENROQUE,
                    "O-O"
                )
                movimientos.append(enroque_corto)

        # Verificar enroque largo
        torre_larga = tablero[fila_rey][0]
        if torre_larga == torre_largo_id:
            torre = self.gestor.get_pieza(torre_largo_id)
            if torre and not torre.movida and self._verificar_enroque(tablero, fila_rey, 4, 0):
                enroque_largo = MovimientoAjedrez(
                    MovimientosTablero.posicion_a_notacion(fila_rey, 4),
                    MovimientosTablero.posicion_a_notacion(fila_rey, 2),
                    TipoMovimiento.ENROQUE,
                    "O-O-O"
                )
                movimientos.append(enroque_largo)
        return movimientos

    def _verificar_enroque(self, tablero: NDArray, fila: int, 
                          col_inicial: int, col_torre: int) -> bool:
        """Verifica si el camino está libre para el enroque"""
        direccion = 1 if col_torre > col_inicial else -1
        col_actual = col_inicial + direccion
        col_final = col_torre  # Verificar hasta la torre inclusive

        print(f"DEBUG Verificación camino enroque:")
        print(f"- Dirección: {'derecha' if direccion > 0 else 'izquierda'}")
        print(f"- Verificando casillas desde {col_actual} hasta {col_final}")

        while col_actual != col_final:
            if tablero[fila][col_actual] != '...':
                print(f"- Obstáculo encontrado en columna {col_actual}: {tablero[fila][col_actual]}")
                return False
            print(f"- Casilla {col_actual} libre")
            col_actual += direccion

        return True

class GestorPiezas:
    """Gestor centralizado de piezas"""

    def __init__(self):
        self.piezas: Dict[str, Pieza] = {}
        self._inicializar_piezas()

    def registrar_pieza(self, id_pieza: str) -> None:
        """Registra una nueva pieza solo si no existe"""
        if id_pieza in self.piezas:
            return

        color = id_pieza[0]
        tipo = id_pieza[1]
        numero = int(id_pieza[2])

        try:
            if tipo in PIEZAS_FACTORY:
                # Solo registrar si es una pieza válida
                pieza = PIEZAS_FACTORY[tipo](color, numero, self)
                self.piezas[id_pieza] = pieza
                print(f"DEBUG - Pieza {id_pieza} registrada en el gestor")
        except Exception as e:
            print(f"Error registrando pieza {id_pieza}: {str(e)}")


    def _inicializar_piezas(self):
        """Inicializa todas las piezas de ambos colores"""
        print("\nDEBUG: Iniciando inicialización de piezas")

        CONFIGURACION_PIEZAS = {
            'P': 8,  # Peones
            'T': 2,  # Torres
            'C': 2,  # Caballos
            'A': 2,  # Alfiles
            'Q': 1,  # Queen
            'R': 1   # Rey
        }

        for color in ['B', 'N']:
            for tipo, cantidad in CONFIGURACION_PIEZAS.items():
                for num in range(1, cantidad + 1):
                    id_pieza = f"{color}{tipo}{num}"
                    self.registrar_pieza(id_pieza)

        print("\nVerificación final:")
        print(f"Total piezas creadas: {len(self.piezas)}")
        print("Piezas por tipo:")
        for tipo in ['P', 'T', 'C', 'A', 'Q', 'R']:
            piezas_tipo = [p for p in self.piezas.keys() if tipo in p]
            print(f"- Tipo {tipo}: {piezas_tipo}")

    def obtener_movimientos_pieza(self, id_pieza: str, tablero: NDArray) -> List[MovimientoAjedrez]:
        """Obtiene todos los movimientos válidos incluyendo especiales"""
        pieza = self.piezas.get(id_pieza)
        if not pieza:
            self.registrar_pieza(id_pieza)
            pieza = self.piezas.get(id_pieza)
            if not pieza:
                return []

        pos_array = np.where(tablero == id_pieza)
        if len(pos_array[0]) == 0:
            return []

        fila, col = pos_array[0][0], pos_array[1][0]
        
        movimientos = pieza.obtener_movimientos((fila, col), tablero)
        print(f"\nDEBUG - Total movimientos encontrados para {id_pieza}: {len(movimientos)}")
        print("Movimientos:")
        for i, mov in enumerate(movimientos, 1):
            print(f"{i}. {str(mov)}")
        
        return movimientos

    def sincronizar_con_tablero(self, tablero: NDArray) -> None:
        """Sincroniza el diccionario de piezas con el estado actual del tablero"""
        # Recolectar las piezas que están en el tablero
        piezas_en_tablero = set()
        for i in range(8):
            for j in range(8):
                pieza_id = tablero[i][j]
                if pieza_id != '...':
                    piezas_en_tablero.add(pieza_id)
        
        # Eliminar piezas que no están en el tablero
        piezas_a_eliminar = set(self.piezas.keys()) - piezas_en_tablero
        for pieza_id in piezas_a_eliminar:
            print(f"DEBUG - Eliminando pieza {pieza_id} del gestor (no está en el tablero)")
            del self.piezas[pieza_id]

    def ejecutar_movimiento(self, movimiento: MovimientoAjedrez, tablero: NDArray) -> NDArray:
        nuevo_tablero = tablero.copy()
        f_desde, c_desde = MovimientosTablero.notacion_a_posicion(movimiento.desde)
        f_hasta, c_hasta = MovimientosTablero.notacion_a_posicion(movimiento.hasta)
        pieza_id = tablero[f_desde][c_desde]
        pieza = self.get_pieza(pieza_id)

        # Verificar captura en destino
        pieza_destino_id = tablero[f_hasta][c_hasta]
        if pieza_destino_id != '...' and movimiento.tipo != TipoMovimiento.ENROQUE:
            if pieza_destino_id in self.piezas:
                print(f"DEBUG - Eliminando pieza capturada: {pieza_destino_id}")
                del self.piezas[pieza_destino_id]

        # Procesar el movimiento según su tipo
        if movimiento.tipo == TipoMovimiento.PROMOCION:
            color = pieza_id[0]
            tipo = movimiento.info_adicional
            
            # Encontrar siguiente número disponible
            max_num = 0
            for pid in self.piezas.keys():
                if pid.startswith(f"{color}{tipo}"):
                    try:
                        num = int(pid[2])
                        max_num = max(max_num, num)
                    except ValueError:
                        continue
            nuevo_num = max_num+1
            print(f"{nuevo_num} ESTO ES LO QUE GUARDAAAAAAAAAAAAAA")
            nuevo_id = f"{color}{tipo}{nuevo_num}"
            
            # Eliminar peón que promueve
            if pieza_id in self.piezas:
                print(f"DEBUG - Eliminando peón que promueve: {pieza_id}")
                del self.piezas[pieza_id]
            
            # Crear y registrar nueva pieza
            nueva_pieza = PIEZAS_FACTORY[tipo](color, nuevo_num, self)
            self.piezas[nuevo_id] = nueva_pieza
            
            # Actualizar tablero
            nuevo_tablero[f_desde][c_desde] = '...'
            nuevo_tablero[f_hasta][c_hasta] = nuevo_id
            print(f"Pieza promovida: {pieza_id} -> {nuevo_id}")

        elif movimiento.tipo == TipoMovimiento.ENROQUE:
            # [código del enroque igual que antes]
            pass
        else:
            # Movimiento normal
            nuevo_tablero[f_hasta][c_hasta] = pieza_id
            nuevo_tablero[f_desde][c_desde] = '...'
            
            if isinstance(pieza, Peon):
                pieza.movimiento_doble_reciente = (abs(f_hasta - f_desde) == 2)
            pieza.movida = True

        # Sincronizar con el nuevo estado del tablero
        self.sincronizar_con_tablero(nuevo_tablero)
        return nuevo_tablero

    def get_pieza(self, id_pieza: str) -> Optional[Pieza]:
        """Obtiene una pieza por su identificador sin crear nuevas"""
        return self.piezas.get(id_pieza)


# Definición del factory de piezas
PIEZAS_FACTORY = {
    'P': Peon,
    'T': Torre,
    'C': Caballo,
    'A': Alfil,
    'Q': Queen,
    'R': Rey
}

# Funciones de utilidad
def imprimir_tablero(tablero):
    """Imprime el tablero con índices de filas y columnas"""
    print("\nTablero de prueba:")
    print("     ", end="")
    for col in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        print(f"{col:^5}", end="")
    print("\n     " + "─" * 40)

    for i in range(8):
        print(f" {8-i} │ ", end="")
        for j in range(8):
            print(f"{tablero[i][j]:4}", end=" ")
        print(f"│ {8-i}")

    print("     " + "─" * 40)
    print("     ", end="")
    for col in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']:
        print(f"{col:^5}", end="")
    print("\n")

if __name__ == "__main__":
    gestor = GestorPiezas()

    # Test de promoción
    print("\n=== Test de Promoción ===")
    tablero = np.full((8, 8), '...', dtype='<U4')

    # Configuración para promoción
    tablero[1][0] = 'BP1'  # Peón blanco en a7 (a punto de promocionar)
    tablero[0][4] = 'NR1'  # Rey negro
    tablero[7][4] = 'BR1'  # Rey blanco
    #tablero[5][1] = 'BQ1'  # Rey blanco
    print("\nTablero inicial para prueba de promoción:")
    imprimir_tablero(tablero)

    # Mostrar movimientos posibles del peón
    print("\nMovimientos disponibles para BP1:")
    movimientos = gestor.obtener_movimientos_pieza('BP1', tablero)
    print("Movimientos encontrados:")
    for i, mov in enumerate(movimientos, 1):
        print(f"{i}. {str(mov)}")

    # Realizar promoción
    print("\nEjecutando promoción a reina...")
    mov = MovimientoAjedrez('a7', 'a8', TipoMovimiento.PROMOCION, 'T')
    tablero = gestor.ejecutar_movimiento(mov, tablero)
    print("\nTablero después de promoción:")
    imprimir_tablero(tablero)

    # Verificar nueva reina
    print("\nBuscando nueva reina BQ2:")
    nueva_reina = gestor.get_pieza('BQ2')
    if nueva_reina:
        print("- Nueva reina encontrada en el gestor")
        pos = np.where(tablero == 'BQ2')
        if len(pos[0]) > 0:
            print(f"- Posición en tablero: {MovimientosTablero.posicion_a_notacion(pos[0][0], pos[1][0])}")
            print("\nMovimientos disponibles para la nueva reina:")
            movimientos = gestor.obtener_movimientos_pieza('BQ2', tablero)
            for i, mov in enumerate(movimientos, 1):
                print(f"{i}. {str(mov)}")
        else:
            print("- ERROR: Nueva reina no encontrada en el tablero")
    else:
        print("- ERROR: Nueva reina no encontrada en el gestor")

    # Test de enroque
    print("\n=== Test de Enroque ===")
    tablero_enroque = np.full((8, 8), '...', dtype='<U4')

    # Configuración inicial para enroque
    tablero_enroque[7][4] = 'BR1'  # Rey blanco en e1
    tablero_enroque[7][7] = 'BT2'  # Torre blanca en h1
    tablero_enroque[7][0] = 'BT1'  # Torre blanca en a1
    tablero_enroque[0][4] = 'NR1'  # Rey negro en e8
    tablero_enroque[0][7] = 'NT2'  # Torre negra en h8
    tablero_enroque[0][0] = 'NT1'  # Torre negra en a8

    print("\nTablero inicial para prueba de enroque:")
    imprimir_tablero(tablero_enroque)

    # Mostrar movimientos posibles del rey blanco (incluyendo enroque)
    print("\nMovimientos disponibles para BR1 (incluyendo enroque):")
    movimientos = gestor.obtener_movimientos_pieza('BR1', tablero_enroque)
    print("Movimientos encontrados:")
    for i, mov in enumerate(movimientos, 1):
        print(f"{i}. {str(mov)}")

    # Realizar enroque corto
    print("\nEjecutando enroque corto...")
    mov_enroque = MovimientoAjedrez('e1', 'g1', TipoMovimiento.ENROQUE, 'O-O')
    tablero_enroque = gestor.ejecutar_movimiento(mov_enroque, tablero_enroque)
    print("\nTablero después de enroque corto:")
    imprimir_tablero(tablero_enroque)

    # Verificar que el rey y la torre se movieron
    rey_blanco = gestor.get_pieza('BR1')
    torre_blanca = gestor.get_pieza('BT2')
    if rey_blanco.movida and torre_blanca.movida:
        print("- Enroque ejecutado correctamente: rey y torre marcados como movidos")
    else:
        print("- ERROR: Estado de movimiento del rey o torre incorrecto")

    # Verificar que ya no se puede hacer enroque
    print("\nVerificando que no hay más enroques disponibles:")
    movimientos = gestor.obtener_movimientos_pieza('BR1', tablero_enroque)
    enroques = [mov for mov in movimientos if mov.tipo == TipoMovimiento.ENROQUE]
    if not enroques:
        print("- Correcto: No hay más enroques disponibles")
    else:
        print("- ERROR: Todavía hay enroques disponibles")

    # Estado final del gestor
    print("\nEstado del gestor:")
    print(f"Total piezas: {len(gestor.piezas)}")
