from dataclasses import dataclass, field

@dataclass
class HardwareGraph:
    nodes: tuple
    edges: tuple
    gate_durations: dict = field(default_factory=dict)
    error_rates: dict = field(default_factory=dict)
    def __post_init__(self):
        if len(set(self.nodes))!=len(self.nodes): raise ValueError('Duplicate nodes')
        if any(a==b or a not in self.nodes or b not in self.nodes for a,b in self.edges): raise ValueError('Invalid edge')
        if any(v<=0 for v in self.gate_durations.values()): raise ValueError('Invalid duration')
        if any(not 0<=v<=1 for v in self.error_rates.values()): raise ValueError('Invalid error rate')
    def allows(self,a,b): return (a,b) in self.edges or (b,a) in self.edges
