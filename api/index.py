"""
换装相机 API - Vercel Serverless Entry Point
"""
from http.server import BaseHTTPRequestHandler
import json
import uuid
from urllib.parse import parse_qs, urlparse

# In-memory storage (note: resets between invocations in serverless)
tasks_store = {}


class handler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        # Health check
        if path == '/api/v1/health':
            self._send_json({
                "status": "ok",
                "service": "换装相机 API",
                "version": "2.0.0",
                "environment": "vercel"
            })
            return

        # Options API
        if path == '/api/v1/options':
            lang = query.get('lang', ['en'])[0]
            if lang == 'zh':
                self._send_json({
                    "room_types": [
                        {"value": "living_room", "label": "客厅"},
                        {"value": "bedroom", "label": "卧室"},
                        {"value": "study", "label": "书房"},
                        {"value": "dining_room", "label": "餐厅"},
                    ],
                    "styles": [
                        {"value": "nordic", "label": "北欧风格", "description": "功能主义，白+原木"},
                        {"value": "japanese", "label": "日式风格", "description": "侘寂美学，低重心"},
                        {"value": "modern_luxury", "label": "现代轻奢", "description": "克制奢华"},
                    ],
                    "budgets": [
                        {"value": "low", "label": "点睛改造", "amount": 300, "description": "1-2件焦点"},
                        {"value": "medium", "label": "氛围升级", "amount": 500, "description": "核心场景"},
                        {"value": "high", "label": "质感重塑", "amount": 1000, "description": "全面优化"},
                    ]
                })
            else:
                self._send_json({
                    "room_types": [
                        {"value": "living_room", "label": "Living Room"},
                        {"value": "bedroom", "label": "Bedroom"},
                        {"value": "study", "label": "Home Office"},
                        {"value": "dining_room", "label": "Dining Room"},
                    ],
                    "styles": [
                        {"value": "boho", "label": "Boho", "description": "Eclectic, warm textures"},
                        {"value": "modern_minimalist", "label": "Modern Minimalist", "description": "Clean lines"},
                        {"value": "scandinavian", "label": "Scandinavian", "description": "Bright, airy"},
                        {"value": "coastal", "label": "Coastal", "description": "Beach-inspired"},
                        {"value": "industrial", "label": "Industrial", "description": "Raw textures"},
                    ],
                    "budgets": [
                        {"value": "200", "label": "$200", "amount": 200, "description": "Quick makeover"},
                        {"value": "400", "label": "$400", "amount": 400, "description": "Visible transformation"},
                        {"value": "800", "label": "$800", "amount": 800, "description": "Cohesive look"},
                        {"value": "1500", "label": "$1500", "amount": 1500, "description": "High-end redesign"},
                    ]
                })
            return

        # Task status
        if path.startswith('/api/v1/task/'):
            task_id = path.split('/')[-1]
            task = tasks_store.get(task_id)
            if task:
                self._send_json(task)
            else:
                self._send_json({"error": "Task not found"}, 404)
            return

        # Not found
        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length > 0 else b''

        # Upload API (simplified - just returns success)
        if path == '/api/v1/upload':
            image_id = str(uuid.uuid4())
            tasks_store[f"image_{image_id}"] = {"uploaded": True}
            self._send_json({
                "success": True,
                "image_id": image_id,
                "image_url": f"/uploads/{image_id}.jpg",
                "message": "Upload successful"
            })
            return

        # Generate API
        if path == '/api/v1/generate':
            task_id = str(uuid.uuid4())
            tasks_store[task_id] = {
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "Task created. Note: Full AI generation requires backend setup."
            }
            self._send_json({
                "task_id": task_id,
                "status": "pending",
                "progress": 0,
                "message": "Task created"
            })
            return

        # Analyze space API
        if path == '/api/v1/analyze-space':
            self._send_json({
                "analysis": "## Space Analysis\n\nThis room has good potential for styling.\n\n[[IMAGE_PROMPT]]\nModern interior with natural light\n[[/IMAGE_PROMPT]]"
            })
            return

        self._send_json({"error": "Not found"}, 404)
