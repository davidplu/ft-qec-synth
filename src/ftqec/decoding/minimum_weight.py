from itertools import combinations


class BoundedMinimumWeightDecoder:
    """Deterministic detector-to-logical recovery table through complete layers.

    Ties select the numerically smallest logical effect. No prediction is made
    for signatures whose minimum weight has not been established.
    """
    def __init__(self):
        self.table = {0: (0, 0)}
        self.completed_through = 0
        self.work = 0

    def fit(self, signatures, max_weight=1, max_combinations=100000):
        self.table = {0: (0, 0)}; self.completed_through = 0; self.work = 0
        for weight in range(1, max_weight+1):
            for indices in combinations(range(len(signatures)), weight):
                if self.work >= max_combinations: return self
                self.work += 1
                group = [signatures[i] for i in indices]
                if len({s.fault.location for s in group}) != weight: continue
                d = l = 0
                for s in group: d ^= s.detectors; l ^= s.logical
                old = self.table.get(d)
                if old is None or (weight, l) < old: self.table[d] = (weight, l)
            self.completed_through = weight
        return self

    def predict_logical(self, detectors):
        entry = self.table.get(detectors)
        if entry is None or entry[0] > self.completed_through: return None
        return entry[1]


def decoder_failures(signatures, decoder, max_weight=1, max_combinations=100000):
    resolved = failures = examined = 0; witnesses = []; completed = 0
    for weight in range(1, max_weight+1):
        for indices in combinations(range(len(signatures)), weight):
            if examined >= max_combinations:
                return dict(resolved=resolved, failures=failures, examined=examined,
                            completed_through=completed, reason='work_limit', witnesses=witnesses)
            examined += 1; group = [signatures[i] for i in indices]
            if len({s.fault.location for s in group}) != weight: continue
            d = l = 0
            for s in group: d ^= s.detectors; l ^= s.logical
            predicted = decoder.predict_logical(d)
            if predicted is None: continue
            resolved += 1
            if predicted != l:
                failures += 1
                if len(witnesses) < 8:
                    witnesses.append(dict(faults=[s.fault.to_dict() for s in group],
                                          detector_signature=d, actual_logical=l, recovery_logical=predicted,
                                          residual_logical=l ^ predicted))
        completed = weight
    return dict(resolved=resolved, failures=failures, examined=examined,
                completed_through=completed, reason=None, witnesses=witnesses)
