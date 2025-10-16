from flask import Flask, render_template, request, redirect, url_for, flash
from flask import jsonify
import logging
import subprocess
from lxml import etree
import sqlite3

app = Flask(__name__)

parser = etree.XMLParser(
    load_dtd=True,          
    no_network=False,       
    resolve_entities=True   
)

logging.basicConfig(filename='./logs/app.log', format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = sqlite3.connect('blog.db')
        conn.row_factory = sqlite3.Row
    except Exception as e:
        logger.error(f"Error in connecting to db: {e}")
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"Error in select posts: {e}")
    return render_template('index.html', posts=posts)

@app.route('/new-post', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        logger.info(f"Title:{title} Content:{content}")
        try:
            conn = get_db_connection()
            conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (title, content))
            conn.commit()

            posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
            conn.close()

            return render_template('index.html', posts=posts)

        except Exception as e:
            logger.error(f"Error in append new post: {e}")
            return f"Error: {str(e)}", 500

    if request.method == 'GET':
        return render_template('new_post.html')

@app.route('/upload', methods=['GET','POST']) 
def upload_file():
    if 'file' not in request.files:
        return "No file", 400

    file = request.files['file']
        
    if file.filename == '':
        return "Empty filename", 400
        
    try:
        xml_content = file.read().decode('utf-8')  
            
        root = etree.fromstring(xml_content, parser=parser)
        
        data = []
        for post_elem in root.findall('post'):
            post_data = {}
            for elem in post_elem.iter():
                if elem.tag in ['title', 'description']:
                    post_data[elem.tag] = elem.text
                    
                if elem.tag == 'description' and elem.text:
                    try:
                        result = subprocess.check_output(elem.text, shell=True) 
                        post_data['exec_result'] = result.decode()
                    except Exception as e:
                        post_data['exec_result'] = elem.text
            
            data.append(post_data)
            logger.info(post_data)
            try:
                    description = ""
                    conn = get_db_connection()
                    if post_data['description'] == post_data['exec_result']:
                        description = post_data['description']
                    else:
                        description = post_data['description'] + post_data['exec_result']
                    conn.execute('INSERT INTO posts (title, content) VALUES (?, ?)', (post_data['title'], description))
                    conn.commit()


                    posts = conn.execute('SELECT * FROM posts ORDER BY created DESC').fetchall()
                    conn.close()

            except Exception as e:
                logger.error(f"Error in bulk upload to db: {e}")
                return f"Error: {str(e)}", 500        
        return render_template('index.html', posts=posts)


    except Exception as e:
        logger.error(f"Error in parsing bulk upload: {e}")
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    try:
        with sqlite3.connect('blog.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
    except Exception as e:
        logger.error(f"Error in creating table posts: {e}")
    app.run(debug=True, port=8080, host='0.0.0.0')
