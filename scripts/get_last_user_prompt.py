import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

last_user = None
with open(r'C:\Users\Kumar\.gemini\antigravity\brain\7663b64b-1423-42e8-8f1b-3774b48f9709\.system_generated\logs\transcript.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        obj = json.loads(line)
        if obj.get('type') == 'USER_INPUT':
            last_user = obj

if last_user:
    print(f"LAST USER INPUT AT STEP {last_user.get('step_index')}:")
    print(last_user.get('content'))
else:
    print("No USER_INPUT found.")
