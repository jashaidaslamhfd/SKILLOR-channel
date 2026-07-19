"""Génère le catalogue France-first de 500 sujets « Réflexes du corps ».

Les sujets sont conçus pour un public francophone : phénomènes quotidiens,
formulations françaises naturelles et aucune promesse médicale.
"""
from __future__ import annotations
import json
from pathlib import Path

PHENOMENA = [
    ("Paupière qui saute", "une paupière qui tressaille sans raison", "ŒIL QUI SAUTE ?"),
    ("Ventre qui gargouille", "un ventre qui gargouille sans faim", "BRUIT DU VENTRE ?"),
    ("Chair de poule", "la chair de poule qui apparaît soudainement", "POURQUOI DES FRISSONS ?"),
    ("Oreilles qui sifflent", "des oreilles qui sifflent dans le silence", "ÇA SIFFLE ?"),
    ("Hoquet soudain", "un hoquet qui commence brusquement", "POURQUOI LE HOQUET ?"),
    ("Nez qui coule", "un nez qui coule quand on pleure", "NEZ QUI COULE ?"),
    ("Mains fripées", "des mains qui se fripent dans l'eau", "MAINS FRIPÉES ?"),
    ("Frissons de stress", "le corps qui frissonne sous le stress", "POURQUOI JE TREMBLE ?"),
    ("Rougir", "le visage qui rougit par gêne", "POURQUOI JE ROUGIS ?"),
    ("Bâillement contagieux", "un bâillement qui se transmet", "POURQUOI ON BÂILLE ?"),
    ("Larmes de rire", "les yeux qui pleurent quand on rit", "LARMES DE RIRE ?"),
    ("Gel du cerveau", "un mal de tête après un aliment froid", "CERVEAU GELÉ ?"),
    ("Fourmillements", "des fourmillements après une mauvaise position", "DES FOURMIS ?"),
    ("Pied endormi", "un pied qui s'endort", "PIED ENDORMI ?"),
    ("Muscle qui saute", "un muscle qui tressaille tout seul", "MUSCLE QUI SAUTE ?"),
    ("Sursaut du sommeil", "le corps qui sursaute en s'endormant", "SURSAUT DU SOMMEIL ?"),
    ("Voix qui tremble", "la voix qui tremble par nervosité", "VOIX QUI TREMBLE ?"),
    ("Mains froides", "des mains froides sous le stress", "MAINS FROIDES ?"),
    ("Oreilles chaudes", "des oreilles qui deviennent chaudes", "OREILLES CHAUDES ?"),
    ("Mains moites", "les paumes qui transpirent par nervosité", "MAINS MOITES ?"),
    ("Nœud au ventre", "une sensation de nœud au ventre avant un moment important", "NŒUD AU VENTRE ?"),
    ("Boule dans la gorge", "une boule dans la gorge sous l'émotion", "BOULE À LA GORGE ?"),
    ("Bouche sèche", "la bouche qui devient sèche par nervosité", "BOUCHE SÈCHE ?"),
    ("Mâchoire qui craque", "la mâchoire qui craque en mâchant", "MÂCHOIRE QUI CRAQUE ?"),
    ("Genoux qui craquent", "les genoux qui craquent en bougeant", "GENOUX QUI CRAQUENT ?"),
    ("Ventre qui se serre", "le ventre qui se serre lors d'une peur", "VENTRE SERRÉ ?"),
    ("Cœur qui s'emballe", "le cœur qui s'emballe sous le stress", "CŒUR QUI S'EMBALLE ?"),
    ("Vertige au lever", "un vertige après s'être levé", "VERTIGE AU LEVER ?"),
    ("Éternuement lumineux", "un éternuement face à une lumière vive", "LUMIÈRE = ÉTERNUEMENT ?"),
    ("Corps flottants", "des corps flottants visibles dans la lumière", "TACHES DEVANT LES YEUX ?"),
    ("Vibration fantôme", "la sensation d'une vibration de téléphone imaginaire", "VIBRATION FANTÔME ?"),
    ("Chanson en boucle", "une chanson qui reste dans la tête", "CHANSON BLOQUÉE ?"),
    ("Déjà-vu", "un déjà-vu étrangement familier", "DÉJÀ-VU ?"),
    ("Trou de mémoire", "oublier pourquoi on entre dans une pièce", "POURQUOI SUIS-JE ICI ?"),
    ("Prénom oublié", "oublier un prénom juste après l'avoir entendu", "PRÉNOM OUBLIÉ ?"),
    ("Souvenirs nocturnes", "des souvenirs gênants qui reviennent le soir", "POURQUOI J'Y REPENSE ?"),
    ("Réveil avant l'alarme", "se réveiller avant son réveil", "AVANT LE RÉVEIL ?"),
    ("Battements entendus", "entendre son cœur battre la nuit", "J'ENTENDS MON CŒUR ?"),
    ("Horloge de la faim", "avoir faim à la même heure chaque jour", "FAIM ENCORE ?"),
    ("Musique et humeur", "la musique qui change vite l'humeur", "MUSIQUE = HUMEUR ?"),
    ("Silence gênant", "le silence qui devient inconfortable", "SILENCE GÊNANT ?"),
    ("Entendre son nom", "le cerveau qui remarque son propre prénom", "J'AI ENTENDU MON NOM ?"),
    ("Temps accéléré", "le temps qui semble passer plus vite en vieillissant", "LE TEMPS ACCÉLÈRE ?"),
    ("Sommeil profond", "le cerveau qui a besoin de sommeil profond", "SOMMEIL PROFOND ?"),
    ("Nuances de vert", "voir davantage de nuances de vert", "POURQUOI LE VERT ?"),
    ("Stress et mémoire", "le stress qui rend la mémoire moins claire", "STRESS ET MÉMOIRE ?"),
    ("Frisson de froid", "frissonner quand on a froid", "FRISSON DE FROID ?"),
    ("Corps lourd", "le corps lourd quand on est fatigué", "CORPS LOURD ?"),
    ("Corps figé", "le corps qui se fige quand on a peur", "CORPS FIGÉ ?"),
    ("Rêve oublié", "un rêve qui disparaît au réveil", "RÊVE DISPARU ?"),
]
ANGLES = [
    "Pourquoi {phenomenon} arrive", "La science derrière {phenomenon}",
    "Ce qui se passe quand {phenomenon} arrive", "Pourquoi {phenomenon} peut sembler étrange",
    "Ce qu'il faut comprendre sur {phenomenon}", "Les déclencheurs possibles de ce phénomène : {phenomenon}",
    "Pourquoi le cerveau remarque {phenomenon}", "Le signal du corps lié à {phenomenon}",
    "Ce qui change lorsque {phenomenon} arrive", "Pourquoi {phenomenon} semble soudain",
]
def build_catalogue() -> list[dict]:
    records=[]
    for number, (label, phenomenon, thumbnail) in enumerate((item for item in PHENOMENA for _ in ANGLES), 1):
        angle=ANGLES[(number-1)%len(ANGLES)]
        records.append({"series_number":number,"series_title":label,"topic":phenomenon,"angle":angle.format(phenomenon=phenomenon),"thumbnail_text":thumbnail,"pillar":"reflexes_du_corps"})
    assert len(records)==500
    return records
if __name__ == '__main__':
    target=Path(__file__).resolve().parents[1]/'data'/'body_glitch_topics.json'
    target.write_text(json.dumps(build_catalogue(),ensure_ascii=False,indent=2),encoding='utf-8')
    print(f"500 sujets français écrits dans {target}")
