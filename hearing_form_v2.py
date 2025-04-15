# 最初のインポートたち
import smtplib
import imghdr
import re
import unicodedata
from flask import Flask, render_template, request
from email.message import EmailMessage

app = Flask(__name__)

# 安全にフォームから単一の値を取得するヘルパー関数
def safe_get_form(key, default=""):
    value = request.form.get(key, default)
    if value is None:
        return default
    # NBSPなどの問題となる文字を事前に置換
    return unicodedata.normalize("NFKC", str(value)).replace("\u00A0", " ")

# 安全にフォームからリスト値を取得するヘルパー関数
def safe_get_form_list(key):
    values = request.form.getlist(key)
    return [unicodedata.normalize("NFKC", str(value)).replace("\u00A0", " ") if value else "" for value in values]

# トップページの表示（index.htmlを表示する）
@app.route('/')
def index():
    return render_template("index.html")  # ← これでテンプレートが表示される

# フォームの送信処理
@app.route('/submit', methods=['POST'])
def submit():
    print(request.form)  # ← これ追加！
    form_type = safe_get_form("form_type")
    if form_type == "logo_only":
        return handle_logo_form()
    elif form_type == "card_only":
        return handle_card_form()
    elif form_type == "logo_and_card":
        return handle_logo_card_form()
    else:
        return "不明なフォームです"

@app.route('/submit_card', methods=['POST'])
def submit_card():
    return handle_card_form()

def get_basic_info():
    user_name = safe_get_form("user_name")
    user_email = safe_get_form("user_email")
    company = safe_get_form("company_name")
    address = safe_get_form("address")
    phone = safe_get_form("phone")

    return f"""■ お名前：{user_name}
■ メールアドレス：{user_email}
■ 会社名または屋号：{company}
■ 住所：{address}
■ 電話番号：{phone}
"""

def handle_logo_form():
    user_name = safe_get_form("user_name")
    user_email = safe_get_form("user_email")

    target = safe_get_form("logo_target")
    age_group = safe_get_form("logo_age_group")
    priority_color = safe_get_form("priority_color")
    company_name = safe_get_form("logo_company")
    name_origin = safe_get_form("logo_meaning")
    logo_type = safe_get_form("logo_type")
    motif = safe_get_form("logo_motif")
    text = safe_get_form("logo_text")
    direction = safe_get_form("logo_direction")
    usage_other = safe_get_form("usage_other_text")
    reference_url = safe_get_form("logo_reference_url")
    other = safe_get_form("logo_other")

    keywords = safe_get_form_list("keywords")
    colors = safe_get_form_list("logo_colors")
    usage = safe_get_form_list("usage")

    body = f"""
{get_basic_info()}

【ロゴヒアリングシート】
■ お名前：{user_name}
■ メールアドレス：{user_email}
■ ターゲット層：{target}
■ 年齢層：{age_group}
■ デザインキーワード：{', '.join(keywords)}
■ イメージカラー：{', '.join(colors)}
■ 重要視する色：{priority_color}
■ 会社・商品名：{company_name}
■ 名前の由来：{name_origin}
■ ロゴイメージ：{logo_type}
■ モチーフ：{motif}
■ ロゴに入れるテキスト：{text}
■ ロゴの方向性：{direction}
■ 使用用途：{', '.join(usage)}
■ その他の使用用途：{usage_other}
■ 参考URL：{reference_url}
■ その他のご希望：{other}
"""

    try:
        send_mail(
            subject="【ロゴヒアリング】新しい回答が届きました",
            sender_email="azumaprint@p-pigeon.com",
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body
        )
        return render_template("thank_you.html")
    except Exception as e:
        return f"送信エラー: {e}"

import os
from werkzeug.utils import secure_filename  # ファイル名安全化のため

def handle_card_form():
    # 単一入力・テキスト
    name = safe_get_form("card_name")
    furigana = safe_get_form("card_furigana")
    romaji = safe_get_form("card_romaji")
    phone = safe_get_form("card_contact")
    address = safe_get_form("address")
    company = safe_get_form("company_name")

    # アップロード画像の取得と保存
    uploaded_image = request.files.get("card_material")
    print("ファイル名:", uploaded_image.filename if uploaded_image else "None")
    saved_filename = ""
    if uploaded_image and uploaded_image.filename != "":
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(uploaded_image.filename)
        save_path = os.path.join(upload_dir, filename)
        uploaded_image.save(save_path)
        saved_filename = filename

    # チェックボックス（複数選択）
    keywords = safe_get_form_list("card_keywords")
    colors = safe_get_form_list("card_colors")

    # その他入力
    keywords_note = safe_get_form("card_keywords_note")
    colors_note = safe_get_form("card_colors_note")
    font_request = safe_get_form("font_notes")
    reference_url = safe_get_form("reference_url")
    other_requests = safe_get_form("other_requests")

    # 単一選択（ラジオボタン）
    reference_style = safe_get_form("card_reference_url")

    # ✅ ここからメール本文・送信までが関数の「内側」にいる！
    body = f"""
{get_basic_info()}

【名刺ヒアリングシート】
■ 表記名：{name}
■ フリガナ：{furigana}
■ ローマ字：{romaji}
■ 電話番号など：{phone}
■ 住所など：{address}
■ 会社名など：{company}
■ デザインキーワード：{', '.join(keywords)}（補足：{keywords_note}）
■ イメージカラー：{', '.join(colors)}（補足：{colors_note}）
■ フォントに関するご希望：{font_request}
■ 参考イメージ：{reference_style}
■ その他参考URL：{reference_url}
■ その他のご要望：{other_requests}
"""

    attachments = []
    if saved_filename:
        file_path = os.path.join("uploads", saved_filename)
        attachments.append(file_path)

    try:
        send_mail(
            subject="【名刺ヒアリング】新しい回答が届きました",
            sender_email="azumaprint@p-pigeon.com",
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body,
            attachments=attachments
        )
        return render_template("thank_you.html")
    except Exception as e:
        return f"送信エラー: {e}"




def handle_logo_card_form():
    # 基本情報
    user_name = safe_get_form("user_name")
    user_email = safe_get_form("user_email")

    # ロゴ部分
    target = safe_get_form("logo_target")
    age_group = safe_get_form("logo_age_group")
    priority_color = safe_get_form("priority_color")
    company_name = safe_get_form("logo_company")
    name_origin = safe_get_form("logo_meaning")
    logo_type = safe_get_form("logo_type")
    motif = safe_get_form("logo_motif")
    text = safe_get_form("logo_text")
    direction = safe_get_form("logo_direction")
    usage_other = safe_get_form("usage_other_text")
    reference_url = safe_get_form("logo_reference_url")
    other = safe_get_form("logo_other")

    keywords_logo = safe_get_form_list("keywords")
    colors_logo = safe_get_form_list("logo_colors")
    usage_logo = safe_get_form_list("usage")

    # 名刺部分
    name = safe_get_form("card_name")
    furigana = safe_get_form("card_furigana")
    romaji = safe_get_form("card_romaji")
    phone = safe_get_form("card_contact")
    address = safe_get_form("address")
    company = safe_get_form("company_name")

    keywords_card = safe_get_form_list("card_keywords")
    colors_card = safe_get_form_list("card_colors")
    reference_img = request.files.get("card_material")

    font_notes = safe_get_form("font_notes")
    reference_url_card = safe_get_form("reference_url")
    other_requests = safe_get_form("other_requests")

    # アップロード画像の保存
    saved_filename = ""
    if reference_img and reference_img.filename != "":
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(reference_img.filename)
        save_path = os.path.join(upload_dir, filename)
        reference_img.save(save_path)
        saved_filename = filename

    # メール本文組み立て
    body = f"""
{get_basic_info()}

【ロゴ＋名刺ヒアリングシート】

=== ロゴデザイン ===
■ ターゲット層：{target}
■ 年齢層：{age_group}
■ デザインキーワード：{', '.join(keywords_logo)}
■ イメージカラー：{', '.join(colors_logo)}
■ 重要視する色：{priority_color}
■ 会社・商品名：{company_name}
■ 名前の由来：{name_origin}
■ ロゴイメージ：{logo_type}
■ モチーフ：{motif}
■ ロゴに入れるテキスト：{text}
■ ロゴの方向性：{direction}
■ 使用用途：{', '.join(usage_logo)}
■ その他の使用用途：{usage_other}
■ 参考URL：{reference_url}
■ その他のご希望：{other}

=== 名刺デザイン ===
■ 表記名：{name}
■ フリガナ：{furigana}
■ ローマ字表記：{romaji}
■ 電話番号など：{phone}
■ 住所：{address}
■ 会社名：{company}
■ デザインキーワード：{', '.join(keywords_card)}
■ イメージカラー：{', '.join(colors_card)}
■ フォントに関する要望：{font_notes}
■ 参考URL：{reference_url_card}
■ その他ご要望：{other_requests}
"""

    # 添付ファイル
    attachments = []
    if saved_filename:
        file_path = os.path.join("uploads", saved_filename)
        attachments.append(file_path)

    try:
        send_mail(
            subject="【ロゴ＋名刺ヒアリング】新しい回答が届きました",
            sender_email="azumaprint@p-pigeon.com",
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body,
            attachments=attachments
        )
        return render_template("thank_you.html")
    except Exception as e:
        return f"送信エラー: {e}"

def send_mail(subject, sender_email, app_password, recipient_email, body, attachments=None):
    subject = unicodedata.normalize("NFKC", str(subject)).replace(u'\u00A0', ' ')
    sender_email = str(sender_email)
    recipient_email = str(recipient_email)
    body = unicodedata.normalize("NFKC", str(body)).replace(u'\u00A0', ' ')

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email
    msg.set_content(body, charset='utf-8')


    if attachments:
        for file_path in attachments:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    file_name = os.path.basename(file_path)
                    file_name = unicodedata.normalize("NFKC", str(file_name)).replace('\xa0', ' ')
                    
                    img_type = imghdr.what(None, file_data)
                    if img_type:
                        maintype = 'image'
                        subtype = img_type
                    else:
                        maintype = 'application'
                        subtype = 'octet-stream'
                    
                    msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
            except Exception as e:
                print(f"添付ファイルエラー: {e}")

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.sendmail(sender_email, recipient_email, msg.as_string().encode('utf-8'))
    except Exception as e:
        print(f"メール送信エラー: {type(e).__name__}: {e}")
        raise



# ローカルサーバー起動
if __name__ == '__main__':
    app.run(debug=True)