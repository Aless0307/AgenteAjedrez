from typing import Dict, List, Set, Tuple, Optional
import numpy as np
from piezas import GestorPiezas, MovimientosTablero, MovimientoAjedrez, TipoMovimiento

# hoal tilin
class AgenteAjedrez:
    # Constantes para piezas
    VACIO = '...'

    # Piezas blancas
    PEON_B = 'BP'
    CABALLO_B = 'BC'
    ALFIL_B = 'BA'
    TORRE_B = 'BT'
    REINA_B = 'BQ'
    REY_B = 'BR'

    # Piezas negras
    PEON_N = 'NP'
    CABALLO_N = 'NC'
    ALFIL_N = 'NA'
    TORRE_N = 'NT'
    REINA_N = 'NQ'
    REY_N = 'NR'

    # Valores absolutos de las piezas
    VALORES_PIEZAS = {
        PEON_B: 100,
        PEON_N: 100,
        CABALLO_B: 320,
        CABALLO_N: 320,
        ALFIL_B: 330,
        ALFIL_N: 330,
        TORRE_B: 500,
        TORRE_N: 500,
        REINA_B: 900,
        REINA_N: 900,
        REY_B: 20000,
        REY_N: 20000
    }

    COLUMNAS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    def __init__(self,
                color: str = 'blancas',
                estado=None,
                padre=None,
                max_profundidad: int = 4):
        """
        Inicializa el agente de ajedrez
        Args:
            color: 'blancas' o 'negras'
            estado: estado inicial del tablero (None para estado inicial)
            padre: nodo padre para árbol de búsqueda
            max_profundidad: profundidad máxima de búsqueda
        """
        self.color = 1 if color == 'blancas' else -1
        self.max_profundidad = max_profundidad
        self.visitados = set()
        self.padre = padre
        self.hijos = []

        # Inicializar gestor de piezas
        self.gestor_piezas = GestorPiezas()

        # Estado del tablero
        if estado is None:
            self.estado = np.full((8, 8), self.VACIO, dtype='<U4')

            # Piezas traseras blancas
            piezas_blancas = [
                (self.TORRE_B, 1), (self.CABALLO_B, 1),
                (self.ALFIL_B, 1), (self.REINA_B, 1), (self.REY_B, 1),
                (self.ALFIL_B, 2), (self.CABALLO_B, 2), (self.TORRE_B, 2)
            ]

            # Piezas traseras negras
            piezas_negras = [
                (self.TORRE_N, 1), (self.CABALLO_N, 1),
                (self.ALFIL_N, 1), (self.REINA_N, 1), (self.REY_N, 1),
                (self.ALFIL_N, 2), (self.CABALLO_N, 2), (self.TORRE_N, 2)
            ]

            # Colocar piezas blancas
            self.estado[7] = [f"{pieza}{num}" for pieza, num in piezas_blancas]
            self.estado[6] = [f"{self.PEON_B}{i+1}" for i in range(8)]

            # Colocar piezas negras
            self.estado[1] = [f"{self.PEON_N}{i+1}" for i in range(8)]
            self.estado[0] = [f"{pieza}{num}" for pieza, num in piezas_negras]
        else:
            self.estado = estado.copy()  # Asegurarse de hacer una copia

        self.visitados.add(tuple(map(tuple, self.estado)))

    def mover(self, cadena: str, promocion_pieza: str = 'Q') -> bool:
        """
        Realiza un movimiento en el tablero usando el gestor de piezas
        """
        if promocion_pieza == 'P' or promocion_pieza == 'R':
          print("No puedes hacer promoción a un Rey u otro peón")
          return
        # Manejar notación de enroque
        if cadena == "O-O" or cadena == "O-O-O":
            fila = 7 if self.color == 1 else 0
            desde = f"e{8-fila}"
            hasta = "g" + desde[1] if cadena == "O-O" else "c" + desde[1]
            movimiento = MovimientoAjedrez(desde, hasta, TipoMovimiento.ENROQUE, cadena)
        else:
            # Movimiento normal
            desde = cadena[0] + cadena[1]
            hasta = cadena[3] + cadena[4]
            
            f_desde, c_desde = MovimientosTablero.notacion_a_posicion(desde)
            id_pieza = self.estado[f_desde][c_desde]
            
            if id_pieza == self.VACIO:
                print(f"No hay pieza en {desde}")
                return False

            # Verificar color
            es_pieza_blanca = id_pieza.startswith('B')
            if (self.color == 1 and not es_pieza_blanca) or (self.color == -1 and es_pieza_blanca):
                print("No puedes mover las piezas del oponente")
                return False

            # Determinar tipo de movimiento
            if id_pieza[1] == 'P' and (hasta[1] == '8' or hasta[1] == '1'):
                movimiento = MovimientoAjedrez(desde, hasta, TipoMovimiento.PROMOCION, promocion_pieza)
            else:
                movimiento = MovimientoAjedrez(desde, hasta, TipoMovimiento.NORMAL, None)

        # Ejecutar el movimiento a través del gestor
        nuevo_estado = self.gestor_piezas.ejecutar_movimiento(movimiento, self.estado)
        if nuevo_estado is None:
            print("Movimiento inválido")
            return False

        # Actualizar estado
        self.estado = nuevo_estado.copy()
        self.visitados.add(tuple(map(tuple, self.estado)))
        self.verificar_consistencia()
        return True
    
    def obtener_movimientos_posibles(self, identificador: str) -> List[MovimientoAjedrez]:
        """
        Obtiene todos los movimientos válidos para una pieza
        Args:
            identificador: ID de la pieza (ej: 'BP1', 'NR1')
        Returns:
            List[MovimientoAjedrez]: Lista de movimientos válidos
        """
        print(f"Depuración - Buscando movimientos para: {identificador}")

        # Verificar que la pieza existe
        pos = self.obtener_posicion_pieza(identificador)
        print(f"Depuración - Posición encontrada: {pos}")

        if pos is None:
            print("Depuración - No se encontró la posición")
            return []

        # Verificar que la pieza está en el gestor
        pieza = self.gestor_piezas.get_pieza(identificador)
        print(f"Depuración - Pieza en gestor: {pieza is not None}")

        if not pieza:
            print("Depuración - Pieza no encontrada en el gestor")
            return []

        # Obtener movimientos
        movimientos = self.gestor_piezas.obtener_movimientos_pieza(identificador, self.estado)
        if movimientos:
            print("Depuración - Movimientos encontrados")
        else:
            print(f"No se encontraron movimientos para {identificador}")
        return movimientos

    def evaluar_material(self) -> int:
        """
        Evalúa el material actual en el tablero
        Returns:
            int: valor positivo favorece al color del agente
        """
        valor = 0
        for pieza, valor_base in self.VALORES_PIEZAS.items():
            count = np.sum(np.char.startswith(self.estado, pieza[:2]))
            # Ajustar valor según el color del agente
            if (pieza.startswith('B') and self.color == 1) or \
               (pieza.startswith('N') and self.color == -1):
                valor += int(count * valor_base)
            else:
                valor -= int(count * valor_base)
        return valor

    def obtener_posicion_pieza(self, identificador: str) -> Optional[Tuple[int, int]]:
        """
        Obtiene la posición actual de una pieza específica
        """
        pos = np.where(self.estado == identificador)
        if pos[0].size > 0:
            print(f"\nDEBUG - Pieza {identificador} encontrada en tablero: ({pos[0][0]}, {pos[1][0]})")
            return (pos[0][0], pos[1][0])
        print(f"\nDEBUG - Pieza {identificador} no encontrada en tablero")
        return None

    def obtener_piezas_por_tipo(self, color: str, tipo: str) -> List[Tuple[str, Tuple[int, int]]]:
        """
        Retorna lista de tuplas (identificador, posición) de todas las piezas de un color y tipo
        """
        print(f"\nDEBUG - Buscando piezas de tipo {color}{tipo}")
        piezas = []
        for i in range(8):
            for j in range(8):
                id_pieza = self.estado[i][j]
                if id_pieza != '...' and id_pieza.startswith(f"{color}{tipo}"):
                    print(f"- Encontrada pieza {id_pieza} en ({i}, {j})")
                    piezas.append((id_pieza, (i, j)))
        
        print(f"- Total piezas encontradas: {len(piezas)}")
        return piezas


    def esta_pieza_en_juego(self, identificador: str) -> bool:
        """
        Verifica si una pieza específica sigue en el tablero
        """
        return self.obtener_posicion_pieza(identificador) is not None

    def contar_piezas_por_tipo(self, color: str, tipo: str) -> int:
        """
        Cuenta cuántas piezas de un tipo específico quedan
        """
        codigo_busqueda = f"{color}{tipo}"
        return np.sum(np.char.startswith(self.estado, codigo_busqueda).astype(int))

    def contar_piezas_color(self, color: str) -> int:
        """
        Cuenta todas las piezas de un color específico
        """
        return np.sum(np.char.startswith(self.estado, color).astype(int))

    def __str__(self) -> str:
        """Representación visual del tablero"""
        resultado = "    "
        for col in self.COLUMNAS:
            resultado += f"{col:^5}"
        resultado += "\n"

        for i in range(8):
            resultado += f"{8-i:<3}"
            for j in range(8):
                pieza = self.estado[i][j]
                if pieza == self.VACIO:
                    resultado += f"{'...':^5}"
                else:
                    resultado += f"{pieza:^5}"
            resultado += f" {8-i}\n\n"

        resultado += "    "
        for col in self.COLUMNAS:
            resultado += f"{col:^5}"

        return resultado
    
    def verificar_consistencia(self) -> bool:
      """Verifica que las piezas en el diccionario coinciden con las del tablero"""
      piezas_tablero = set()
      for i in range(8):
          for j in range(8):
              pieza = self.estado[i][j]
              if pieza != '...':
                  piezas_tablero.add(pieza)
      
      piezas_gestor = set(self.gestor_piezas.piezas.keys())
      
      if piezas_tablero != piezas_gestor:
          print("\nInconsistencia detectada:")
          print(f"Solo en tablero: {piezas_tablero - piezas_gestor}")
          print(f"Solo en gestor: {piezas_gestor - piezas_tablero}")
          return False
      return True


def crear_estado_prueba():
    """
    Crea un estado de prueba donde la mayoría de las piezas pueden moverse.
    """
    estado = np.full((8, 8), '...', dtype='<U4')

    # Piezas blancas
    estado[7] = ['BT1', 'BC1', '...', 'BQ1', 'BR1', '...', 'BC2', 'BT2']
    estado[6] = ['BP1', '...', 'BP3', '...', '...', 'BP6', '...', 'BP8']
    estado[5] = ['...', 'BP2', '...', 'BP4', '...', '...', 'BP7', '...']
    estado[4] = ['...', '...', 'BA1', '...', 'BP5', '...', '...', '...']

    # Piezas negras
    estado[0] = ['NT1', 'NC1', '...', 'NQ1', 'NR1', '...', 'NC2', 'NT2']
    estado[1] = ['NP1', '...', 'NP3', '...', 'NP5', 'NP6', 'NP7', 'NP8']
    estado[3] = ['...', 'NP2', '...', 'NP4', '...', '...', '...', '...']

    return estado


def crear_tablero_prueba_especial():
    """
    Crea un tablero con posiciones para probar promoción
    """
    estado = np.full((8, 8), '...', dtype='<U4')

    # Peones blancos
    estado[1][0] = 'BP1'  # Peón blanco en a7 (a punto de promocionar)
    estado[3][3] = 'BP2'  # Otro peón en d5

    # Piezas negras
    estado[0][4] = 'NR1'  # Rey negro
    estado[1][2] = 'NP2'  # Peón negro en c7
    estado[1][4] = 'NP1'  # Peón negro en e7

    # Piezas blancas
    estado[7][4] = 'BR1'  # Rey blanco
    estado[7][3] = 'BQ1'  # Reina blanca

    return estado


def crear_tablero_inicial():
    """
    Crea el tablero de ajedrez organizado en su estado inicial.
    Devuelve un arreglo de numpy con las piezas en sus posiciones iniciales.
    """
    estado = np.full((8, 8), '...', dtype='<U4')

    # Piezas blancas
    estado[7] = ['BT1', 'BC1', 'BA1', 'BQ1', 'BR1', 'BA2', 'BC2', 'BT2']
    estado[6] = [f"BP{i+1}" for i in range(8)]

    # Piezas negras
    estado[0] = ['NT1', 'NC1', 'NA1', 'NQ1', 'NR1', 'NA2', 'NC2', 'NT2']
    estado[1] = [f"NP{i+1}" for i in range(8)]

    return estado

def mostrar_diccionario_piezas(gestor, mensaje="Estado actual del diccionario:"):
    print(f"\n{mensaje}")
    print("Piezas Blancas:")
    for color in ['B']:
        for tipo in ['P', 'T', 'C', 'A', 'Q', 'R']:
            piezas = [pid for pid in gestor.piezas.keys() if pid.startswith(f"{color}{tipo}")]
            if piezas:
                print(f"- {tipo}: {sorted(piezas)}")

if __name__ == "__main__":
    # Test de movimientos básicos y capturas
    print("\n=== Test de Movimientos y Capturas ===")
    agente = AgenteAjedrez(color='blancas')
    agente2 = AgenteAjedrez(color='negras')
    
    print("Estado inicial del tablero:")
    print(agente)
    
    # Secuencia de movimientos para probar diferentes aspectos
    movimientos = [
        # Abrir camino para las piezas
        ("e2-e4", "blancas"),  # Peón blanco
        ("e7-e5", "negras"),   # Peón negro
        ("g1-f3", "blancas"),  # Caballo blanco
        ("b8-c6", "negras"),   # Caballo negro
        ("f1-c4", "blancas"),  # Alfil blanco
        ("f8-c5", "negras"),   # Alfil negro
        
        # Probar captura
        ("f3-e5", "blancas"),  # Caballo blanco captura peón
        ("d7-d6", "negras"),   # Peón negro amenaza caballo
        ("e5-f7", "blancas"),  # Caballo blanco captura peón
        
        # Preparar enroque (mover piezas del camino)
        ("g2-g3", "blancas"),
        ("g8-f6", "negras"),
        ("f2-f3", "blancas"),
        ("f6-e4", "negras"),
    ]

    # Ejecutar secuencia de movimientos
    for movimiento, color in movimientos:
        print(f"\nMoviendo {color}: {movimiento}")
        if color == "blancas":
            agente.mover(movimiento)
            agente2.estado = agente.estado
        else:
            agente2.mover(movimiento)
            agente.estado = agente2.estado
        print(agente)
        
    # Probar enroque corto
    print("\n=== Probando Enroque Corto ===")
    print("\nMovimientos disponibles para rey blanco:")
    agente.obtener_movimientos_posibles("BR1")
    agente.mover("d2-d4")
    agente.mover("c2-c3")
    agente.mover("b2-b2")
    agente.mover("a2-a4")
    agente.mover("b1-d2")
    agente.mover("c1-a3")
    agente.mover("d1-b3")
    agente.obtener_movimientos_posibles("BR1")
    agente.mover("O-O-O")
    agente.mover("f7-h6")
    agente.mover("f3-f4")
    agente.mover("f4-f5")
    agente.mover("f5-f6")
    agente.mover("f6-f7")
    agente.mover("b3-b4")
    agente2.estado = agente.estado
    agente2.mover("c5-b4")
    agente.estado = agente2.estado
    agente.mover("f7-f8","P")
    print(agente)
