import asyncio,json,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(OUT/'tooling'))
import edge_tts
CUTS=[
(1,0,7,'海草や海藻が育つ、藻場。調査には、撮った場所が大切です。','海草や海藻が育つ、もば。調査には、撮った場所が大切です。'),
(2,7,14,'でも水中では、GPSが使いにくく、海藻も揺れてしまいます。','でも水中では、ジーピーエスが使いにくく、海藻も揺れてしまいます。'),
(3,14,19,'光と音を組み合わせる、AquaBeacon。','光とおとを組み合わせる、アクアビーコン。'),
(4,19,28,'水上の装置から音を送り、届くまでの時間で、水中の装置までの距離を測ります。','水上の装置からおとを送り、届くまでの時間で、水中の装置までの距離を測ります。'),
(5,28,36,'水中のライトを、水上のカメラで捉え、方向を測ります。','水中のライトを、水上のカメラで捉え、方向を測ります。'),
(6,36,46,'距離と方向、水上のGPSから、水中の位置を推定。撮った映像を、地図につなげます。','距離と方向、水上のジーピーエスから、水中の位置を推定。撮った映像を、地図につなげます。'),
(7,46,54,'機体の製作と実験を重ね、地図づくりに向けて、開発を進めています。','機体の製作と実験を重ね、地図づくりに向けて、開発を進めています。'),
(8,54,60,'藻場を調べる人たちへ。AquaBeacon。','もばを調べる人たちへ。アクアビーコン。')]
async def main():
    out=[]
    manifest=OUT/'narration_script.json'
    old={x['cut']:x for x in json.loads(manifest.read_text(encoding='utf-8'))} if manifest.exists() else {}
    for i,start,end,text,spoken in CUTS:
        path=OUT/f'cut_{i:02}_raw.mp3'
        m= {'cut':i,'start':start,'end':end,'text':text,'spoken_text':spoken,'voice':'ja-JP-NanamiNeural','rate':'+0%','raw_file':path.name,'boundaries':[]}
        if not path.exists() or old.get(i,{}).get('spoken_text')!=spoken:
            comm=edge_tts.Communicate(spoken,'ja-JP-NanamiNeural',rate='+0%',volume='+0%',pitch='+0Hz')
            with path.open('wb') as f:
                async for chunk in comm.stream():
                    if chunk['type']=='audio':f.write(chunk['data'])
                    elif chunk['type'] in ('WordBoundary','SentenceBoundary'): m['boundaries'].append({k:v for k,v in chunk.items() if k!='type'})
            print(f'created {path.name}',flush=True)
        else:
            m=old[i]
        out.append(m)
        (OUT/'narration_script.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
asyncio.run(main())
