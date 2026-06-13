# -*- coding: utf-8 -*-
"""Reconstrueix ca_ES.json a partir d'en_US.json + lots de traduccio tr_*.json.
Valida que cada traduccio preserva variables {x}, enllacos @:clau, plurals | i alternatives ::.
"""
import json, re, glob, os, sys

HERE = os.path.dirname(__file__)
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
EN = os.path.join(ROOT, 'i18n', 'locales', 'en_US.json')
OUT = os.path.join(ROOT, 'i18n', 'locales', 'ca_ES.json')

def load_translations():
    tr = {}
    for f in sorted(glob.glob(os.path.join(HERE, 'tr_*.json'))):
        data = json.load(open(f, encoding='utf-8'))
        tr.update(data)
    return tr

PLACEHOLDER = re.compile(r'\{[^}]+\}')
# @:key or @.modifier:key  (key may contain letters, digits, dots, underscores)
LINK = re.compile(r'@(?:\.[a-z]+)?:[A-Za-z0-9_.]+')

LINKKEY = re.compile(r'@(?:\.[a-z]+)?:([A-Za-z0-9_.]+)')

def validate(src, dst, valid_keys):
    errs = []
    sp = sorted(PLACEHOLDER.findall(src))
    dp = sorted(PLACEHOLDER.findall(dst))
    if sp != dp:
        errs.append('CRITIC: variables {} difereixen: %r vs %r' % (sp, dp))
    # cada enllac @: de la traduccio ha d'apuntar a una clau existent
    for k in LINKKEY.findall(dst):
        if k not in valid_keys:
            errs.append('enllac @:%s no existeix a en_US' % k)
    if src.count('|') != dst.count('|'):
        errs.append('avis: nombre de | (plurals) difereix: %d vs %d' % (src.count('|'), dst.count('|')))
    if src.count('::') != dst.count('::'):
        errs.append('avis: nombre de :: (alternatives) difereix: %d vs %d' % (src.count('::'), dst.count('::')))
    return errs

def collect_keys(o, p='', out=None):
    if out is None: out = set()
    if isinstance(o, dict):
        for k, v in o.items():
            np = (p + '.' + k) if p else k
            out.add(np)
            collect_keys(v, np, out)
    return out

def main():
    en = json.load(open(EN, encoding='utf-8'))
    valid_keys = collect_keys(en)
    tr = load_translations()
    missing = []
    errors = []
    def walk(o, p=''):
        if isinstance(o, dict):
            return {k: walk(v, (p + '.' + k) if p else k) for k, v in o.items()}
        if isinstance(o, list):
            return [walk(v, p + '[' + str(i) + ']') for i, v in enumerate(o)]
        src = o
        if src in tr and tr[src] != '':
            dst = tr[src]
            for e in validate(src, dst, valid_keys):
                errors.append((p, e, src, dst))
            return dst
        missing.append((p, src))
        return src
    out = walk(en)
    with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write('\n')
    total_leaves = len(missing) + (count_leaves(en) - len(missing))
    tl = count_leaves(en)
    print('Cadenes totals (fulles):', tl)
    print('Tradudes:', tl - len(missing), '(%.1f%%)' % (100*(tl-len(missing))/tl))
    print('Pendents:', len(missing))
    if errors:
        print('\n*** ERRORS DE VALIDACIO:', len(errors))
        for p, e, s, d in errors[:60]:
            print('  [%s] %s\n      SRC=%r\n      DST=%r' % (p, e, s, d))
    if '--missing' in sys.argv:
        print('\n--- PENDENTS ---')
        for p, s in missing:
            print('%s\t%s' % (p, s))

def count_leaves(o):
    if isinstance(o, dict): return sum(count_leaves(v) for v in o.values())
    if isinstance(o, list): return sum(count_leaves(v) for v in o)
    return 1

if __name__ == '__main__':
    main()
