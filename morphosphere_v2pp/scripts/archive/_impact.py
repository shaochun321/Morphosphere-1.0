import sqlite3
from pathlib import Path

eng = Path('pipeline_engine.py').read_text(encoding='utf-8')
lines = eng.split('\n')
print(f'pipeline_engine.py: {len(lines)} lines total')

sections = {
    'imports_utils_helpers':   (1, 90,    'KEEP'),
    'write_envelope':          (90, 120,  'KEEP'),
    'write_cells':             (120, 200, 'KEEP - adapter interface unchanged'),
    'write_transport':         (200, 350, 'MODIFY - add OT option'),
    'write_hypotheses':        (350, 470, 'KEEP'),
    'write_xi':                (470, 530, 'KEEP'),
    'write_fhpms_rlis':        (530, 700, 'MODIFY - add feedback loop'),
    'write_legacy_layers':     (700, 830, 'KEEP'),
    'prx_triview_analysis':    (830, 1200,'REPLACE - softmax → EM'),
    'convergence':             (1200, 1277,'MODIFY - add real iteration'),
}

keep = 0; modify = 0; replace = 0
for name, (s, e, action) in sections.items():
    sz = e - s
    tag = action.split(' -')[0].strip()
    print(f'  {name:30s}: {sz:3d} lines  {action}')
    if tag == 'KEEP': keep += sz
    elif tag == 'MODIFY': modify += sz
    elif tag == 'REPLACE': replace += sz

total = keep + modify + replace
print(f'\nSummary:')
print(f'  KEEP unchanged:    {keep:4d} lines ({keep*100//total}%)')
print(f'  MODIFY (extend):   {modify:4d} lines ({modify*100//total}%)')
print(f'  REPLACE (rewrite): {replace:4d} lines ({replace*100//total}%)')

# DB tables
conn = sqlite3.connect('v37415_20260509_batch6.db')
tables = [t[0] for t in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
prx = [t for t in tables if 'v37415' in t]
fhpms = [t for t in tables if 'fhpms' in t or 'hebbian' in t.lower()]
transport = [t for t in tables if 'transport' in t]
untouched = [t for t in tables if t not in prx + fhpms + transport]
print(f'\nDatabase tables ({len(tables)} total):')
print(f'  PRX分析 (replace):     {len(prx):3d} tables')
print(f'  FHPMS/Hebbian (modify):{len(fhpms):3d} tables')
print(f'  Transport (modify):    {len(transport):3d} tables')
print(f'  Untouched:             {len(untouched):3d} tables ({len(untouched)*100//len(tables)}%)')

# Adapters
print(f'\nAdapter interface:')
print(f'  CellRecord dataclass:    KEEP (x,y,z,V_mean... all fields stay)')
print(f'  generate_cells(k):       KEEP (new adapter implements same interface)')
print(f'  make_envelope(k):        KEEP')
print(f'  Only change: ADD one new adapter class (AllenBrainAdapter)')
conn.close()
