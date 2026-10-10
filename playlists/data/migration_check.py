#!/usr/bin/env python3
# متتبّع نقل السلاسل إلى «إرث» — يولّد playlists/data/migration.json
# السلسلة تُحسب منقولة فقط باكتمال طبقاتها الأربع كلها: تفريغ+محاذاة+تلخيص+أسئلة
import json, os, glob

HUB = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IRTH = os.environ.get('IRTH_REPO', '/home/ubuntu/irth')

# slug مجلد الدروس في هب ← معرّف السلسلة في إرث
SLUG2IRTH = {
    'bouti-sira': 'fi9hElsirah', 'bouti-rihla': 'ri7latEl5oloud',
    'bouti-khutab-2012': '5o6ab', 'bouti-yaqiniyyat': 'kobraElya9inyat',
    'bouti-ulum-quran': '3oloumEl9or1n', 'bouti-hubb': 'al7obFiEl9or1n',
    'bouti-tarikh': 'tari5Eltachri3', 'bouti-yaghalitun': 'yoghalitonak',
    'bouti-aqeeda': 'dawraFiEl3a9ida',
    'alsayed-mut-628': 'elsiraLilmosli7in', 'alsayed-mut-636': 'el6ari9IlaBaytElmaqdis',
    'alsayed-mut-660': 'elommaBaynI7tilayn', 'alsayed-mut-651': 'siyarWa3ibar',
    'alsayed-mut-645': 'tajaribI9la7iya', 'alsayed-mut-653': 'yawmElfur9an',
    'alsayed-mut-671': 'albina2Eltazkawi', 'alsayed-mut-652': 'sonanIlahiya',
    'alsayed-mut-675': 'tadabburElanfal', 'alsayed-mut-630': 'tari5ElfikrElgharbi',
    'alsayed-mut-687': 'ma9asidElssowar', 'alsayed-mut-659': 'eltazkiaLilmosli7in',
    'alsayed-mut-656': 'riyadElsali7in',
    'aouni-ibada': 'aouniIbada', 'aouni-jabir': 'aouniJabir', 'aouni-mousiqa': 'aouniMousiqa',
    'abdelwahid-tawassul': 'abdelwahidTawassul',
    'abdelmonem-juz30': 'abdelmonemJuz30',
    'alasri-arbaa': 'alasriArbaa',
    'fadel-juz30': 'fadelJuz30', 'fadel-dawra': 'fadelDawra', 'fadel-farsh': 'fadelFarsh',
    'alamri-adab-murid': 'alamriAdabMurid', 'alamri-barahin-kitab': 'alamriBarahinKitab',
    'alamri-barahin-muqtatafat': 'alamriBarahinMuqtatafat', 'alamri-barahin-sharh': 'alamriBarahinSharh',
    'alamri-bath': 'alamriBath', 'alamri-durus-amma': 'alamriDurusAmma',
    'alamri-falsafa-din': 'alamriFalsafaDin', 'alamri-falsafa-haditha': 'alamriFalsafaHaditha',
    'alamri-hisam': 'alamriHisam', 'alamri-iqtisad': 'alamriIqtisad',
    'alamri-liqaat': 'alamriLiqaat', 'alamri-manhaj-iman': 'alamriManhajIman',
    'alamri-mayar-ilm': 'alamriMayarIlm', 'alamri-mughni': 'alamriMughni',
    'alamri-muhadara': 'alamriMuhadara', 'alamri-nasafiyya': 'alamriNasafiyya',
    'alamri-qawaid-tasawwuf': 'alamriQawaidTasawwuf', 'alamri-qushayriyya': 'alamriQushayriyya',
    'alamri-sulam': 'alamriSulam',
}

def main():
    stats = json.load(open(os.path.join(HUB, 'playlists/data/sheikh_stats.json')))
    out = {}
    for sh, st in stats.items():
        if sh == '_meta' or not isinstance(st, dict):
            continue
        for r in st.get('rows', []):
            rid = r.get('id')
            if not rid:
                continue
            slug = r.get('sSlug') or r.get('ld') or ''
            tot = r.get('rtt') or r.get('ytn') or 0
            txt = r.get('rdn') or 0
            al = r.get('wan') or 0
            sm = r.get('sun') or 0
            q = 0
            sid = SLUG2IRTH.get(slug)
            if sid:
                q = len(glob.glob(os.path.join(IRTH, 'content/tube', sid + '-*/questions.json')))
            done = bool(tot) and txt >= tot and al >= tot and sm >= tot and q >= tot
            out[rid] = {'t': tot, 'txt': txt, 'al': al, 'sm': sm, 'q': q, 'done': done}
    dst = os.path.join(HUB, 'playlists/data/migration.json')
    json.dump({'v': 1, 'rows': out}, open(dst, 'w'), ensure_ascii=False)
    done = [k for k, v in out.items() if v['done']]
    print('rows:', len(out), '| migrated:', len(done))
    for k in done:
        print('  ✅', k)

if __name__ == '__main__':
    main()
