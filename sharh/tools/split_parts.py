#!/usr/bin/env python3
# يقطّع كتاب شرح إلى أجزاء على حدود الشروح (toc) — بلا تداخل حرف واحد
# استعمال: python3 split_parts.py <book_dir> <out_dir>
import json,re,os,sys
def main(D,OUT):
    os.makedirs(OUT,exist_ok=True)
    pages={}
    for l in open(f'{D}/pages.jsonl'):
        d=json.loads(l); pages[d['page_id']]=d['body'].replace('\r','\n')
    toc=[json.loads(l) for l in open(f'{D}/toc.jsonl')]
    toc.sort(key=lambda t:t['page_id'])
    ids=sorted(pages)
    def strip(s):
        s=re.sub(r'<span[^>]*id=toc-\d+>.*?</span>','',s)
        s=re.sub(r'<[^>]+>','',s)
        return '\n'.join(x for x in s.split('\n') if x.strip())
    made=0
    for i,t in enumerate(toc):
        start=t['page_id']; end=toc[i+1]['page_id'] if i+1<len(toc) else None
        body=[p for pid,p in ((pid,pages[pid]) for pid in ids) if pid>=start and (not end or pid<end)]
        text=strip('\n'.join(body))
        if len(text)<30: continue
        rec={'part':made,'book':os.path.basename(D),'shamela_title_id':t.get('shamela_title_id'),'title':t['title_text'],'text':text}
        open(f'{OUT}/{made:03d}.jsonl','w',encoding='utf8').write(json.dumps(rec,ensure_ascii=False)+'\n'); made+=1
    print('parts:',made)
if __name__=='__main__': main(sys.argv[1],sys.argv[2])
