"""Permanent development ladder; repetition channels are explicitly not quantum-distance evidence."""
from pathlib import Path
from dataclasses import replace
import json,time,ctypes,gzip
from ftqec.codes.stabilizer import StabilizerCode
from ftqec.architectures.generators import generate
from ftqec.circuits.memory import MemoryConfig
from ftqec.resource_synthesis.design import Design
from ftqec.resource_synthesis.circuits import build_design,validate_ideal
from ftqec.resource_synthesis.certification import SignatureCache
from ftqec.faults.search import search_faults
from ftqec.certification_v5.exact import certify
from ftqec.certification_v5.independent import exclusion

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'results/v0.5'


def shor(size):
    n=size*size; g=[]
    for block in range(size):
        for j in range(size-1):
            s=['I']*n;s[block*size+j]=s[block*size+j+1]='Z';g.append(''.join(s))
    for block in range(size-1):
        s=['I']*n
        for q in range(block*size,(block+2)*size):s[q]='X'
        g.append(''.join(s))
    return StabilizerCode.from_dict(dict(n=n,generators=g,name=f'shor_{size}x{size}_development'))


def peak_memory():
    if not hasattr(ctypes,'windll'):return None
    class Counters(ctypes.Structure):
        _fields_=[('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)]+[(name,ctypes.c_size_t) for name in
            ('PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage',
             'QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    c=Counters();c.cb=ctypes.sizeof(c)
    kernel=ctypes.windll.kernel32; kernel.GetCurrentProcess.restype=ctypes.c_void_p
    ps=ctypes.windll.psapi.GetProcessMemoryInfo
    ps.argtypes=[ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    return c.PeakWorkingSetSize if ps(kernel.GetCurrentProcess(),ctypes.byref(c),c.cb) else None


def main():
    cases=[]
    for n in (3,5,7):
        g=['I'*i+'ZZ'+'I'*(n-i-2) for i in range(n-1)]
        cases.append((f'repetition-channel-{n}',StabilizerCode.from_dict(dict(n=n,generators=g)),n,
                      'classical observable proxy; quantum code distance 1; excluded from readiness'))
    for size in (5,7):
        cases.append((f'shor-{size}x{size}',shor(size),size,
                      'standard concatenated repetition stabilizer construction, quantum distance '+str(size)))
    results=[]
    for name,code,target,provenance in cases:
        d=Design(next(iter(generate(code,1,10))),family='verified_cat'); memory=MemoryConfig(rounds=3,basis='Z')
        t=time.perf_counter();c=build_design(code,d,memory);ideal=validate_ideal(c)
        ss,_=SignatureCache().get(c);signature_seconds=time.perf_counter()-t
        b=certify(c,ss,target,1048576,250000)
        independent=exclusion(c,min(target-1,b['lower_bound']-1),250000,2000000)
        t=time.perf_counter();naive=search_faults(c,ss,min(target-1,6),8192);naive_seconds=time.perf_counter()-t
        record=dict(name=name,permanent_development=True,provenance=provenance,code=code.to_dict(),
                    design=d.to_dict(),memory=memory.__dict__,circuit=c.to_dict(),ideal=ideal,target=target,
                    signature_seconds=signature_seconds,bounds=b,independent=independent,naive=naive,
                    naive_seconds=naive_seconds,process_peak_working_set_bytes=peak_memory(),
                    readiness_eligible=name.startswith('shor') and b['lower_bound']>=target and independent['verified'])
        results.append(record);print(name,'types',b['signature_types'],'bounds',b['lower_bound'],b['upper_bound'],
              'independent',independent['verified'],'reason',b['reason'],flush=True)
        (OUT/'ladder.json.gz').write_bytes(gzip.compress(json.dumps(results,indent=2).encode(),mtime=0))


if __name__=='__main__':main()
