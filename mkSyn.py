from machine import Pin, ADC
import rp2
from time import sleep, ticks_ms
from math import sin, cos, floor, pi, pow
import random
from typing import List, Tuple, Callable

class Transport:

    def __init__(self, k :float = 0):
        self.clock : float = ticks_ms() / 1000.0

    def tick(self):
        self.clock = ticks_ms() / 1000.0

class Signal():

    def __init__(self, k):
        if not isinstance(k, Oscilator):
            raise NotImplementedError
        self.val = k.get()
    
    def __add__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val + other.get()
        return self

    def __radd__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = other.get() + self.val
        return self
    
    def __sub__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val - other.get()
        return self

    def __rsub__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = other.get() - self.val
        return self

    def __mul__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val * other.get()
        return self

    def __rmul__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = other.get() * self.val
        return self
    
    def __div__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val / other.get()
        return self

    def __rdiv__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = other.get() / self.val
        return self

    def __iadd__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val + other.get()
        return self

    def __isub__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val - other.get()
        return self

    def __imul__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val * other.get()
        return self
  
    def __idiv__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.val = self.val / other.get()
        return self

    def __str__(self):
        return str(self.val)

class Oscilator:

    def __init__(
            self, *, 
            amplitude : float = 1.0, 
            frequency : float = 0.0,
            value     : float = 0.0
        ):
        self.amp : float = amplitude
        self.frq : float = 0.0
        self.val : float = value
        self.set_freq_by_hertz(frequency)

    def get(self) -> float:
        global tp
        if self.frq != 0:
            self.val = self.generator(tp.clock)
        return self.val * self.amp

    def set_freq_by_hertz(self, f : float):
        self.frq = self.from_hertz(f)
        
    def generator(self, x : float) -> float:
        return self.val

    def assign_generator(self, fn : Callable[[int], float]):
        self.generator = fn

    def from_hertz(self, h : float) -> float:
        if h == 0:
            return 0.0
        period : float =  1.0 / h 
        return period

    def freq_mod(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.frq = other.get()

    def __eq__(self, other):
        if not isinstance(other, Oscilator):
            return false
        return self.get() == other.get()

    def __add__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.amp + other.get()

    def __radd__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        other.amp + self.get()

    def __iadd__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.amp + other.get()

    def __mul__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.amp * other.get()

    def __rmul__(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        other.amp * self.get()

    def __imul(self, other):
        if not isinstance(other, Oscilator):
            raise NotImplementedError
        self.amp = other.get()        
        
class SineWave(Oscilator):

    def generator(self, x : float) -> float:
        b = (2 * pi * x) / self.frq
        return sin(b)

class SawWave(Oscilator):

    def generator(self, x : float) -> float:
        b : float = float(x) / self.frq
        c : float = floor((1/2) + b)
        return 2 * (b - c)

class SquareWave(Oscilator):

    def generator(self, x : float) -> float:
        return pow(-1, floor(2 * self.frq * x))

class TriWave(Oscilator):

    def generator(self, x : float) -> float:
        b : float = float(x) / self.frq
        c = floor((1/2) + b)
        d = abs(2 * (b - c))
        return 2 * d - 1

class WhiteNoise(Oscilator):

    def generator(self, x : float) -> float:
        return random.uniform(-1.0, 1.0)

class GaussNoise(Oscilator):

    def generator(self, x : float) -> float:
        return random.gauss(-1.0, 1.0)

class DAC:

    pio_config = {
        "out_init": [rp2.PIO.OUT_HIGH] * 10, 
        "out_shiftdir": rp2.PIO.SHIFT_RIGHT,
        "autopull": True,
        "pull_thresh": 10
    }
    
    def __init__(self, pins : List[int]):
        self.pins : Tuple[Pins] = tuple([Pin(p, Pin.OUT) for p in pins])
        self.sm = rp2.StateMachine(0, self.update_DAC, freq=16384, out_base=Pin(6))
        self.sm.active(1)

    @rp2.asm_pio(**pio_config)
    def update_DAC():
        out(pins, 10) # punch x register onto all pins instantaneously

    def punch(self, output : int):
        output = int(output) # no daughter of mine will date a filthy non-int
        output &= int(0x3FF) # chop to LSB 10bits
        self.sm.put(output)

    def punch_signal(self, sig : Signal):
        if not isinstance(sig, Signal):
            raise NotImplementedError
        output = (sig.val + 1) / 2 * (2**10 - 1)
        self.punch(output)

    def __str__(self):
        ink = ""
        for pin in self.pins:
            ink = str(pin.value()) + ink
        return  ink

class Pot:
    
    def __init__(self, p : int):
        self.pin = Pin(p)
        self.adc = ADC(self.pin)

    def read(self) -> float: # 0-1
        val = self.adc.read_u16()
        return val / 65535.0

class VCC_Monitor:

    def __init__(self, p : int):
        self.pin = Pin(p)
        self.adc = ADC(self.pin)
        
    def read(self):
        val = self.adc.read_u16()
        val = val / 65535.0
        print(f"dac - {val}")

# Monitor the r2Ladder Output
# vcc_mon = VCC_Monitor(28)

# Manip values with pots
north_pot = Pot(27)
south_pot = Pot(26)

# the global transport
tp = Transport()

# the makerverse r2 ladder
dac = DAC(list(range(6, 16)))

# oscilators
cycle = SineWave(amplitude=1, frequency=2)
saw = SawWave(amplitude=0.35, frequency=120)
saw2 = SawWave(amplitude=0.1, frequency=480)
sqr = SquareWave(amplitude=0.5, frequency=512)

while 1:
    sig = Signal(cycle)
    dac.punch_signal(sig)
    tp.tick()
