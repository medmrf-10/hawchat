#!/usr/bin/env python3
"""align_to_transcript.py <audio> <transcript.txt> <out.json>
Forced-align a KNOWN transcript to audio via faster-whisper word timestamps
+ difflib mapping. Output: {"w":[[word,start,end,seg],...]}
Also caches raw whisper output at <out>.wwords.json for reuse."""
import sys, json, re, os, difflib
from faster_whisper import WhisperModel

DIAC = re.compile(r'[ً-ْٰـ]')
PUNCT = re.compile(r'[^\w\s]', re.UNICODE)

def norm(w):
    w = DIAC.sub('', w)
    w = PUNCT.sub('', w)
    w = w.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    w = w.replace('ى','ي').replace('ة','ه').replace('ؤ','و').replace('ئ','ي')
    return w.strip()

def whisper_words(audio, cache):
    if os.path.exists(cache):
        return json.load(open(cache, encoding='utf8'))
    model = WhisperModel('small', device='cpu', compute_type='int8', cpu_threads=3)
    segs, _ = model.transcribe(audio, language='ar', word_timestamps=True,
                             beam_size=3, vad_filter=True)
    ww = []
    for si, seg in enumerate(segs):
        for w in (seg.words or []):
            t = w.word.strip()
            if t:
                ww.append({'t': t, 'n': norm(t), 's': round(w.start,2), 'e': round(w.end,2), 'seg': si})
    json.dump(ww, open(cache,'w',encoding='utf8'), ensure_ascii=False)
    return ww

def main(audio, txt_path, out_path):
    cache = out_path + '.wwords.json'
    disp_words = open(txt_path, encoding='utf8').read().split()
    wwords = whisper_words(audio, cache)
    a = [norm(w) for w in disp_words]
    b = [w['n'] for w in wwords]
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    out = [{'t': dw, 's': None, 'e': None, 'seg': -1} for dw in disp_words]
    for blk in sm.get_matching_blocks():
        for k in range(blk.size):
            w = wwords[blk.b + k]
            out[blk.a + k].update(s=w['s'], e=w['e'], seg=w['seg'])
    n = len(out); matched = sum(1 for x in out if x['s'] is not None)
    for i, x in enumerate(out):
        if x['s'] is not None: continue
        j = i-1
        while j >= 0 and out[j]['s'] is None: j -= 1
        k = i+1
        while k < n and out[k]['s'] is None: k += 1
        s0 = out[j]['e'] if j >= 0 else 0.0
        e0 = out[k]['s'] if k < n else s0 + 0.4
        span = max(e0 - s0, 0.15)
        frac = (i - j) / (k - j) if k > j else 0.5
        x['s'] = round(s0 + span*frac, 2)
        x['e'] = round(x['s'] + 0.15, 2)
        # inherit seg from nearest matched neighbour for phrase grouping
        x['seg'] = out[j]['seg'] if j >= 0 else (out[k]['seg'] if k < n else 0)
    # drop -1 seg leftovers (unmatchable leading words)
    lastseg = 0
    for x in out:
        if x['seg'] < 0: x['seg'] = lastseg
        else: lastseg = x['seg']
    cov = matched/n if n else 0
    words = [[x['t'], x['s'], x['e'], x['seg']] for x in out]
    json.dump({'cov': round(cov,3), 'w': words}, open(out_path,'w',encoding='utf8'), ensure_ascii=False)
    print(out_path, 'words', len(words), 'coverage', f'{cov:.1%}')

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
