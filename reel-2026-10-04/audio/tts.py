import os
import soundfile as sf, numpy as np, json, sys
from kokoro_onnx import Kokoro
k = Kokoro(os.environ.get("KOKORO_DIR","models")+"/kokoro-v1.0.onnx", os.environ.get("KOKORO_DIR","models")+"/voices-v1.0.bin")
lines = [
 ("hook1","Founders don't run businesses."),
 ("hook2","They run errands."),
 ("l1a","Answer DMs."),("l1b","Send invoices."),("l1c","Chase leads."),
 ("l2a","That is not leadership."),
 ("l2b","That is admin, with a nicer title."),
 ("l3","Every errand hour is an hour not spent growing."),
 ("l4a","Automate the repeats."),
 ("l4b","Keep the decisions."),
 ("q","Be honest. What is your biggest errand right now?"),
]
voice = sys.argv[1] if len(sys.argv)>1 else "af_heart"
speed = float(sys.argv[2]) if len(sys.argv)>2 else 0.95
import os; os.makedirs("audio/vo",exist_ok=True)
meta={}
for key,text in lines:
    s, sr = k.create(text, voice=voice, speed=speed, lang="en-us")
    # trim silence
    a=np.abs(s); idx=np.where(a>0.01)[0]
    s=s[max(0,idx[0]-int(.02*sr)):idx[-1]+int(.06*sr)]
    sf.write(f"audio/vo/{key}.wav", s, sr)
    meta[key]=round(len(s)/sr,3)
print(json.dumps(meta)); json.dump(meta,open("audio/vo/durations.json","w"))
