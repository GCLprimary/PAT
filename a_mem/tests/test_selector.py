"""Probe 9 / K1: selector classification capacity. Baselines: 100% at
k = 3, ~90% at k = 8 (assert >= 85%), ~79% at k = 12 (assert >= 70%)."""
from amem import cosine


def accuracy(names, lib, probes):
    correct = total = 0
    for name in names:
        for probe_sig in probes[name]:
            pick = max(names, key=lambda n: cosine(probe_sig, lib[n]["sig"]))
            correct += int(pick == name)
            total += 1
    return correct / total


def test_classification_k3(twelve_bank):
    names, lib, probes = twelve_bank
    assert accuracy(names[:3], lib, probes) == 1.0


def test_classification_k8(twelve_bank):
    names, lib, probes = twelve_bank
    acc = accuracy(names[:8], lib, probes)
    assert acc >= 0.85, f"k=8 accuracy {acc:.2f} < 0.85"


def test_classification_k12(twelve_bank):
    names, lib, probes = twelve_bank
    acc = accuracy(names, lib, probes)
    assert acc >= 0.70, f"k=12 accuracy {acc:.2f} < 0.70"
