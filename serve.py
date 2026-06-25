"""Static file server with no-cache headers so browsers always fetch fresh JS."""
import http.server, sys, os

class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def log_message(self, *a):
        pass  # silence access log

port = int(sys.argv[1])
directory = sys.argv[2]
os.chdir(directory)
with http.server.HTTPServer(('', port), NoCacheHandler) as httpd:
    print(f'Serving {directory} on port {port}')
    httpd.serve_forever()
