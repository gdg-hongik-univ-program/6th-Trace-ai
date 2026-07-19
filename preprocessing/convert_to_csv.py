import json
import csv
import os

INPUT_PATH = os.path.join(os.path.dirname(__file__), '라벨링데이터/수학_지식체계_데이터_세트_210611.json.part0')
OUT_DIR = os.path.dirname(__file__)

with open(INPUT_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

concepts = {}    # id -> concept row
chapters = {}    # id -> name
achievements = {}  # id -> name
relations = []   # (from_concept_id, to_concept_id)

for record in data.values():
    for concept in (record['fromConcept'], record['toConcept']):
        cid = concept['id']
        if cid not in concepts:
            chapter = concept.get('chapter', {})
            achievement = concept.get('achievement', {})
            ch_id = str(chapter.get('id', ''))
            ach_id = str(achievement.get('id', ''))

            concepts[cid] = {
                'id': cid,
                'name': concept.get('name', ''),
                'semester': concept.get('semester', ''),
                'description': concept.get('description', ''),
                'chapter_id': ch_id,
                'achievement_id': ach_id,
            }
            if ch_id:
                chapters[ch_id] = chapter.get('name', '')
            if ach_id:
                achievements[ach_id] = achievement.get('name', '')

    relations.append({
        'from_concept_id': record['fromConcept']['id'],
        'to_concept_id': record['toConcept']['id'],
    })

def write_csv(path, fieldnames, rows):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"저장: {path} ({len(rows)}행)")

write_csv(
    os.path.join(OUT_DIR, 'concepts.csv'),
    ['id', 'name', 'semester', 'description', 'chapter_id', 'achievement_id'],
    sorted(concepts.values(), key=lambda x: x['id']),
)

write_csv(
    os.path.join(OUT_DIR, 'chapters.csv'),
    ['id', 'name'],
    [{'id': k, 'name': v} for k, v in sorted(chapters.items())],
)

write_csv(
    os.path.join(OUT_DIR, 'achievements.csv'),
    ['id', 'name'],
    [{'id': k, 'name': v} for k, v in sorted(achievements.items())],
)

write_csv(
    os.path.join(OUT_DIR, 'relations.csv'),
    ['from_concept_id', 'to_concept_id'],
    relations,
)
