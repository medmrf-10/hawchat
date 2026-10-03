#!/usr/bin/env python3
# يبني فهرس متون من matn_src/<dir> -> matn/<book>.jsonl {id,text,key}
import json,re,os,sys
DIAC=re.compile(r'[ً-ْٰـ]')
def norm(s):
    s=DIAC.sub('',s); s=re.sub(r'<[^>]+>',' ',s); s=re.sub(r'[^\w\s]',' ',s)
    for a,b in [('أ','ا'),('إ','ا'),('آ','ا'),('ى','ي'),('ة','ه'),('ؤ','و'),('ئ','ي')]: s=s.replace(a,b)
    return ' '.join(s.split())
AN={'٠':0,'١':1,'٢':2,'٣':3,'٤':4,'٥':5,'٦':6,'٧':7,'٨':8,'٩':9}
def anum(s): return int(''.join(str(AN[c]) if c in AN else c for c in s))
def build(src,out,book):
    full=' '.join(json.loads(l)['body'].replace('\r',' ').replace('\n',' ') for l in open(src+'/pages.jsonl'))
    full=re.sub(r'<span[^>]*id=toc-\d+>.*?</span>',' ',full)
    if book=='bukhari': parts=re.split(r'•\s*\[([٠-٩0-9]+)\]',full); step=2; off=1
    else: parts=re.split(r'(?<!\d)(\d{1,5})\s*-\s*\((\d{1,5})\)',full); step=3; off=2
    n=0; w=open(out,'w')
    i=1
    while i+step-1<len(parts):
        hid=anum(parts[i+step-1]) if step==2 else int(parts[i+1])
        body=parts[i+step] if step==2 else parts[i+2]
        i+=step
        body=re.sub(r'<[^>]+>',' ',body); body=' '.join(body.split())
        if len(body)<40 or hid>9000: continue
        w.write(json.dumps({'id':hid,'book':book,'text':body,'key':norm(body)[:120]},ensure_ascii=False)+'\n'); n+=1
    print(book,n)
if __name__=='__main__':
    src=sys.argv[1]  # matn_src root
    os.makedirs('matn',exist_ok=True)
    build(src+'/1167__صحيح-البخاري-ط-التأصيل','matn/bukhari.jsonl','bukhari')
    build(src+'/1481__صحيح-مسلم-ت-عبد-الباقي','matn/muslim.jsonl','muslim')
