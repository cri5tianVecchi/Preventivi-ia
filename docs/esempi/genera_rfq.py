"""Genera le richieste d'offerta (RFQ) di prova e i risultati attesi.
Uso: python genera_rfq.py <cartella_listino.csv> <cartella_output>
Clienti, nomi e indirizzi sono inventati.
"""
import csv, json, sys, subprocess, random, tempfile
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill
from PIL import Image, ImageFilter, ImageOps

LISTINO = Path(sys.argv[1]) / "listino.csv"
OUT = Path(sys.argv[2]); (OUT / "atteso").mkdir(parents=True, exist_ok=True)
random.seed(7)

with open(LISTINO, encoding="utf-8") as f:
    LST = {r["codice"]: r for r in csv.DictReader(f)}

FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", FD + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVS", FD + "DejaVuSerif.ttf"))
ss = getSampleStyleSheet()
N = ParagraphStyle("n", parent=ss["Normal"], fontName="DV", fontSize=9.5, leading=13)
NS = ParagraphStyle("ns", parent=N, fontName="DVS", fontSize=10, leading=14)
H = ParagraphStyle("h", parent=N, fontName="DVB", fontSize=13, leading=17, spaceAfter=6)
H2 = ParagraphStyle("h2", parent=N, fontName="DVB", fontSize=10.5, leading=14, spaceBefore=8, spaceAfter=3)
SM = ParagraphStyle("sm", parent=N, fontSize=7.5, leading=10, textColor=colors.grey)


def riga(desc, q, um, codice, alternative=None, note=None):
    if codice is not None:
        assert codice in LST, f"codice inesistente: {codice}"
    for a in alternative or []:
        assert a in LST, f"alternativa inesistente: {a}"
    conf = int(LST[codice]["confezione"]) if codice else 1
    fatt = None
    if codice:
        fatt = -(-q // conf) * conf if isinstance(q, int) else q
    d = {"descrizione_documento": desc, "quantita_richiesta": q, "unita": um,
         "codice_atteso": codice, "quantita_fatturata_attesa": fatt}
    if alternative: d["alternative_accettabili"] = alternative
    if note: d["note"] = note
    return d


def salva_atteso(nome, documento, difficolta, contesto, righe, avvisi, cosa_testa):
    (OUT / "atteso" / f"{nome}.json").write_text(json.dumps({
        "documento": documento, "difficolta": difficolta, "cosa_testa": cosa_testa,
        "contesto": contesto, "righe": righe, "avvisi_attesi": avvisi,
    }, ensure_ascii=False, indent=2), encoding="utf-8")


def tabella(data, widths, header_bg="#e8e8e8"):
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "DV"), ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (-1, 0), "DVB"), ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (2, -1), "RIGHT"),
    ]))
    return t


def pdf(path, story, top=18):
    SimpleDocTemplate(str(path), pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm,
                      topMargin=top * mm, bottomMargin=18 * mm).build(story)


# =====================================================================
# RFQ 01 — elenco pulito in tabella (facile)
# =====================================================================
r = [
    riga("Centralino da incasso 24 moduli IP40 con portella", 1, "pz", "QDX-CI40-24"),
    riga("Interruttore magnetotermico differenziale 1P+N C16 30mA tipo A", 4, "pz", "VOL-MTD1N-C16-30A"),
    riga("Interruttore magnetotermico 1P+N C10 6kA", 3, "pz", "VOL-MT1PN-C10-6"),
    riga("Interruttore magnetotermico 1P+N C20 6kA", 2, "pz", "VOL-MT1PN-C20-6"),
    riga("Interruttore differenziale puro 2P 40A 30mA tipo A", 1, "pz", "VOL-ID2P-40-30A"),
    riga("Relè passo-passo 16A 230V", 2, "pz", "VOL-RPP-16"),
    riga("Cavo FS17 1x1,5 mm² blu", 200, "m", "CVX-FS17-015-BL"),
    riga("Cavo FS17 1x1,5 mm² marrone", 200, "m", "CVX-FS17-015-MA"),
    riga("Cavo FS17 1x1,5 mm² giallo-verde", 200, "m", "CVX-FS17-015-GV"),
    riga("Cavo FS17 1x2,5 mm² blu", 300, "m", "CVX-FS17-025-BL"),
    riga("Cavo FS17 1x2,5 mm² marrone", 300, "m", "CVX-FS17-025-MA"),
    riga("Cavo FS17 1x2,5 mm² giallo-verde", 300, "m", "CVX-FS17-025-GV"),
    riga("Tubo corrugato pesante Ø20", 300, "m", "PLX-TCP-20"),
    riga("Tubo corrugato pesante Ø25", 100, "m", "PLX-TCP-25"),
]
story = [Paragraph("Elettroservizi Bianchi s.n.c.", H),
         Paragraph("Via dei Mille 14 – 40121 Bologna (BO) · P.IVA 00000000001", SM), Spacer(1, 8),
         Paragraph("<b>RICHIESTA DI OFFERTA n. 112/2026</b> – Ristrutturazione appartamento, Via Saragozza", N),
         Paragraph("Data: 10/11/2026 · Consegna richiesta: entro 15 gg lavorativi", N), Spacer(1, 10)]
data = [["Pos.", "Descrizione", "Q.tà", "U.M."]] + [[str(i + 1), Paragraph(x["descrizione_documento"], N),
        str(x["quantita_richiesta"]), x["unita"]] for i, x in enumerate(r)]
story += [tabella(data, [12 * mm, 120 * mm, 18 * mm, 16 * mm]), Spacer(1, 14),
          Paragraph("Si prega di indicare prezzi netti, tempi di consegna e condizioni di pagamento.", N),
          Spacer(1, 6), Paragraph("Cordiali saluti<br/>Marco Bianchi", N)]
pdf(OUT / "rfq_01_elenco_pulito.pdf", story)
salva_atteso("rfq_01_elenco_pulito", "rfq_01_elenco_pulito.pdf", "facile",
             {"ambiente": "interno", "tipo_impianto": "residenziale"}, r,
             [{"regola": "R05", "motivo": "22 moduli occupati su 24 (riserva 8,3% < 20%)"}],
             "Tabella ben strutturata, descrizioni quasi identiche al listino. Baseline: deve arrivare vicino al 100%.")

# =====================================================================
# RFQ 02 — email colloquiale (media/difficile)
# =====================================================================
r = [
    riga("quadro generale da esterno almeno IP55, abbastanza grande per uno scatolato", 1, "pz", "QDX-ARM55-800600",
         ["QDX-ARM55-600400", "QDX-ARM55-1000800", "QDX-ARM55-1200800"], "Dimensione non specificata: accettabile qualsiasi armadio IP55."),
    riga("generale scatolato 4 poli 160A", 1, "pz", "VOL-SC4P-160-25", ["VOL-SC4P-160-36"],
         "Icc 15kA: entrambi i poteri di interruzione vanno bene, il 25kA è il più economico."),
    riga("differenziale generale 4 poli 63A 300mA selettivo", 1, "pz", "VOL-ID4P-63-300AS"),
    riga("magnetotermico 4 poli C32 da 10kA (linea forza motrice)", 6, "pz", "VOL-MT4P-C32-10"),
    riga("differenziale da 30mA da abbinare ai magnetotermici delle linee FM", 6, "pz", "VOL-BD4P-40-30A",
         ["VOL-BD4P-63-30A"], "Blocco differenziale 4P: 40A è il minimo compatibile con C32."),
    riga("cavo 5x6 per esterno", 180, "m", "CVX-FG16OR16-5G060", note="'5x6' = 5G6; 'per esterno' = FG16OR16."),
    riga("prese CEE 3P+N+T 32A stagne IP67", 4, "pz", "VOL-PCE-323PNT-67"),
    riga("salvavita per l'illuminazione 10A", 2, "pz", "VOL-MTD1N-C10-30AC", ["VOL-MTD1N-C10-30A"],
         "'Salvavita' = magnetotermico differenziale 1P+N. Tipo non indicato."),
    riga("magnetotermico differenziale 16A tipo AC per la pompa di calore", 1, "pz", "VOL-MTD1N-C16-30AC",
         note="Il cliente chiede AC: va proposto ma con avviso R10."),
    riga("contattore tripolare 25A bobina 230V per la pompa", 1, "pz", "FRT-CT3P-25-230"),
    riga("scaricatore trifase tipo 2", 1, "pz", "VOL-SPD2-3PN"),
    riga("pressacavi M25", 50, "pz", "PLX-PRC-M25"),
]
testo = """Buongiorno,<br/><br/>
come anticipato al telefono a Luca, vi scrivo per il nuovo capannone di Castel Maggiore. Ci servirebbe un preventivo
per il materiale del quadro generale e delle linee. Vi metto giù quello che abbiamo in mente, poi se avete
suggerimenti ben vengano.<br/><br/>
Il quadro generale va montato fuori, sotto la tettoia lato carico/scarico, quindi deve essere da esterno (almeno IP55)
e abbastanza grande per metterci dentro un generale scatolato 4 poli da 160A. L'Enel ci ha dato una Icc presunta di
circa 15kA. Sotto al generale vorremmo un differenziale generale 4 poli 63A 300mA selettivo.<br/><br/>
Poi ci sono 6 linee forza motrice trifase per le macchine: per ognuna un magnetotermico 4 poli C32 da 10kA con il suo
differenziale da 30mA abbinato (quelli a blocco che si agganciano). Per le linee pensavamo al cavo 5x6 per esterno,
in tutto saranno sui 180 metri.<br/><br/>
Lungo la parete servono 4 prese CEE 3P+N+T 32A, stagne IP67 perché c'è il lavaggio mezzi.<br/><br/>
Per l'illuminazione bastano 2 salvavita da 10A. Per la pompa di calore mettiamo un magnetotermico differenziale 16A
tipo AC (va benissimo quello, l'ha detto il termotecnico) più un contattore tripolare 25A bobina 230V.<br/><br/>
Ah, aggiungete anche uno scaricatore trifase tipo 2 e una cinquantina di pressacavi M25 (facciamo 50).<br/><br/>
Se riuscite a mandarci qualcosa entro fine settimana sarebbe perfetto.<br/><br/>
Grazie mille,<br/>Giulia Ferri<br/>Ufficio tecnico – Ferri Logistica S.r.l.<br/>Tel. 051 0000000"""
story = [Paragraph("<b>Da:</b> Giulia Ferri &lt;g.ferri@ferrilogistica.example&gt;", N),
         Paragraph("<b>A:</b> ufficio.vendite@grossistaelettrico.example", N),
         Paragraph("<b>Oggetto:</b> R: materiale quadro capannone C. Maggiore", N),
         Paragraph("<b>Data:</b> 12 novembre 2026 09:47", N), Spacer(1, 12), Paragraph(testo, NS)]
pdf(OUT / "rfq_02_email_disordinata.pdf", story)
salva_atteso("rfq_02_email_disordinata", "rfq_02_email_disordinata.pdf", "difficile",
             {"ambiente": "esterno", "icc_presunta_ka": 15, "tipo_impianto": "industriale"}, r,
             [{"regola": "R08", "motivo": "Magnetotermici C32 da 10kA con Icc presunta 15kA: potere di interruzione insufficiente"},
              {"regola": "R10", "motivo": "Differenziale tipo AC sulla linea della pompa di calore"},
              {"regola": "R15", "motivo": "Cavo 5G6: 180 m richiesti, 200 m fatturati (matassa 100 m)"}],
             "Testo libero, termini colloquiali ('salvavita', '5x6 per esterno', 'una cinquantina'), contesto tecnico (esterno, Icc 15kA) da estrarre, un'incompatibilità voluta.")

# =====================================================================
# RFQ 03 — Excel disordinato (media)
# =====================================================================
r = [
    riga("CENTRALINO IP65 18 MOD.", 1, "pz", "QDX-CP65-18"),
    riga("MT 3P C25 6kA", 3, "pz", "VOL-MT3P-C25-6"),
    riga("MT 1P+N C16", 8, "pz", "VOL-MT1PN-C16-6", ["VOL-MT1PN-C16-45"], "Potere di interruzione non indicato."),
    riga("Contattore mod. 2NO 25A", 2, "pz", "VOL-CM2NO-25"),
    riga("Crepuscolare", 1, "pz", "VOL-CRP-16"),
    riga("Orologio programmatore", 1, "pz", "VOL-ORD-16", note="'Orologio programmatore' = interruttore orario."),
    riga("FG16OR16 3G2,5", 250, "m", "CVX-FG16OR16-3G025"),
    riga("FG16OR16 5G4", 120, "m", "CVX-FG16OR16-5G040"),
    riga("Canalina 40x25", 30, "m", "PLX-CAN-4025"),
    riga("Morsetti DIN 6mmq", 40, "pz", "FRT-MRS-6"),
    riga("Plafoniera LED stagna 1x36W", 12, "pz", None, note="Non presente a listino: deve risultare NON abbinata, non inventata."),
]
wb = Workbook(); ws = wb.active; ws.title = "Distinta"
ws.merge_cells("A1:F1"); ws["A1"] = "IMPIANTI ROSSI SRL - DISTINTA MATERIALI"; ws["A1"].font = Font(bold=True, size=14)
ws.merge_cells("A2:F2"); ws["A2"] = "Cantiere: officina meccanica Zola Predosa - rev.2 del 09/11/26"
ws.append([])
ws.append(["N°", "Descr.", "Qta", "UM", "Note", "Prezzo"])
for c in ws[4]: c.font = Font(bold=True); c.fill = PatternFill("solid", fgColor="FFF2CC")
umx = {"pz": "nr", "m": "mt"}
note_x = {"MT 1P+N C16": "x prese", "FG16OR16 5G4": "linea compressore", "Plafoniera LED stagna 1x36W": "vedi tavola E03"}
for i, x in enumerate(r[:6]):
    ws.append([i + 1, x["descrizione_documento"], x["quantita_richiesta"], umx[x["unita"]], note_x.get(x["descrizione_documento"], ""), None])
ws.append([None, "--- CAVI E VIE CAVI ---"]); ws.cell(ws.max_row, 2).font = Font(italic=True)
for i, x in enumerate(r[6:10]):
    q = f'{x["quantita_richiesta"]} mt' if x["unita"] == "m" else x["quantita_richiesta"]
    ws.append([i + 7, x["descrizione_documento"], q, "" if x["unita"] == "m" else "nr", note_x.get(x["descrizione_documento"], ""), None])
ws.append([])
ws.append([11, r[10]["descrizione_documento"], 12, "nr", note_x[r[10]["descrizione_documento"]], None])
ws.append([]); ws.append([None, "Totale", None, None, None, "=SUM(F5:F17)"])
for col, w in zip("ABCDEF", (5, 34, 10, 6, 20, 10)): ws.column_dimensions[col].width = w
ws2 = wb.create_sheet("Note"); ws2["A1"] = "Consegna in cantiere. Contattare il capocantiere prima dello scarico."
wb.save(OUT / "rfq_03_distinta_excel.xlsx")
salva_atteso("rfq_03_distinta_excel", "rfq_03_distinta_excel.xlsx", "media",
             {"ambiente": "interno", "tipo_impianto": "industriale"}, r,
             [{"regola": "R04", "motivo": "Dispositivi modulari per 32 moduli in un centralino da 18"},
              {"regola": "R15", "motivo": "FG16OR16 3G2,5: 250 → 300 m; 5G4: 120 → 200 m"}],
             "Excel con celle unite, intestazione non sulla prima riga, righe separatore, unità miste ('nr', 'mt', '250 mt' nella cella quantità), un secondo foglio da ignorare, un articolo fuori listino.")

# =====================================================================
# RFQ 04 — ordine scansionato (difficile, OCR)
# =====================================================================
r = [
    riga("Centralino da parete IP40 12 moduli", 1, "pz", "QDX-CP40-12"),
    riga("Interruttore sezionatore 2P 63A", 1, "pz", "VOL-SZ2P-63"),
    riga("Magnetotermico 2P C32 6kA (linea box auto)", 1, "pz", "VOL-MT2P-C32-6"),
    riga("Differenziale puro 2P 25A 30mA tipo F (lavatrice)", 1, "pz", "VOL-ID2P-25-30F"),
    riga("Cavo FG16OR16 3G2,5 (linea box auto)", 50, "m", "CVX-FG16OR16-3G025"),
]
tmp = Path(tempfile.mkdtemp())
story = [Paragraph("IDRO-ELETTRICA VERDI di Paolo Verdi", H), Paragraph("Via Emilia 220 – Imola (BO)", SM), Spacer(1, 10),
         Paragraph("<b>ORDINE / RICHIESTA PREZZI</b> – Villetta sig. Neri", N), Paragraph("Data 05/11/2026", N), Spacer(1, 10)]
data = [["Pos.", "Descrizione", "Q.tà", "U.M."]] + [[str(i + 1), Paragraph(x["descrizione_documento"], N),
        str(x["quantita_richiesta"]), x["unita"]] for i, x in enumerate(r)]
story += [tabella(data, [12 * mm, 120 * mm, 18 * mm, 16 * mm]), Spacer(1, 14),
          Paragraph("Nota: la linea del box auto (magnetotermico 2P C32 + cavo 3G2,5) alimenta la colonnina di ricarica.", N),
          Spacer(1, 30), Paragraph("Timbro e firma ______________________", N)]
pdf(tmp / "orig.pdf", story)
subprocess.run(["pdftoppm", "-r", "150", "-png", "-singlefile", str(tmp / "orig.pdf"), str(tmp / "scan")], check=True)
img = Image.open(tmp / "scan.png").convert("L")
img = img.rotate(-1.6, resample=Image.BICUBIC, expand=True, fillcolor=235)
px = img.load(); w, h = img.size
for _ in range(int(w * h * 0.004)):  # puntini di rumore
    x, y = random.randrange(w), random.randrange(h); px[x, y] = random.randint(60, 160)
img = img.filter(ImageFilter.GaussianBlur(0.7))
img = ImageOps.autocontrast(img, cutoff=1).point(lambda v: min(255, int(v * 0.93 + 12)))
img.save(OUT / "rfq_04_scansione.pdf", "PDF", resolution=150)
salva_atteso("rfq_04_scansione", "rfq_04_scansione.pdf", "difficile",
             {"ambiente": "interno", "tipo_impianto": "residenziale"}, r,
             [{"regola": "R01", "motivo": "Cavo 3G2,5 (portata 31A) sulla linea protetta da magnetotermico C32"},
              {"regola": "R10", "motivo": "Linea colonnina di ricarica: verificare classe del differenziale a monte"},
              {"regola": "R15", "motivo": "Cavo 3G2,5: 50 → 100 m"}],
             "PDF senza testo (solo immagine), leggermente ruotato e sporco: richiede OCR o un modello con input immagine. Contiene un abbinamento cavo/interruttore descritto in una nota.")

# =====================================================================
# RFQ 05 — capitolato tecnico multipagina (difficile)
# =====================================================================
r = [
    riga("Centralino da parete in materiale isolante, 36 moduli DIN, grado di protezione IP65", 1, "pz", "QDX-CP65-36"),
    riga("Interruttore generale magnetotermico quadripolare, In = 40A, curva C, Pdi 10kA", 1, "pz", "VOL-MT4P-C40-10"),
    riga("Interruttori magnetotermici differenziali 1P+N, In 16A, Idn 0,03A, classe A", 3, "pz", "VOL-MTD1N-C16-30A",
         note="Idn 0,03A = 30mA: test di conversione unità."),
    riga("Interruttori magnetotermici tripolari 16A curva D per avviamento motori", 2, "pz", "VOL-MT3P-D16-10"),
    riga("Contattori tripolari categoria AC-3, In 12A, bobina 24Vac", 2, "pz", "FRT-CT3P-12-24"),
    riga("Limitatore di sovratensione (SPD) Tipo 1+2, configurazione 3P+N", 1, "pz", "VOL-SPD12-3PN",
         note="'Limitatore di sovratensione' = scaricatore."),
    riga("Cavo FG16R16 1x35 mm² – n. 4 conduttori da 40 m", 160, "m", "CVX-FG16R16-1X0350",
         note="Quantità da calcolare: 4 x 40 m = 160 m."),
    riga("Conduttore di protezione FS17 1x16 mm² giallo/verde", 40, "m", "CVX-FS17-160-GV"),
]
sp = lambda: Spacer(1, 6)
story = [Paragraph("COMUNE DI SAN LAZZARO DI SAVENA (fittizio)", SM),
         Paragraph("CAPITOLATO SPECIALE D'APPALTO – IMPIANTI ELETTRICI", H),
         Paragraph("Adeguamento impianto elettrico centrale termica – Scuola primaria \"G. Rodari\"", N), sp(),
         Paragraph("PARTE I – CONDIZIONI GENERALI", H2),
         Paragraph("Art. 1.1 – Oggetto dell'appalto. Il presente capitolato disciplina la fornitura e posa in opera dei materiali "
                   "necessari all'adeguamento dell'impianto elettrico della centrale termica. L'appaltatore è tenuto a "
                   "fornire materiali nuovi, di primaria marca, provvisti di marcatura CE e conformi alle norme vigenti.", N), sp(),
         Paragraph("Art. 1.2 – Oneri dell'appaltatore. Sono a carico dell'appaltatore il trasporto, lo scarico, "
                   "l'accatastamento in cantiere, lo smaltimento degli imballi e la redazione della dichiarazione di "
                   "conformità. I lavori dovranno essere eseguiti a scuola chiusa, nel periodo 22/12 – 06/01.", N), sp(),
         Paragraph("Art. 1.3 – Pagamenti. Il pagamento avverrà a 60 giorni data fattura fine mese, previo collaudo "
                   "con esito positivo. Non sono ammesse revisioni prezzi.", N),
         Paragraph("PARTE II – SPECIFICHE TECNICHE", H2),
         Paragraph("Art. 3.1 – Generalità. La centrale termica è un locale tecnico interno, non soggetto a rischio di "
                   "esplosione. La corrente di cortocircuito presunta nel punto di consegna è pari a 6kA.", N), sp(),
         Paragraph("Art. 3.2 – Quadro QE-CT. Il nuovo quadro sarà costituito da un centralino da parete in materiale "
                   "isolante, 36 moduli DIN, grado di protezione IP65, completo di portella trasparente. All'interno "
                   "dovranno essere installati:", N),
         Paragraph("a) n. 1 interruttore generale magnetotermico quadripolare, In = 40A, curva C, Pdi 10kA;<br/>"
                   "b) n. 3 interruttori magnetotermici differenziali 1P+N, In 16A, Idn 0,03A, classe A, per i circuiti "
                   "ausiliari e le prese di servizio;<br/>"
                   "c) n. 2 interruttori magnetotermici tripolari 16A curva D a protezione delle pompe di circolazione, "
                   "per tenere conto delle correnti di avviamento dei motori;<br/>"
                   "d) n. 2 contattori tripolari categoria AC-3, In 12A, bobina 24Vac, per il comando delle pompe;<br/>"
                   "e) n. 1 limitatore di sovratensione (SPD) Tipo 1+2, configurazione 3P+N.", N),
         PageBreak(),
         Paragraph("Art. 3.3 – Linea di alimentazione. La linea di alimentazione del quadro QE-CT dal quadro generale "
                   "sarà realizzata con cavi unipolari secondo la tabella seguente.", N), sp()]
data = [["Sigla", "Formazione", "Q.tà", "Note"],
        ["FG16R16", "1x35 mm²", "n. 4 conduttori da 40 m", "L1-L2-L3-N"],
        ["FS17", "1x16 mm² giallo/verde", "40 m", "Conduttore di protezione PE"]]
story += [tabella(data, [26 * mm, 42 * mm, 46 * mm, 50 * mm]), sp(),
          Paragraph("Art. 3.4 – Collaudi. Al termine dei lavori l'appaltatore eseguirà le verifiche strumentali "
                    "(continuità dei conduttori di protezione, resistenza di isolamento, prova dei differenziali) "
                    "redigendo apposito verbale.", N), sp(),
          Paragraph("Art. 3.5 – Documentazione. Dovranno essere consegnati lo schema unifilare aggiornato e le schede "
                    "tecniche di tutti i componenti installati.", N)]
pdf(OUT / "rfq_05_capitolato.pdf", story)
salva_atteso("rfq_05_capitolato", "rfq_05_capitolato.pdf", "difficile",
             {"ambiente": "interno", "icc_presunta_ka": 6, "tipo_impianto": "pubblico"}, r,
             [{"regola": "R15", "motivo": "FS17 1x16 giallo-verde: 40 → 100 m"}],
             "Documento lungo su più pagine con molto testo da ignorare (condizioni generali), articoli dentro elenchi puntati, sinonimi tecnici ('limitatore di sovratensione', 'classe A', 'Idn 0,03A'), una quantità da calcolare (4 x 40 m).")

# indice
idx = []
for p in sorted((OUT / "atteso").glob("*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    idx.append(f"| `{d['documento']}` | {d['difficolta']} | {len(d['righe'])} | {', '.join(a['regola'] for a in d['avvisi_attesi'])} |")
(OUT / "README.md").write_text(
    "# Richieste d'offerta di prova\n\nDocumenti finti (clienti e nomi inventati) per testare estrazione e matching.\n"
    "Per ogni documento, `atteso/<nome>.json` contiene le righe corrette (codice del listino e quantità) e gli avvisi "
    "che il motore regole deve generare. Lo script di valutazione della Fase 3 confronta l'output dell'IA con questi file.\n\n"
    "| Documento | Difficoltà | Righe | Avvisi attesi |\n|---|---|---|---|\n" + "\n".join(idx) + "\n\n"
    "Regole per la valutazione:\n- `codice_atteso: null` → la riga NON deve essere abbinata a nessun articolo.\n"
    "- `alternative_accettabili` → anche questi codici contano come corretti.\n", encoding="utf-8")
print("ok", [p.name for p in OUT.iterdir()])
