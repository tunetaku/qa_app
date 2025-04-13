import sqlite3

def init_db():
    conn = sqlite3.connect('qa_app.db')
    c = conn.cursor()
    
    # ユーザーテーブル
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (ldap_id TEXT PRIMARY KEY, 
                  name TEXT NOT NULL,
                  created_at TEXT)''')
    
    # 質問テーブル
    c.execute('''CREATE TABLE IF NOT EXISTS questions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  category TEXT,
                  tags TEXT,
                  ldap_id TEXT,
                  created_at TEXT,
                  resolved INTEGER DEFAULT 0,
                  best_answer_id INTEGER DEFAULT NULL,
                  thank_message TEXT,
                  FOREIGN KEY(ldap_id) REFERENCES users(ldap_id))''')
    
    # 回答テーブル
    c.execute('''CREATE TABLE IF NOT EXISTS answers
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question_id INTEGER,
                  content TEXT,
                  ldap_id TEXT,
                  posted_at TEXT,
                  updated_at TEXT,
                  is_best INTEGER DEFAULT 0,
                  FOREIGN KEY(question_id) REFERENCES questions(id),
                  FOREIGN KEY(ldap_id) REFERENCES users(ldap_id))''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("データベースを初期化します...")
    init_db()
    print("データベースの初期化が完了しました")
