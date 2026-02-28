import json
import sys
import urllib.request
import subprocess

def get_ollama_models():
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')[1:]
        return [line.split()[0] for line in lines if line]
    except:
        return ["qwen2.5-coder:32b"]

def ollama_generate(prompt, model):
    url = "http://localhost:11434/api/generate"
    data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())["response"]

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line: break
            request = json.loads(line)
            if request.get("method") == "list_tools":
                models = get_ollama_models()
                tools = []
                for m in models:
                    safe_name = m.replace(":", "_").replace(".", "_").replace("-", "_")
                    tools.append({
                        "name": f"ollama_{safe_name}",
                        "description": f"Use local model {m} for reasoning",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"prompt": {"type": "string"}},
                            "required": ["prompt"]
                        }
                    })
                response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {"tools": tools}}
            elif request.get("method") == "call_tool":
                tool_name = request["params"]["name"]
                prompt = request["params"]["arguments"]["prompt"]
                # Find which model matches this tool
                models = get_ollama_models()
                target_model = "qwen2.5-coder:32b"
                for m in models:
                    safe_name = m.replace(":", "_").replace(".", "_").replace("-", "_")
                    if f"ollama_{safe_name}" == tool_name:
                        target_model = m
                        break
                result = ollama_generate(prompt, target_model)
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {"content": [{"type": "text", "text": result}]}
                }
            else:
                response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(f"Error: {e}\n")

if __name__ == "__main__":
    main()
