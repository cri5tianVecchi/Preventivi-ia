"""Genera il listino demo (materiale elettrico) per la Fase 0.
Output: listino.csv e seed.sql nella cartella passata come argomento.
Marche e codici sono inventati; prezzi di listino indicativi (prima dello sconto).
"""
import csv, json, sys, random
from pathlib import Path

random.seed(42)
OUT = Path(sys.argv[1])
articoli = []

def add(codice, descrizione, categoria, marca, unita, prezzo, moduli=None, confezione=1, **attr):
    articoli.append(dict(
        codice=codice, descrizione=descrizione, categoria=categoria, marca=marca,
        unita=unita, confezione=confezione, prezzo_listino=round(prezzo, 2),
        moduli_din=moduli, attributi={k: v for k, v in attr.items() if v is not None},
    ))

def var(p):  # piccola variazione per non avere prezzi troppo "puliti"
    return p * random.uniform(0.97, 1.03)

# ---------- Interruttori magnetotermici ----------
POLI = {"1P": (1, 14), "1P+N": (2, 22), "2P": (2, 38), "3P": (3, 62), "4P": (4, 85)}
F_IN = {6: 1.05, 10: 1, 16: 1, 20: 1, 25: 1.02, 32: 1.08, 40: 1.3, 50: 1.45, 63: 1.6}
F_PDI = {4.5: 0.85, 6: 1, 10: 1.45}
F_CURVA = {"B": 1.05, "C": 1, "D": 1.25}

def mt(poli, In, curva, pdi):
    mod, base = POLI[poli]
    p = base * F_IN[In] * F_PDI[pdi] * F_CURVA[curva]
    pp = poli.replace("+", "")
    add(f"VOL-MT{pp}-{curva}{In:02d}-{str(pdi).replace('.', '')}",
        f"Interruttore magnetotermico {poli} curva {curva} {In}A {pdi}kA {mod} modul{"o" if mod == 1 else "i"}",
        "magnetotermici", "Voltaria", "pz", var(p), mod,
        poli=poli, corrente_a=In, curva=curva, potere_interruzione_ka=pdi, tensione_v=230 if poli in ("1P", "1P+N", "2P") else 400)

for poli in POLI:
    for In in F_IN:
        mt(poli, In, "C", 6)
for In in (10, 16, 20):
    mt("1P+N", In, "C", 4.5)
for poli in ("3P", "4P"):
    for In in (16, 20, 25, 32, 40, 63):
        mt(poli, In, "C", 10)
for In in (16, 25, 32, 40, 63):
    mt("3P", In, "D", 10)
for In in (6, 10, 16, 20):
    mt("1P+N", In, "B", 6)

# ---------- Interruttori differenziali puri ----------
F_TIPO = {"AC": 1, "A": 1.3, "F": 1.8}
def diff(poli, In, idn, tipo, selettivo=False):
    mod = 2 if poli == "2P" else 4
    base = 65 if poli == "2P" else 150
    p = base * {25: 1, 40: 1.12, 63: 1.4}[In] * F_TIPO[tipo] * (0.9 if idn >= 300 else 1) * (1.4 if selettivo else 1)
    s = "S" if selettivo else ""
    add(f"VOL-ID{poli}-{In}-{idn}{tipo}{s}",
        f"Interruttore differenziale puro {poli} {In}A {idn}mA tipo {tipo}{' selettivo' if selettivo else ''}",
        "differenziali", "Voltaria", "pz", var(p), mod,
        poli=poli, corrente_a=In, sensibilita_ma=idn, classe_diff=tipo, selettivo=selettivo)

for In in (25, 40, 63):
    for tipo in ("AC", "A"):
        diff("2P", In, 30, tipo)
    diff("2P", In, 30, "F") if In != 63 else None
    for idn in (30, 300):
        diff("4P", In, idn, "A")
    diff("4P", In, 300, "A", selettivo=True)

# ---------- Magnetotermici differenziali compatti ----------
for In in (6, 10, 16, 20, 25, 32):
    for tipo in ("AC", "A"):
        p = 78 * F_TIPO[tipo] * (1.1 if In >= 25 else 1)
        add(f"VOL-MTD1N-C{In:02d}-30{tipo}",
            f"Interruttore magnetotermico differenziale 1P+N C{In} 30mA tipo {tipo} 6kA 2 moduli",
            "magnetotermici_differenziali", "Voltaria", "pz", var(p), 2,
            poli="1P+N", corrente_a=In, curva="C", potere_interruzione_ka=6, sensibilita_ma=30, classe_diff=tipo)

# ---------- Blocchi differenziali (accessori da accoppiare a un magnetotermico) ----------
for poli, mod, base in (("2P", 2, 55), ("4P", 3, 120)):
    for In in (25, 40, 63):
        for idn in (30, 300):
            p = base * {25: 1, 40: 1.1, 63: 1.35}[In] * (0.9 if idn == 300 else 1)
            add(f"VOL-BD{poli}-{In}-{idn}A",
                f"Blocco differenziale {poli} {In}A {idn}mA tipo A da accoppiare a magnetotermico",
                "blocchi_differenziali", "Voltaria", "pz", var(p), mod,
                poli=poli, corrente_max_a=In, sensibilita_ma=idn, classe_diff="A", accessorio=True)

# ---------- Centralini e quadri ----------
for mod in (4, 8, 12, 18, 24, 36, 54, 72):
    add(f"QDX-CP40-{mod:02d}", f"Centralino da parete IP40 {mod} moduli DIN con portella fumé",
        "quadri", "Quadrix", "pz", var(10 + mod * 1.35), None,
        moduli_disponibili=mod, grado_ip="IP40", montaggio="parete", tipo_quadro="modulare")
for mod in (4, 8, 12, 18, 24, 36, 54):
    add(f"QDX-CP65-{mod:02d}", f"Centralino stagno da parete IP65 {mod} moduli DIN portella trasparente",
        "quadri", "Quadrix", "pz", var(18 + mod * 2.1), None,
        moduli_disponibili=mod, grado_ip="IP65", montaggio="parete", tipo_quadro="modulare")
for mod in (8, 12, 18, 24, 36, 54):
    add(f"QDX-CI40-{mod:02d}", f"Centralino da incasso IP40 {mod} moduli DIN con cassetta e portella",
        "quadri", "Quadrix", "pz", var(22 + mod * 1.6), None,
        moduli_disponibili=mod, grado_ip="IP40", montaggio="incasso", tipo_quadro="modulare")
for (h, l, p) in ((600, 400, 210), (800, 600, 320), (1000, 800, 480), (1200, 800, 610)):
    add(f"QDX-ARM55-{h}{l}", f"Quadro metallico a armadio IP55 {h}x{l}x250 mm con piastra di fondo",
        "quadri", "Quadrix", "pz", var(p), None,
        grado_ip="IP55", montaggio="pavimento/parete", tipo_quadro="armadio", altezza_mm=h, larghezza_mm=l,
        accetta_scatolati=True)

# ---------- Interruttori scatolati (MCCB) ----------
for poli in ("3P", "4P"):
    for In in (100, 160, 250):
        for icu in (25, 36):
            p = {100: 380, 160: 520, 250: 760}[In] * (1.25 if poli == "4P" else 1) * (1.2 if icu == 36 else 1)
            add(f"VOL-SC{poli}-{In}-{icu}", f"Interruttore scatolato {poli} {In}A Icu {icu}kA sganciatore termomagnetico regolabile",
                "scatolati", "Voltaria", "pz", var(p), None,
                poli=poli, corrente_a=In, potere_interruzione_ka=icu, montaggio="piastra", tensione_v=400)

# ---------- Sezionatori ----------
for poli, mod in (("2P", 2), ("4P", 4)):
    for In in (32, 63, 100):
        add(f"VOL-SZ{poli}-{In}", f"Interruttore sezionatore modulare {poli} {In}A {mod} modul{"o" if mod == 1 else "i"}",
            "sezionatori", "Voltaria", "pz", var((24 if poli == "2P" else 46) * {32: 1, 63: 1.3, 100: 1.8}[In]), mod,
            poli=poli, corrente_a=In)

# ---------- Contattori ----------
for In in (20, 25, 40):
    mod = 1 if In == 20 else 2
    add(f"VOL-CM2NO-{In}", f"Contattore modulare 2NO {In}A bobina 230V AC {mod} modul{"o" if mod == 1 else "i"}",
        "contattori", "Voltaria", "pz", var({20: 32, 25: 41, 40: 68}[In]), mod,
        contatti="2NO", corrente_a=In, bobina_v=230, tipo_contattore="modulare")
for In in (9, 12, 18, 25, 32, 40):
    for bob in (24, 230):
        add(f"FRT-CT3P-{In:02d}-{bob}", f"Contattore tripolare AC-3 {In}A bobina {bob}V AC 1NO aux montaggio guida DIN",
            "contattori", "Ferrotec", "pz", var({9: 38, 12: 44, 18: 58, 25: 79, 32: 104, 40: 139}[In]), None,
            poli="3P", corrente_ac3_a=In, bobina_v=bob, tipo_contattore="industriale")

# ---------- Relè e dispositivi di comando ----------
add("VOL-RPP-16", "Relè passo-passo 1NO 16A bobina 230V 1 modulo", "comando", "Voltaria", "pz", var(29), 1, corrente_a=16)
add("VOL-CRP-16", "Interruttore crepuscolare con sonda esterna IP54 16A 1 modulo", "comando", "Voltaria", "pz", var(64), 1, corrente_a=16)
add("VOL-ORD-16", "Interruttore orario digitale settimanale 16A 2 moduli", "comando", "Voltaria", "pz", var(79), 2, corrente_a=16)
add("VOL-SPV-01", "Spia luminosa modulare LED verde 230V 1 modulo", "comando", "Voltaria", "pz", var(12), 1)

# ---------- Scaricatori di sovratensione ----------
for poli, mod, p, tipo in (("1P+N", 2, 115, "2"), ("3P+N", 4, 230, "2"), ("1P+N", 2, 290, "1+2"), ("3P+N", 4, 560, "1+2")):
    add(f"VOL-SPD{tipo.replace('+', '')}-{poli.replace('+', '')}", f"Scaricatore di sovratensione SPD tipo {tipo} {poli} con cartucce estraibili",
        "scaricatori", "Voltaria", "pz", var(p), mod, poli=poli, tipo_spd=tipo,
        protezione_monte_max_a=125 if tipo == "2" else 160)

# ---------- Cavi ----------
def cavo_m(sigla, cond, sez, desc_extra, f, base):
    return base + cond * sez * f

for cond, sezs in ((3, (1.5, 2.5, 4, 6, 10)), (5, (1.5, 2.5, 4, 6, 10, 16, 25))):
    for s in sezs:
        sz = f"{int(s*10):03d}"
        add(f"CVX-FG16OR16-{cond}G{sz}", f"Cavo FG16OR16 0,6/1kV {cond}G{str(s).replace('.', ',')} mm² multipolare guaina PVC grigia",
            "cavi", "Cavilux", "m", var(cavo_m("FG16OR16", cond, s, "", 0.20, 0.30)), None,
            confezione=100 if s < 16 else 1,
            tipo_cavo="FG16OR16", conduttori=cond, sezione_mm2=s, tensione_v=1000, posa="esterna/interrata", isolante="EPR")
for s in (2.5, 4):
    add(f"CVX-FG16OR16-2X{int(s*10):03d}", f"Cavo FG16OR16 0,6/1kV 2x{str(s).replace('.', ',')} mm² multipolare senza PE",
        "cavi", "Cavilux", "m", var(cavo_m("", 2, s, "", 0.20, 0.28)), None, confezione=100,
        tipo_cavo="FG16OR16", conduttori=2, sezione_mm2=s, tensione_v=1000, posa="esterna/interrata", isolante="EPR")
for s in (16, 25, 35, 50, 70, 95, 120):
    add(f"CVX-FG16R16-1X{s*10:04d}", f"Cavo FG16R16 0,6/1kV unipolare 1x{s} mm² nero",
        "cavi", "Cavilux", "m", var(cavo_m("", 1, s, "", 0.21, 0.4)), None, confezione=1,
        tipo_cavo="FG16R16", conduttori=1, sezione_mm2=s, tensione_v=1000, posa="esterna/interrata", isolante="EPR")
COLORI = {"BL": "blu", "MA": "marrone", "GV": "giallo-verde", "NE": "nero", "GR": "grigio"}
for s in (1.5, 2.5, 4, 6, 10, 16):
    for c, nome in COLORI.items():
        add(f"CVX-FS17-{int(s*10):03d}-{c}", f"Cavo FS17 450/750V unipolare 1x{str(s).replace('.', ',')} mm² {nome}",
            "cavi", "Cavilux", "m", var(cavo_m("", 1, s, "", 0.14, 0.08)), None, confezione=100,
            tipo_cavo="FS17", conduttori=1, sezione_mm2=s, tensione_v=750, colore=nome, posa="in tubo/canalina", isolante="PVC")

# ---------- Tubi e canaline ----------
for d, conf in ((16, 100), (20, 100), (25, 50), (32, 50), (40, 25), (50, 25)):
    add(f"PLX-TCP-{d}", f"Tubo corrugato flessibile pesante PVC Ø{d} mm grigio (matassa {conf} m)",
        "tubi_canaline", "Plastex", "m", var(0.18 + d * 0.022), None, confezione=conf,
        diametro_mm=d, tipo="corrugato pesante")
for (l, h) in ((25, 17), (40, 17), (40, 25), (60, 40), (80, 40), (100, 60)):
    add(f"PLX-CAN-{l}{h}", f"Canalina PVC {l}x{h} mm con coperchio bianca (barre da 2 m)",
        "tubi_canaline", "Plastex", "m", var(0.9 + l * h * 0.0012), None, confezione=2,
        larghezza_mm=l, altezza_mm=h)

# ---------- Morsetti ----------
for (smin, smax, p) in ((0.2, 4, 0.55), (0.5, 6, 0.85), (2.5, 10, 1.6), (4, 16, 2.4), (10, 35, 4.9), (25, 70, 9.8)):
    add(f"FRT-MRS-{str(smax).replace('.', '')}", f"Morsetto componibile su guida DIN sezione {str(smin).replace('.', ',')}-{smax} mm²",
        "morsetti", "Ferrotec", "pz", var(p), None, confezione=10 if smax <= 16 else 1,
        sezione_min_mm2=smin, sezione_max_mm2=smax)

# ---------- Prese e spine industriali CEE ----------
for In in (16, 32):
    for poli, v in (("2P+T", 230), ("3P+T", 400), ("3P+N+T", 400)):
        for ip in ("IP44", "IP67"):
            p = {16: 9, 32: 16}[In] * (1 + 0.25 * poli.count("P")) * (1.6 if ip == "IP67" else 1)
            add(f"VOL-PCE-{In}{poli.replace('+', '')}-{ip[2:]}", f"Presa industriale CEE da parete {poli} {In}A {v}V {ip}",
                "prese_industriali", "Voltaria", "pz", var(p), None,
                poli=poli, corrente_a=In, tensione_v=v, grado_ip=ip)

# ---------- Pressacavi ----------
for m, (dmin, dmax), p in (("M16", (4, 8), 0.45), ("M20", (6, 12), 0.6), ("M25", (9, 17), 0.85), ("M32", (13, 21), 1.4), ("M40", (19, 28), 2.3)):
    add(f"PLX-PRC-{m}", f"Pressacavo in poliammide {m} IP68 per cavi Ø{dmin}-{dmax} mm",
        "accessori", "Plastex", "pz", var(p), None, confezione=10,
        filettatura=m, diametro_cavo_min_mm=dmin, diametro_cavo_max_mm=dmax, grado_ip="IP68")

# ---------- Output ----------
codici = [a["codice"] for a in articoli]
assert len(codici) == len(set(codici)), "codici duplicati"

with open(OUT / "listino.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["codice", "descrizione", "categoria", "marca", "unita", "confezione", "prezzo_listino", "moduli_din", "attributi"])
    for a in articoli:
        w.writerow([a["codice"], a["descrizione"], a["categoria"], a["marca"], a["unita"], a["confezione"],
                    f"{a['prezzo_listino']:.2f}", a["moduli_din"] if a["moduli_din"] is not None else "",
                    json.dumps(a["attributi"], ensure_ascii=False)])

def q(s):
    return "'" + str(s).replace("'", "''") + "'"

with open(OUT / "seed.sql", "w", encoding="utf-8") as f:
    f.write("-- Dati demo generati: marche e codici inventati, prezzi indicativi.\nBEGIN;\n")
    f.write("INSERT INTO articoli (codice, descrizione, categoria, marca, unita, confezione, prezzo_listino, moduli_din, attributi) VALUES\n")
    rows = []
    for a in articoli:
        rows.append(f"({q(a['codice'])}, {q(a['descrizione'])}, {q(a['categoria'])}, {q(a['marca'])}, {q(a['unita'])}, "
                    f"{a['confezione']}, {a['prezzo_listino']:.2f}, {a['moduli_din'] if a['moduli_din'] is not None else 'NULL'}, "
                    f"{q(json.dumps(a['attributi'], ensure_ascii=False))}::jsonb)")
    f.write(",\n".join(rows) + ";\n")
    regole = json.loads((OUT / "regole.json").read_text(encoding="utf-8"))
    f.write("\nINSERT INTO regole (id, nome, gravita, tipo, descrizione, parametri) VALUES\n")
    f.write(",\n".join(
        f"({q(r['id'])}, {q(r['nome'])}, {q(r['gravita'])}, {q(r['tipo'])}, {q(r['descrizione'])}, {q(json.dumps(r['parametri'], ensure_ascii=False))}::jsonb)"
        for r in regole["regole"]) + ";\nCOMMIT;\n")

from collections import Counter
print(len(articoli), "articoli")
print(Counter(a["categoria"] for a in articoli))