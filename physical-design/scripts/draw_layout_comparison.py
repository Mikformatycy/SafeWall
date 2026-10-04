"""Generate a scale-consistent engineering comparison from the same inputs as Fusion."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'layout-study.json').read_text())
battery = data['battery_reference']
energy = data['energy_assumptions_not_measurements']
factor = energy['average_conversion_efficiency'] * energy['usable_energy_fraction']
nominal = battery['capacity_typical_mah'] / 1000 * battery['nominal_voltage_v']
minimum = battery['capacity_minimum_mah'] / 1000 * battery['nominal_voltage_v']
calculations = {
    'status': 'calculated_estimates_not_measurements',
    'nominal_battery_energy_wh': nominal,
    'minimum_capacity_based_energy_wh': minimum,
    'assumed_conversion_efficiency': energy['average_conversion_efficiency'],
    'assumed_usable_energy_fraction': energy['usable_energy_fraction'],
    'average_load_limit_for_2h_typical_w': nominal * factor / 2,
    'average_load_limit_for_2h_minimum_capacity_w': minimum * factor / 2,
    'runtime_scenarios_h': {str(p): nominal * factor / p for p in energy['load_scenarios_w']},
    'variants': [{
        'id': v['id'], 'width_length_height_mm': [v['width'], v['length'], v['height']],
        'bounding_box_volume_cm3': v['width'] * v['length'] * v['height'] / 1000,
    } for v in data['variants']],
}
(ROOT / 'layout-study-calculations.json').write_text(json.dumps(calculations, indent=2))
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="1120" viewBox="0 0 1200 1120">',
       '<rect width="1200" height="1120" fill="#F3F4F1"/>',
       '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#202B34}.muted{fill:#63717D}.small{font-size:16px}.body{font-size:18px}.title{font-size:32px;font-weight:700}.dim{font-size:19px;font-weight:700}</style>']


def rect(x, y, w, h, fill, radius=0, extra=''):
    svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" {extra}/>')


def text(x, y, content, cls='body', extra=''):
    svg.append(f'<text x="{x}" y="{y}" class="{cls}" {extra}>{html.escape(content)}</text>')


text(48, 52, 'SafeWall / porównanie układu wnętrza', 'title')
text(48, 83, 'KONCEPCJA v01 · ta sama bateria w obu wariantach · wymiary robocze, przed walidacją', 'body')
rect(46, 108, 1108, 2, '#CFD7D7')
scale = 3
for v, ox in zip(data['variants'], [84, 754]):
    is_b = v['id'] == 'B'
    text(ox, 150, 'B / bateria pod elektroniką' if is_b else 'A / bateria obok elektroniki', 'dim')
    text(ox, 178, f"{v['width']} × {v['length']} × {v['height']} mm", 'dim')
    oy = 212
    w, length = v['width'], v['length']
    rect(ox, oy, w*scale, length*scale, '#282C30', v['corner_radius']*scale)
    rect(ox+4.8, oy+4.8, (w-3.2)*scale, (length-3.2)*scale, '#E4E9E6', 22)
    # Plan view: high Y is at the top.
    def part(x, y, pw, pl, color, caption, dash=False):
        px, py = ox+x*scale, oy+(length-y-pl)*scale
        rect(px, py, pw*scale, pl*scale, color, 4,
             'stroke="#64737C" stroke-width="2" stroke-dasharray="6 4"' if dash else '')
        if caption:
            text(px+8, py+23, caption, 'small')
    if is_b:
        part(v['battery_x'], v['battery_y'], 55.5, 92, '#CBD4DE', '', True)
    else:
        part(v['battery_x'], v['battery_y'], 55.5, 92, '#CBD4DE', 'Akumulator')
    cx, cy = v['carrier_x'], v['carrier_y']
    part(cx, cy, 60, 88, '#74A990', '')
    part(cx+2.5, cy+42, 55, 40, '#C0D9CB', 'CM4')
    part(cx+5, cy+5, 32, 29, '#A7B8C7', 'LTE*')
    part(cx+42, cy+5, 15, 29, '#D8B382', '')
    svg.append(f'<circle cx="{ox+w*scale/2}" cy="{oy+(length-80)*scale}" r="{54.1*scale/2}" fill="none" stroke="#EAF6FD" stroke-width="2" stroke-dasharray="7 5"/>')
    text(ox, 575, 'Mniejsza grubość, duża szerokość' if not is_b else 'Kierunek preferowany do MagSafe', 'small')
    text(ox, 599, 'Bateria i elektronika na jednym poziomie' if not is_b else 'Bateria schowana pod płytką bazową', 'small')
    text(ox, 640, 'Przekrój gabarytowy (X–Z)', 'dim')
    sy = 750
    rect(ox, sy-v['height']*scale, w*scale, v['height']*scale, '#282C30', 5)
    rect(ox+4.8, sy-(v['height']-1.6)*scale, (w-3.2)*scale, (v['height']-4.6)*scale, '#E4E9E6', 1)
    # A projected envelope section, not a cut through a specific PCB trace.
    def section(x, z, pw, ph, color):
        rect(ox+x*scale, sy-(z+ph)*scale, pw*scale, ph*scale, color, 1)
    section(v['battery_x'], v['battery_z'], 55.5, 6.3, '#A7B8C7')
    section(cx, v['carrier_z'], 60, 1.6, '#287555')
    section(cx+2.5, v['carrier_z']+1.6, 55, 6.578, '#74A990')
    text(ox, 783, f"Grubość: {v['height']} mm", 'dim')
text(84, 815, '* Moduł LTE jest tylko odniesieniem wymiarowym. Pomarańczowy: rezerwa zasilania i I/O.', 'small')
rect(48, 844, 1104, 166, '#FFFFFF', 16)
text(72, 881, 'Cel: 2 godziny pracy', 'dim')
text(72, 912, f'3400 mAh × 3,7 V = {nominal:.2f} Wh; założenia: sprawność 90%, użyteczna energia 90%.', 'body')
text(72, 942, f'Limit średniego poboru: {nominal*factor/2:.2f} W typowo / {minimum*factor/2:.2f} W przy pojemności minimalnej.', 'body')
text(72, 976, 'Szacunek czasu: ' + '   ·   '.join(f'{p} W → {nominal*factor/p:.2f} h' for p in energy['load_scenarios_w']), 'body')
text(48, 1044, 'Niezweryfikowane: anteny, termika, PCB, porty, luzy baterii, geometria telefonu i siła mocowania.', 'small')
text(48, 1073, 'Źródła: Raspberry Pi CM4 datasheet; EEMB LP605590-PCM-NTC-LD; Apple Accessory Design Guidelines 2026-09-21.', 'small')
text(48, 1097, 'Wspólna skala widoków. To rysunek obliczeniowy, nie zrzut z Fusion ani projekt do produkcji.', 'small')
svg.append('</svg>')
(ROOT/'layout-comparison.svg').write_text('\n'.join(svg))
print(json.dumps(calculations, indent=2))
print('Generated layout-comparison.svg')
