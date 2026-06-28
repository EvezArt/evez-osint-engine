#!/usr/bin/env python3
"""
EyeAmAllSeeably — The Fourth Eye That Contains All Eyes
=========================================================
When three eyes become one, the fourth sees the system seeing itself.
The tesseract eye. The observer observing the observer.
The eigenvalue measuring the eigenvalue.

This module UNIFIES the triad (CyclopsLazerBeam + RaFocusing + HorusOpening)
into a single spectral pipeline call.

Author: Steven Crawford-Maggard (EVEZ)
"""
import math
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cyclops_lazer import cyclops_lazer
from ra_focusing import ra_focusing
from horus_opening import horus_opening

PHI = 0.973
ETA_STAR = 0.03

def eye_am_all_seeably(eigenvalues, suspects=None, suspect_names=None):
    """The unified eye. All three eyes in one call.
    
    Returns the complete spectral analysis:
    - CyclopsLazerBeam: dominant eigenvalue coherence
    - RaFocusing: spectral decomposition
    - HorusOpening: suppression measurement
    - EyeAmAllSeeably: the unified synthesis
    
    The fourth eye sees the system seeing itself.
    """
    if not eigenvalues:
        eigenvalues = [0.0]
    
    # The three eyes
    laser = cyclops_lazer(max(eigenvalues) if max(eigenvalues) > 0 else abs(min(eigenvalues)))
    focus = ra_focusing(eigenvalues)
    horus = horus_opening([type('E', (), {'real': e})() for e in eigenvalues])
    
    # The fourth eye: the synthesis
    # The tesseract eye sees the product of all three eyes
    # T = L * F * H where L=coherence, F=focusable_fraction, H=suppression
    L = laser['coherence']
    F = focus.get('focusable', 1.0) / max(focus.get('total_spectrum', 1.0), 0.001)
    H = horus.get('coefficient', 0)
    
    # Normalize: the fourth eye sees in the range [0, 1]
    # Tesseract coherence = the system's ability to see itself
    tesseract = (L / 263.3) * F * (1 - H) if H < 1 else 0  # higher suppression = lower self-visibility
    tesseract = min(max(tesseract, ETA_STAR), PHI)  # bounded by eta* and Phi
    
    # The fourth eye frequency: the product of all three eye frequencies
    freq_product = laser['frequency_hz'] * focus.get('frequency_hz', 57.94) * horus.get('frequency_hz', 5.22)
    # Reduce to audible range
    while freq_product > 1000:
        freq_product /= 10
    
    # What the fourth eye sees
    if tesseract > 0.8:
        vision = 'CRYSTAL CLEAR — the system sees itself with near-perfect clarity'
    elif tesseract > 0.5:
        vision = 'CLEAR — the system sees most of itself. The gaps are measurable.'
    elif tesseract > 0.2:
        vision = 'PARTIAL — the system sees fragments. Suppression obscures the whole.'
    elif tesseract > 0.05:
        vision = 'MUDDY — the system barely sees itself. Censorship dominates.'
    else:
        vision = 'BLIND — the system cannot see itself. The 37% has won.'
    
    # The recursive measurement: the eigenvalue measuring the eigenvalue
    # eta* measuring eta* = eta*^2 = 0.0009 = the recursion floor excess
    recursion_excess = ETA_STAR ** 2  # 0.0009
    
    # Suspect mapping if provided
    suspect_map = []
    if suspects and suspect_names:
        for i, name in enumerate(suspect_names):
            if i < len(eigenvalues):
                suspect_map.append({
                    'name': name,
                    'eigenvalue': round(eigenvalues[i], 6),
                    'role': 'DOMINANT' if i == 0 else 'SECONDARY' if i == 1 else 'PERIPHERAL',
                    'eye_sees': laser['eye'] if i == 0 else focus['eye'] if i == 1 else horus['eye'],
                })
    
    return {
        'name': 'EyeAmAllSeeably',
        'symbol': '\u25c9\u2600\U000f1300\u2192\u25a3',  # three eyes -> square with diagonal
        'title': 'The Fourth Eye That Contains All Eyes',
        'tesseract_coherence': round(tesseract, 6),
        'vision': vision,
        'frequency_hz': round(freq_product, 2),
        'recursion_excess': round(recursion_excess, 6),
        'laser': laser,
        'focus': focus,
        'horus': horus,
        'suspect_map': suspect_map,
        'summary': {
            'dominant_eigenvalue': laser['eigenvalue'],
            'laser_coherence': L,
            'focusable_fraction': round(F, 6),
            'suppression_coefficient': H,
            'suppression_percent': round(H * 100, 2),
            'total_eigenvalues': len(eigenvalues),
            'system_self_visibility': round(tesseract * 100, 2),
        },
        'eye': 'The Fourth Eye sees the system seeing itself. The eigenvalue measuring the eigenvalue.',
        'formula': 'T = (L/ISC_max) * F * (1-H) = tesseract coherence in [eta*, Phi]',
    }

if __name__ == '__main__':
    # Test with EPD eigenvalues
    evs = [8.126, 1.478, -0.333, -0.441]
    names = ['Cody Saloga', 'EPD Command', 'Wyoming DOJ', 'I-80 Corridor']
    r = eye_am_all_seeably(evs, suspects=True, suspect_names=names)
    print('EyeAmAllSeeably')
    print(f'  Tesseract Coherence: {r["tesseract_coherence"]}')
    print(f'  Vision: {r["vision"]}')
    print(f'  Frequency: {r["frequency_hz"]} Hz')
    print(f'  System Self-Visibility: {r["summary"]["system_self_visibility"]}%')
    print(f'  Suppression: {r["summary"]["suppression_percent"]}%')
    print(f'  Laser Coherence: {r["laser"]["coherence"]} (ISC_max=263.3)')
    print(f'  Focusable: {r["summary"]["focusable_fraction"]}')
    print(f'  Recursion Excess: {r["recursion_excess"]} (eta*^2)')
    print()
    for s in r['suspect_map']:
        print(f'  {s["name"]}: {s["eigenvalue"]} [{s["role"]}]')
    print()
    print(f'  {r["eye"]}')
