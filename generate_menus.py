#!/usr/bin/env python3
# generate_menus.py — GitHub Actions : rotation semaine + génération via Groq (free)
# Nécessite : GROQ_API_KEY en variable d'environnement (GitHub Secret)

import os, re, sys, requests
from datetime import date

GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_MODEL   = 'llama-3.3-70b-versatile'  # gratuit, 100k tokens/jour

SAISONS = {
    'printemps': {'mois':[3,4,5],  'label':'Printemps', 'legumes':'asperges, radis, épinards, petits pois, fèves, brocoli, carottes nouvelles, poireaux, laitue',             'fruits':'fraises, rhubarbe, cerises'},
    'ete':       {'mois':[6,7,8],  'label':'Été',       'legumes':'courgettes, tomates, poivrons, aubergines, haricots verts, maïs, fenouil',                                  'fruits':'pêches, abricots, framboises, myrtilles, pastèque, melons, prunes'},
    'automne':   {'mois':[9,10,11],'label':'Automne',   'legumes':'courge butternut, potiron, champignons, poireaux, chou-fleur, brocoli, betterave, patate douce',            'fruits':'pommes, poires, raisins, figues, kaki'},
    'hiver':     {'mois':[12,1,2], 'label':'Hiver',     'legumes':'poireaux, choux, endives, navets, carottes, épinards, mâche',                                               'fruits':'agrumes, kiwi, pommes, poires'},
}

def get_saison():
    m = date.today().month
    for v in SAISONS.values():
        if m in v['mois']:
            return v
    return SAISONS['hiver']

def extract_semaine_str(content, varname):
    """Extrait la chaîne JS du tableau const semaineX=[...]"""
    pattern = rf'const {varname}\s*=\s*(\[.*?\]);'
    m = re.search(pattern, content, re.DOTALL)
    return m.group(1) if m else None

def get_meal_names(js_array_str):
    if not js_array_str:
        return []
    return list(set(re.findall(r"nom:'([^']+)'", js_array_str)))

def build_prompt(noms_a_eviter, saison):
    today = date.today().strftime('%d/%m/%Y')
    return f"""Tu es un assistant culinaire expert en nutrition. Génère exactement 7 jours de menus familiaux.
Date : {today}. Saison : {saison['label']}.
Légumes de saison : {saison['legumes']}.
Fruits de saison : {saison['fruits']}.

═══ PROFIL FAMILLE ═══
- 2 adultes (Elle + Lui) + 2 enfants <10 ans
- Lundi→Vendredi midi : portions:'2 adultes'
- Lundi→Vendredi soir : portions:'4 pers.'
- Samedi + Dimanche : portions:'4 pers.' toute la journée

═══ PRÉFÉRENCES ═══
- Elle n'aime pas : concombre, fromage bleu
- Lui n'aime pas : fromage de chèvre, fromage de brebis, fromage bleu
- Enfants n'aiment pas : le poisson
- Poisson UNIQUEMENT au déjeuner (midi adultes), JAMAIS le soir
- Féculents : riz complet, riz basmati, pâtes complètes UNIQUEMENT
- Collation soir adultes : chocolat noir 70%+ (15-20g)
- Petit-déjeuner : skyr, flocons d'avoine, yaourt fruits mixé, beurre de cacahuète, amandes, noix

═══ CONTRAINTES ═══
- Repas semaine : < 20 minutes · Week-end : jusqu'à 40 minutes
- Budget total < 80€/semaine
- Max 3 repas viande rouge, max 2 repas poisson (midi seul), max 4 repas poulet
- 80% légumes/fruits de saison

═══ QUANTITÉS (base 1 adulte) ═══
- Viande/poisson max 150g | Féculents max 80g cru | Légumes max 150g
- Oeufs : écrire "X pièces" (ex: "Oeufs 2 pièces")
- Apostrophes : toujours \\' (ex: "dans l\\'huile")
- Tomates : distinguer "Tomates 100g" / "Tomates cerises 100g" / "Tomates concassées 100g"

═══ MACROS CIBLES (base 1 adulte) ═══
Elle : 1520 kcal/j — 30% P / 40% G / 30% L
Lui  : 1720 kcal/j — 30% P / 40% G / 30% L

═══ REPAS DES 2 DERNIÈRES SEMAINES À NE PAS RÉPÉTER ═══
{' | '.join(noms_a_eviter)}

═══ FORMAT EXACT D'UN REPAS ═══
{{moment:'Petit-déjeuner',nom:'Nom du plat',kcal:350,p:20,g:40,l:10,portions:'2 adultes',ings:['Ingrédient 100g'],steps:['Étape 1.'],note:''}}

5 MOMENTS OBLIGATOIRES PAR JOUR :
1. Petit-déjeuner  2. Déjeuner  3. Collation  4. Dîner  5. Collation soir

GÉNÈRE UNIQUEMENT le bloc JS suivant, SANS texte avant ni après, SANS markdown :

const semaine2=[
  {{f:[5 repas lundi elle],m:[5 repas lundi lui]}},
  {{f:[5 repas mardi elle],m:[5 repas mardi lui]}},
  {{f:[5 repas mercredi elle],m:[5 repas mercredi lui]}},
  {{f:[5 repas jeudi elle],m:[5 repas jeudi lui]}},
  {{f:[5 repas vendredi elle],m:[5 repas vendredi lui]}},
  {{f:[5 repas samedi elle],m:[5 repas samedi lui]}},
  {{f:[5 repas dimanche elle],m:[5 repas dimanche lui]}},
];"""

def call_groq(prompt):
    r = requests.post(
        'https://api.groq.com/openai/v1/chat/completions',
        headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
        json={'model': GROQ_MODEL, 'messages': [{'role': 'user', 'content': prompt}],
              'temperature': 0.35, 'max_tokens': 8000},
        timeout=120
    )
    r.raise_for_status()
    return r.json()['choices'][0]['message']['content']

def parse_and_validate(raw):
    cleaned = raw.replace('```javascript','').replace('```js','').replace('```','').strip()
    start = cleaned.find('const semaine2=[')
    if start == -1:
        raise ValueError('Bloc "const semaine2=[" introuvable')
    extracted = cleaned[start:]
    last = extracted.rfind('];')
    if last != -1:
        extracted = extracted[:last+2]
    nb_jours = extracted.count('{f:[')
    if nb_jours < 7:
        raise ValueError(f'Seulement {nb_jours} jours trouvés (7 requis)')
    return extracted

def build_output(sem1_str, sem2_str):
    return (
        '// ╔══════════════════════════════════════════════════════════════╗\n'
        '// ║  DONNÉES MENUS — généré automatiquement chaque mardi        ║\n'
        '// ╚══════════════════════════════════════════════════════════════╝\n\n'
        '// ── DONNÉES SEMAINE 1 ──────────────────────────────────────────\n'
        f'const semaine1={sem1_str}\n\n'
        f'{sem2_str}\n\n'
        'const semaines=[semaine1, semaine2];\n'
        "const semaineLabels=['Semaine en cours','Semaine suivante'];\n"
    )

def main():
    if not GROQ_API_KEY:
        print('ERREUR: GROQ_API_KEY non défini — ajouter ce secret dans les paramètres du repo GitHub')
        sys.exit(1)

    with open('menus_data.js', 'r', encoding='utf-8') as f:
        content = f.read()

    sem1_str = extract_semaine_str(content, 'semaine1')
    sem2_str = extract_semaine_str(content, 'semaine2')

    if not sem1_str:
        print('ERREUR: semaine1 introuvable dans menus_data.js')
        sys.exit(1)

    noms1 = get_meal_names(sem1_str)
    noms2 = get_meal_names(sem2_str)
    noms_a_eviter = list(set(noms1 + noms2))

    print(f'Semaine1 : {len(noms1)} repas | Semaine2 : {len(noms2)} repas')
    print(f'Rotation : semaine2 → semaine1 | Génération nouvelle semaine2')
    print(f'Saison : {get_saison()["label"]}')

    # Rotation : la semaine2 actuelle devient la nouvelle semaine1
    new_sem1 = sem2_str if sem2_str else sem1_str

    prompt = build_prompt(noms_a_eviter, get_saison())

    print('Appel Groq API...')
    last_err = None
    for attempt in range(3):
        try:
            raw = call_groq(prompt)
            new_sem2 = parse_and_validate(raw)
            print(f'✅ Génération OK (tentative {attempt+1})')
            break
        except Exception as e:
            last_err = e
            print(f'Tentative {attempt+1} échouée : {e}')
    else:
        print(f'ERREUR : échec après 3 tentatives — {last_err}')
        sys.exit(1)

    output = build_output(new_sem1, new_sem2)
    with open('menus_data.js', 'w', encoding='utf-8') as f:
        f.write(output)

    print('✅ menus_data.js mis à jour avec rotation semaine')

if __name__ == '__main__':
    main()
