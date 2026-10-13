import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable


class JanelaDeslizante:
    def __init__(self, limite: int, janela: float = 60.0, relogio: Callable[[], float] = time.monotonic) -> None:
        self.limite = limite
        self.janela = janela
        self._relogio = relogio
        self._chamadas: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def registrar(self, chave: str) -> int | None:
        with self._trava:
            agora = self._relogio()
            chamadas = self._chamadas[chave]
            while chamadas and chamadas[0] <= agora - self.janela:
                chamadas.popleft()
            if len(chamadas) >= self.limite:
                return max(1, math.ceil(chamadas[0] + self.janela - agora))
            chamadas.append(agora)
            return None
