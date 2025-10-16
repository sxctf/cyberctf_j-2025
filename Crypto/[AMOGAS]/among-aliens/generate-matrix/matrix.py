from sage.all import *
import random
import json
import time
import os
import sys
import socketserver
import http.server
import urllib.parse
import threading

def generate_Mars_matrix(k, session_id):
    try:
        seed = 1
        flag_text = os.getenv('FLAG_TEXT', "THIS_IS_NOT_REAL_FLAG_TRY_HARDER").encode()
        M = [0] * (k * k)

        for i in range(k - 1):
            M[i * k + i] = flag_text[i]
            M[i * k + i + 1] = 1
            seed *= flag_text[i]

        M[(k - 1) * k + k - 1] = flag_text[k - 1]
        seed *= flag_text[k - 1]
        M = matrix(QQ, k, k, M)

        random.seed(seed)

        K = [random.randint(0, 255) for _ in range(k * k)]
        K = matrix(QQ, k, k, K)

        C = K * M * K.inverse()

        return C
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def save_matrix(session_id, matrix_data, levels_data):
    output_dir = "/app/matrix-data"
    os.makedirs(output_dir, exist_ok=True)
    
    result = {
        "matrix": str(matrix_data),
        "levels": levels_data,
        "session_id": session_id
    }
    
    output_file = os.path.join(output_dir, f"{session_id}.json")
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return output_file

class MatrixRequestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            path_parts = parsed_path.path.split('/')
            
            if len(path_parts) >= 3 and path_parts[1] == 'generate':
                session_id = path_parts[2]
                matrix = generate_Mars_matrix(32, session_id)

                if matrix:
                    levels = []

                    for i in range(matrix.nrows()):
                        for j in range(matrix.ncols()):
                            cur_l = (int(matrix[i, j][0]) % 5) + 1
                            levels.append(cur_l)

                    output_file = save_matrix(session_id, matrix, levels)
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    response = {
                        "status": "success",
                        "session_id": session_id
                    }
                    
                    self.wfile.write(json.dumps(response).encode())
                
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"Not Found")
                
        except Exception as e:
            print(f"ERROR: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "status": "error",
                "message": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())

def run_server():
    port = 5001
    server_address = ('0.0.0.0', port)
    httpd = socketserver.TCPServer(server_address, MatrixRequestHandler)
    print(f"Matrix generation server started on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("Server stopped")