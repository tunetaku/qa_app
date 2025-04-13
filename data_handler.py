import sqlite3
import os
from datetime import datetime
from db_init import init_db

# 質問保存
def save_question(title, content, category, tags, ldap_id):
    try:
        print(f"保存試行 - タイトル: {title}, カテゴリ: {category}, ユーザー: {ldap_id}")  # デバッグ用
        init_db()
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        tags_str = ",".join(tags) if tags else ""
        
        c.execute('''INSERT INTO questions 
                    (title, content, category, tags, ldap_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 (title, content, category, tags_str, ldap_id, 
                  datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        question_id = c.lastrowid
        print(f"保存成功 - 質問ID: {question_id}")  # デバッグ用
        return question_id
    except Exception as e:
        print(f"保存エラー: {str(e)}")  # 詳細なエラー出力
        return None
    finally:
        if 'conn' in locals():
            conn.close()

# 回答追加
def add_answer(question_id, content, ldap_id):
    try:
        print(f"回答追加試行 - 質問ID: {question_id}, ユーザー: {ldap_id}, 内容長: {len(content)}")  # デバッグ用
        init_db()
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        c.execute('''INSERT INTO answers
                    (question_id, content, ldap_id, posted_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)''',
                 (question_id, content, ldap_id, now, now))
        
        conn.commit()
        print(f"回答追加成功 - 質問ID: {question_id}")
        return True
    except Exception as e:
        print(f"回答の保存に失敗しました: {str(e)}")  # 詳細なエラー出力
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# 回答更新
def update_answer(answer_id, new_content):
    try:
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        c.execute('''
            UPDATE answers 
            SET content = ?, updated_at = ?
            WHERE id = ?
        ''', (new_content, now, answer_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"回答更新エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# 回答削除
def delete_answer(answer_id):
    try:
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        c.execute('DELETE FROM answers WHERE id = ?', (answer_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"回答削除エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# 質問一覧取得
def get_questions(resolved_filter=None):
    try:
        init_db()  # Added init_db call for consistency
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        # Improved query with subquery for answer count (works across databases)
        query = '''
            SELECT q.id, q.title, q.content, q.tags, q.ldap_id, 
                   q.created_at, q.resolved, q.best_answer_id, q.thank_message,
                   u.name as user_name,
                   (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) as answer_count
            FROM questions q
            JOIN users u ON q.ldap_id = u.ldap_id
        '''
        
        if resolved_filter is not None:
            query += f" WHERE q.resolved = {1 if resolved_filter else 0}"
            
        query += " ORDER BY q.created_at DESC"
        
        c.execute(query)
        
        questions = []
        for row in c.fetchall():
            questions.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'tags': row[3],
                'ldap_id': row[4],
                'created_at': row[5],
                'resolved': row[6],
                'best_answer_id': row[7],
                'thank_message': row[8],
                'user_name': row[9] if row[9] else "Unknown",  # Handle NULL user_name
                'answer_count': row[10]
            })
        
        return questions
    except Exception as e:
        print(f"質問取得エラー: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# 回答取得
def get_answers(question_id):
    try:
        print(f"[DEBUG] 回答取得開始 - 質問ID: {question_id}")  # デバッグ用出力
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        sql = '''
            SELECT a.id, a.content, a.posted_at, a.updated_at, u.name as user_name, a.is_best, a.ldap_id
            FROM answers a
            JOIN users u ON a.ldap_id = u.ldap_id
            WHERE a.question_id = ?
            ORDER BY a.is_best DESC, a.posted_at
        '''
        print(f"[DEBUG] 実行SQL:\n{sql}")  # デバッグ用SQL出力
        print(f"[DEBUG] パラメータ: {question_id}")  # デバッグ用パラメータ出力
        
        c.execute(sql, (question_id,))
        
        answers = []
        rows = c.fetchall()
        print(f"[DEBUG] 取得行数: {len(rows)}")  # デバッグ用取得件数出力
        
        for row in rows:
            answers.append({
                'id': row[0],
                'content': row[1],
                'posted_at': row[2],
                'updated_at': row[3],
                'user_name': row[4] if row[4] else "Unknown",
                'is_best': row[5],
                'ldap_id': row[6],
                'question_id': question_id  # 明示的にquestion_idを追加
            })
        
        print(f"[DEBUG] 回答データ: {answers}")  # デバッグ用回答データ出力
        return answers
    except Exception as e:
        print(f"[DEBUG] 回答取得エラー: {e}")  # 詳細なエラー出力
        return []
    finally:
        if 'conn' in locals():
            conn.close()

# ユーザー名取得
def get_user_name(ldap_id):
    try:
        init_db()
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        c.execute("SELECT name FROM users WHERE ldap_id=?", (ldap_id,))
        result = c.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"ユーザー名の取得に失敗しました: {e}")
        return None
    finally:
        conn.close()

# ユーザー登録
def signup(ldap_id, name):
    try:
        init_db()
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO users (ldap_id, name, created_at)
                     VALUES (?, ?, ?)''',
                 (ldap_id, name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"ユーザー登録エラー: {e}")  # Improved error logging
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# ログイン確認
def login(ldap_id):
    try:
        init_db()
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        c.execute("SELECT name FROM users WHERE ldap_id=?", (ldap_id,))
        result = c.fetchone()
        return result is not None
    except Exception as e:
        print(f"ログイン確認に失敗しました: {e}")
        return False
    finally:
        conn.close()

# 質問を解決済みにする
def mark_question_resolved(question_id, thank_message=None):
    try:
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        c.execute('''
            UPDATE questions 
            SET resolved = 1, thank_message = ?
            WHERE id = ?
        ''', (thank_message, question_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"質問解決済み設定エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# 質問を未解決に戻す
def mark_question_unresolved(question_id):
    try:
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        c.execute('''
            UPDATE questions 
            SET resolved = 0, best_answer_id = NULL, thank_message = NULL
            WHERE id = ?
        ''', (question_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"質問未解決設定エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# ベストアンサー設定
def set_best_answer(question_id, answer_id):
    try:
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        # 既存のベストアンサーをリセット
        c.execute('''
            UPDATE answers 
            SET is_best = 0 
            WHERE question_id = ?
        ''', (question_id,))
        
        # 新しいベストアンサーを設定
        c.execute('''
            UPDATE answers 
            SET is_best = 1 
            WHERE id = ?
        ''', (answer_id,))
        
        # 質問にベストアンサーIDを記録
        c.execute('''
            UPDATE questions 
            SET best_answer_id = ? 
            WHERE id = ?
        ''', (answer_id, question_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"ベストアンサー設定エラー: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

# 質問検索（複数キーワードAND検索）
def search_questions(keywords):
    try:
        conn = sqlite3.connect('qa_app.db')
        c = conn.cursor()
        
        # キーワードを分割して検索条件を生成
        keywords = [k.strip() for k in keywords.split() if k.strip()]
        if not keywords:
            return []
            
        # 各キーワードを含む質問をAND条件で検索
        query = '''
            SELECT q.*, u.name as user_name,
                   (SELECT COUNT(*) FROM answers a WHERE a.question_id = q.id) as answer_count
            FROM questions q
            JOIN users u ON q.ldap_id = u.ldap_id
            WHERE ''' + ' AND '.join(['(q.title LIKE ? OR q.content LIKE ? OR q.tags LIKE ?)' for _ in keywords])
        
        params = []
        for keyword in keywords:
            like_term = f'%{keyword}%'
            params.extend([like_term, like_term, like_term])
        
        c.execute(query, params)
        
        questions = []
        for row in c.fetchall():
            questions.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'tags': row[3],
                'ldap_id': row[4],
                'created_at': row[5],
                'resolved': row[6],
                'best_answer_id': row[7],
                'thank_message': row[8],
                'user_name': row[9],
                'answer_count': row[10]
            })
        
        return questions
    except Exception as e:
        print(f"検索エラー: {e}")
        return []
    finally:
        if 'conn' in locals():
            conn.close()