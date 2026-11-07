import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open(r'C:\Users\Kumar\.gemini\antigravity\brain\7663b64b-1423-42e8-8f1b-3774b48f9709\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('step_index') == 8254:
            print(obj.get('content'))
            break
