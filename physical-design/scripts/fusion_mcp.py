"""Small localhost MCP client for the running Autodesk Fusion instance."""
import argparse
import base64
import http.client
import json
from pathlib import Path


class FusionMCP:
    def __init__(self):
        self.connection = http.client.HTTPConnection("127.0.0.1", 27182, timeout=180)
        self.headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        self.counter = 0
        self.request("initialize", {
            "protocolVersion": "2025-03-26", "capabilities": {},
            "clientInfo": {"name": "safewall-design", "version": "0.1.0"},
        })
        self.request("notifications/initialized", notification=True)

    def request(self, method, params=None, notification=False):
        payload = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            payload["params"] = params
        if not notification:
            self.counter += 1
            payload["id"] = self.counter
        self.connection.request("POST", "/mcp", json.dumps(payload), self.headers)
        response = self.connection.getresponse()
        raw = response.read().decode()
        session = response.getheader("MCP-Session-Id")
        if session:
            self.headers["MCP-Session-Id"] = session
        if response.status >= 400:
            raise RuntimeError(f"HTTP {response.status}: {raw}")
        if not raw:
            return None
        decoded = json.loads(raw)
        if "error" in decoded:
            raise RuntimeError(decoded["error"])
        return decoded.get("result")

    def call(self, name, arguments):
        result = self.request("tools/call", {"name": name, "arguments": arguments})
        if result.get("isError"):
            raise RuntimeError(result)
        for block in result.get("content", []):
            if block.get("type") != "text":
                continue
            try:
                payload = json.loads(block["text"])
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and payload.get("success") is False:
                raise RuntimeError(payload.get("error", payload))
        return result


def print_result(result):
    for block in result.get("content", []):
        if block.get("type") == "text":
            print(block["text"])
    if "structuredContent" in result:
        print(json.dumps(result["structuredContent"], indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["read", "docs", "run", "screenshot"])
    parser.add_argument("value")
    parser.add_argument("--direction", default="current")
    args = parser.parse_args()
    client = FusionMCP()
    try:
        if args.command == "read":
            result = client.call("fusion_mcp_read", json.loads(args.value))
        elif args.command == "docs":
            result = client.call("fusion_mcp_read", {
                "queryType": "apiDocumentation", "searchPattern": args.value, "apiCategory": "all",
            })
        elif args.command == "run":
            result = client.call("fusion_mcp_execute", {
                "featureType": "script", "object": {"script": Path(args.value).read_text()},
            })
        else:
            result = client.call("fusion_mcp_read", {
                "queryType": "screenshot", "width": 1800, "height": 1300,
                "antiAliasing": True, "transparentBackground": False,
                "direction": args.direction,
            })
            candidates = list(result.get("content", []))
            structured = result.get("structuredContent")
            if structured:
                candidates.append(structured)
            for block in list(candidates):
                if block.get("type") == "text":
                    try:
                        candidates.append(json.loads(block["text"]))
                    except (json.JSONDecodeError, TypeError):
                        pass
            for block in candidates:
                encoded = block.get("base64Data") or (block.get("data") if block.get("type") == "image" else None)
                if encoded:
                    target = Path(args.value)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(base64.b64decode(encoded))
                    print(f"Saved screenshot: {target}")
                    return
            raise RuntimeError(f"Screenshot image missing; result keys: {list(result)}")
        print_result(result)
    finally:
        client.connection.close()


if __name__ == "__main__":
    main()
