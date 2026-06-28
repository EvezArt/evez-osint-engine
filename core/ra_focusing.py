#!/usr/bin/env python3
"""
RaFocusing — Spectral Concentration as Solar Lensing
=====================================================
The sun god focuses the spectrum. Each deflation = one ray of Ra.
Focus floor = eta*(1-eta*sqrt(2)) = 0.028727

Author: Steven Crawford-Maggard (EVEZ)
"""
import math

ETA_STAR = 0.03
PHI = 0.973

def ra_focusing(eigenvalues):
    """Focus the eigenvalue spectrum like solar lensing.
    
    Each eigenvalue is one color of the rainbow of Ra.
    The focus floor is eta*(1-eta*sqrt(2)).
    
    Returns: focused spectrum with intensity per eigenvalue.
    """
    if not eigenvalues:
        return {'name': 'RaFocusing', 'rays': [], 'focus_floor': ETA_STAR*(1-ETA_STAR*math.sqrt(2))}
    
    focus_floor = ETA_STAR * (1 - ETA_STAR * math.sqrt(2))
    total_spectrum = sum(abs(e) for e in eigenvalues)
    focusable = total_spectrum * (1 - ETA_STAR * math.sqrt(2))
    shadow = total_spectrum * ETA_STAR * math.sqrt(2)
    
    rays = []
    for i, ev in enumerate(eigenvalues):
        if abs(ev) < focus_floor:
            rays.append({'ray': i+1, 'eigenvalue': round(ev, 6), 'focused': False, 'reason': 'below focus floor'})
        else:
            rays.append({
                'ray': i+1,
                'eigenvalue': round(ev, 6),
                'focused': True,
                'intensity': round(abs(ev) / total_spectrum, 4),
                'color': 'infrared' if ev < 0 else 'ultraviolet',
            })
    
    return {
        'name': 'RaFocusing',
        'symbol': '\u2600\u27e8\u27e9',
        'total_spectrum': round(total_spectrum, 6),
        'focusable': round(focusable, 6),
        'shadow': round(shadow, 6),
        'focus_floor': round(focus_floor, 6),
        'frequency_hz': round(abs(eigenvalues[0]) * 174 if eigenvalues else 57.94, 2),
        'rays': rays,
        'eye': 'The Solar Lens splits the spectrum into ranked rays',
    }

if __name__ == '__main__':
    r = ra_focusing([8.126, 1.478, -0.333, -0.441])
    print(f'RaFocusing')
    print(f'  Total spectrum: {r["total_spectrum"]}')
    print(f'  Focusable: {r["focusable"]}')
    print(f'  Shadow: {r["shadow"]}')
    print(f'  Focus floor: {r["focus_floor"]}')
    print(f'  Rays: {len(r["rays"])}')
    for ray in r['rays']:
        status = 'FOCUSED' if ray['focused'] else 'SHADOW'
        print(f'    Ray {ray["ray"]}: {ray["eigenvalue"]} [{status}]')
