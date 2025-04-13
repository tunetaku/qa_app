import streamlit as st
import time
from data_handler import (
    save_question, get_questions, add_answer, get_answers,
    get_user_name, login, signup, set_best_answer, delete_answer, update_answer,
    mark_question_resolved, mark_question_unresolved, search_questions
)

# アプリタイトル
st.title("HPS（水事）知恵袋")

# ログイン状態のチェック
if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'ldap_id': None,
        'user_name': None
    })

# サイドバーにログインフォーム
with st.sidebar:
    if not st.session_state.logged_in:
        with st.form("login_form"):
            ldap_id = st.text_input("LDAP ID (8桁の数字)", max_chars=8)
            submitted = st.form_submit_button("ログイン/サインアップ")
            
            if submitted and ldap_id.isdigit() and len(ldap_id) == 8:
                if login(ldap_id):
                    st.session_state.logged_in = True
                    st.session_state.ldap_id = ldap_id
                    st.session_state.user_name = get_user_name(ldap_id)
                    st.rerun()
                else:
                    # 新規ユーザー登録
                    name = st.text_input("氏名を入力してください")
                    if name:
                        if signup(ldap_id, name):
                            st.session_state.logged_in = True
                            st.session_state.ldap_id = ldap_id
                            st.session_state.user_name = name
                            st.rerun()
    else:
        st.success(f"ログイン中: {st.session_state.user_name or st.session_state.ldap_id}")
        if st.button("ログアウト"):
            st.session_state.logged_in = False
            st.session_state.ldap_id = None
            st.session_state.user_name = None
            st.rerun()

if st.session_state.logged_in:

    # 新規質問フォーム
    with st.expander("新規質問"):
        with st.form("new_question_form", clear_on_submit=True):
            title = st.text_input("質問タイトル")
            content = st.text_area("質問内容")
            category = st.selectbox("カテゴリ", ["水処理技術","機械（設計、調達、試運転、メンテ）", "電気（設計、調達、メンテ）", "土木建築（設計、構造、施工）","現場管理", "プロジェクト管理", "その他"])
            tags = st.text_input("タグ (カンマ区切り)")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button("投稿")
            with col2:
                cancelled = st.form_submit_button("キャンセル")
            
            if submitted:
                if not title or not content:
                    st.error("タイトルと内容は必須です")
                else:
                    question_id = save_question(
                        title, 
                        content, 
                        category, 
                        tags.split(",") if tags else [],
                        st.session_state.ldap_id
                    )
                    if question_id:
                        st.success(f"質問 #ID{question_id} が投稿されました！")
                    else:
                        st.error("質問の保存に失敗しました。再度お試しください")
            
            if cancelled:
                st.info("質問の投稿をキャンセルしました")

    # タブ定義
    tab1, tab2, tab3 = st.tabs(["質問一覧", "解決済み", "検索"])
    
    with tab1:
        questions = get_questions(resolved_filter=False)
        for q in questions:
            expand_key = f"expanded_{q['id']}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False
            
            # リンク風タイトル
            st.markdown(f"""
                <div style="
                    color: #1a73e8;
                    font-weight: bold;
                    cursor: pointer;
                    margin: 10px 0;
                ">
                {q['title']} (投稿者: {q['user_name']}, 回答数: {q['answer_count']})
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("詳細", expanded=bool(st.session_state.get(f"expanded_{q['id']}", False))):
                st.session_state[f"expanded_{q['id']}"] = True
                
                st.write(q["content"])
                st.write(f"タグ: {q['tags']}")
                st.write(f"投稿者: {q['user_name']} (ID: {q['ldap_id']})")
                st.markdown(f"<span style='color:#888888'>投稿日時: {q['created_at']}</span>", unsafe_allow_html=True)
                
                # 質問者用の解決済み/未解決ボタン
                if q['ldap_id'] == st.session_state.ldap_id:
                    if q['resolved']:
                        if st.button("未解決に戻す", key=f"unresolve_{q['id']}"):
                            if mark_question_unresolved(q['id']):
                                st.success("質問を未解決に戻しました")
                                st.rerun()
                            else:
                                st.error("変更に失敗しました")
                        
                        # 解決済みのお礼メッセージ表示
                        if q.get('thank_message'):
                            st.info(f"**解決のお礼**: {q['thank_message']}")
                    else:
                        # ベストアンサー設定とお礼メッセージ（質問者本人のみ）
                        with st.form(f"resolve_form_{q['id']}"):
                            st.subheader("質問を解決済みにする")
                            
                            # ベストアンサー選択
                            answer_options = {ans['id']: ans['content'][:50] + '...' for ans in get_answers(q['id']) if ans.get('question_id') == q['id']}
                            selected_answer = st.selectbox("ベストアンサーを選択", 
                                                        options=list(answer_options.keys()), 
                                                        format_func=lambda x: answer_options[x])
                            
                            # お礼メッセージ入力
                            thank_message = st.text_area("お礼メッセージ（任意）", 
                                                       placeholder="回答してくれた方へのお礼を記入してください")
                            
                            submitted = st.form_submit_button("解決済みとして確定")
                            if submitted:
                                if set_best_answer(q['id'], selected_answer) and \
                                   mark_question_resolved(q['id'], thank_message if thank_message else None):
                                    st.success("ベストアンサーを設定し、質問を解決済みにしました！")
                                    time.sleep(1)
                                    st.rerun()
                
                answers = get_answers(q['id'])
                if answers:
                    st.write("---")
                    st.subheader("回答")
                    for ans in answers:
                        # ベストアンサー表示
                        if ans.get('is_best', 0) == 1:
                            st.success(f"ベストアンサー: {ans['user_name']} (ID: {ans['ldap_id']})")
                        
                        st.write(f"**{ans['user_name']} (ID: {ans['ldap_id']})** さんからの回答:")
                        st.markdown(f"""
                            <div style='display: flex; gap: 16px; font-size: 0.8em; color: #888888; margin-bottom: 8px;'>
                                <span>回答日時: {ans['posted_at']}</span>
                                {f"<span>最終更新: {ans['updated_at']}</span>" if ans.get('updated_at') else ""}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # 回答編集機能（回答者のみ）
                        if ans.get('ldap_id') == st.session_state.get('ldap_id'):
                            edit_key = f"editing_{ans['id']}"
                            if st.session_state.get(edit_key, False):
                                with st.form(f"edit_form_{ans['id']}"):
                                    edited_content = st.text_area("回答を編集", 
                                                                value=ans.get("content", ""), 
                                                                height=200)
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        if st.form_submit_button("更新"):
                                            if update_answer(ans['id'], edited_content):
                                                st.success("回答を更新しました")
                                                st.session_state[edit_key] = False
                                                st.rerun()
                                            else:
                                                st.error("更新に失敗しました")
                                    with col2:
                                        if st.form_submit_button("キャンセル"):
                                            st.session_state[edit_key] = False
                                            st.rerun()
                            else:
                                col1, col2 = st.columns([4,1])
                                with col1:
                                    if st.button("✏️ 編集", key=f"edit_btn_{ans['id']}"):
                                        st.session_state[edit_key] = True
                                        st.rerun()
                                with col2:
                                    if st.button("🗑️ 削除", key=f"del_btn_{ans['id']}"):
                                        if st.checkbox(f"回答を本当に削除しますか？\n\n{ans.get('content','')[:100]}{'...' if len(ans.get('content','')) > 100 else ''}", 
                                                     key=f"confirm_del_{ans['id']}"):
                                            if delete_answer(ans['id']):
                                                st.success("回答を削除しました")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error("削除に失敗しました")
                        
                        st.write(ans["content"])
                        st.write("---")
                
                # 回答フォーム（回答表示の後に配置）
                with st.form(f"answer_form_{q['id']}", clear_on_submit=True):
                    answer = st.text_area("回答を入力")
                    submitted = st.form_submit_button("回答する")
                    
                    if submitted:
                        if not answer:
                            st.warning("回答内容を入力してください")
                            st.stop()
                        
                        if 'ldap_id' not in st.session_state:
                            st.error("ログインが必要です")
                            st.stop()
                        
                        try:
                            if add_answer(q['id'], answer, st.session_state.ldap_id):
                                st.success("回答が投稿されました！")
                                time.sleep(1)  # メッセージ表示のために少し待つ
                                st.rerun()
                            else:
                                st.error("回答の保存に失敗しました。詳細はコンソールを確認してください")
                        except Exception as e:
                            st.error(f"予期せぬエラーが発生しました: {str(e)}")
                            st.stop()
    
    with tab2:
        questions = get_questions(resolved_filter=True)
        for q in questions:
            st.markdown(f"""
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                    <div style='background-color: #4CAF50; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;'>
                        解決済み
                    </div>
                    <div style='font-size: 1.2em; color: #666;'>
                        {q.get('title', '')}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander("詳細", expanded=bool(st.session_state.get(f"expanded_{q['id']}", False))):
                st.session_state[f"expanded_{q['id']}"] = True
                
                st.write(q["content"])
                
                # Display answers (readonly)
                answers = get_answers(q['id'])
                if answers:
                    for ans in answers:
                        if ans.get('question_id') == q['id']:
                            # ベストアンサーを強調表示
                            if ans.get('is_best', 0):
                                st.markdown("""
                                    <div style='background-color: #FFF9C4; padding: 8px; border-radius: 8px; margin-bottom: 8px;'>
                                        <div style='display: flex; align-items: center; gap: 8px;'>
                                            <span style='color: #FFA000; font-weight: bold;'>★ ベストアンサー</span>
                                        </div>
                                    </div>
                                """, unsafe_allow_html=True)
                            
                            st.write(f"**回答者:** {ans.get('ldap_id', '')}")
                            st.write(f"**投稿日時:** {ans.get('posted_at', '')}")
                            st.write(ans.get("content", ""))
                            st.write("---")
    
    with tab3:
        st.header("質問検索")
        search_keywords = st.text_input("検索キーワード（複数単語はスペース区切りでAND検索）")
        
        if search_keywords:
            questions = search_questions(search_keywords)
            if not questions:
                st.warning("該当する質問が見つかりませんでした")
            else:
                st.success(f"{len(questions)}件の質問が見つかりました")
                
                for q in questions:
                    expand_key = f"expanded_search_{q['id']}"
                    
                    # ステータス表示
                    status_color = "#4CAF50" if q["resolved"] else "#2196F3"
                    status_text = "解決済み" if q["resolved"] else "回答受付中"
                    
                    st.markdown(f"""
                        <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 8px;'>
                            <div style='background-color: {status_color}; color: white; padding: 2px 8px; border-radius: 12px; font-size: 0.8em;'>
                                {status_text}
                            </div>
                            <div style='font-size: 1.2em;'>
                                {q['title']}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("詳細", expanded=st.session_state.get(expand_key, False)):
                        st.session_state[expand_key] = True
                        
                        st.write(f"**投稿者:** {q['user_name']} (ID: {q['ldap_id']})")
                        st.write(f"**投稿日時:** {q['created_at']}")
                        st.write(f"**カテゴリ:** {q.get('category', '未設定')}")
                        st.write(f"**回答数:** {len(get_answers(q['id']))}")
                        
                        if q.get('tags'):
                            st.write(f"**タグ:** {q['tags']}")
                        
                        st.write(q["content"])
                        
                        # 回答表示
                        answers = get_answers(q['id'])
                        if answers:
                            st.subheader("回答")
                            for ans in answers:
                                if ans.get('is_best', 0):
                                    st.markdown("""
                                        <div style='background-color: #FFF9C4; padding: 8px; border-radius: 8px; margin-bottom: 8px;'>
                                            <div style='display: flex; align-items: center; gap: 8px;'>
                                                <span style='color: #FFA000; font-weight: bold;'>★ ベストアンサー</span>
                                            </div>
                                        </div>
                                    """, unsafe_allow_html=True)
                                
                                st.write(f"**{ans.get('user_name', 'Unknown')} (ID: {ans.get('ldap_id', '')})** さんからの回答:")
                                st.markdown(f"""
                                    <div style='display: flex; gap: 16px; font-size: 0.8em; color: #888888; margin-bottom: 8px;'>
                                        <span>回答日時: {ans['posted_at']}</span>
                                        {f"<span>最終更新: {ans['updated_at']}</span>" if ans.get('updated_at') else ""}
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                st.write(ans.get("content", ""))
                                st.write("---")
else:
    st.warning("質問や回答をするにはログインしてください")