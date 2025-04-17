# 最初のインポートたち
import smtplib
import imghdr
import re
import unicodedata
from flask import Flask, render_template, request
from email.message import EmailMessage
from email.header import Header
from email.utils import formataddr


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
    return render_template("index.html", form_data={}, errors=[], form_type="")


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

    # 必須チェック（エラーがあればまとめて返す）
    errors = []
    if not user_name:
        errors.append("お名前は必須です。")
    if not user_email:
        errors.append("メールアドレスは必須です。")
    if not company:
        errors.append("会社名または屋号は必須です。")
    if not phone:
        errors.append("電話番号は必須です。")

    if errors:
        return {
        "error": True,
        "messages": errors,
        "form_data": request.form  # ★追加！
    }
    
    

    return {
    "error": False,
    "user_name": user_name,
    "user_email": user_email,
    "company": company,
    "address": address,
    "phone": phone,
    "form_data": request.form  # ★追加（任意）
}

def format_basic_info(data):
    return f"""
■ お名前：{data['user_name']}
■ メールアドレス：{data['user_email']}
■ 会社名または屋号：{data['company']}
■ 住所：{data['address']}
■ 電話番号：{data['phone']}
"""


def handle_logo_form():
    # 共通（基本）情報
    basic_info = get_basic_info()
    if basic_info["error"]:
        return render_template(
        "index.html",
        errors=basic_info["messages"],
        form_data=basic_info["form_data"],  # ★フォーム値も戻す
        form_type="logo_only"
    )

    
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

        # ▼ 必須チェック
    errors = []
    if not target:
        errors.append("主なターゲット層は必須です。")
    if not age_group:
        errors.append("年齢層の選択は必須です。")
    if not keywords:
        errors.append("デザインキーワードは1つ以上選択してください。")
    if not colors:
        errors.append("イメージカラーは1つ以上選択してください。")
    if not company_name:
        errors.append("会社・商品名やサービス名は必須です。")
    if not name_origin:
        errors.append("名前の由来は必須です。")
    if not logo_type:
        errors.append("ロゴイメージの選択は必須です。")
    if not direction:
        errors.append("ロゴの方向性は必須です。")
    if not usage:
        errors.append("使用用途は1つ以上選択してください。")

    # 🔽 ここがフォーム専用のバリデーションエラー処理！！
    if errors:
        return render_template(
        "index.html",
        errors=errors,
        form_data=request.form,
        form_type="logo_only"  # ←ここも忘れずに！
    )

    body = f"""
【基本情報】
■ お名前：{basic_info["user_name"]}
■ メールアドレス：{basic_info["user_email"]}
■ 会社名・屋号：{basic_info["company"]}
■ 住所：{basic_info["address"]}
■ 電話番号：{basic_info["phone"]}

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
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body
        )
        return render_template("thank_you.html")
    except Exception as e:
        return f"送信エラー: {e}"

import os
from werkzeug.utils import secure_filename  # ファイル名安全化のため

def handle_card_form():
    # 共通（基本）情報
    basic_info = get_basic_info()
    if basic_info["error"]:
        return render_template(
        "index.html",
        errors=basic_info["messages"],
        form_data=basic_info["form_data"],  # ★フォーム値も戻す
        form_type="card_only"
    )
    # 単一入力・テキスト
    card_name = safe_get_form("card_name")
    orientation = safe_get_form("card_orientation")
    logo_exist = safe_get_form("logo_exist")
    keywords = safe_get_form_list("card_keywords")
    colors = safe_get_form_list("card_colors")
    font = safe_get_form("font")
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
    errors = []
    if not orientation:
        errors.append("名刺の向きは必須です。")
    if not logo_exist:
        errors.append("既存ロゴの有無は必須です。")
    if not card_name:
        errors.append("お名前は必須です。")
    if not keywords:
        errors.append("デザインキーワードは1つ以上選択してください。")
    if not colors:
        errors.append("イメージカラーは1つ以上選択してください。")
    if not font:
        errors.append("ご希望のイメージフォントを選択してください。")

    
    # 🔽 ここがフォーム専用のバリデーションエラー処理！！
    if errors:
        return render_template(
        "index.html",
        errors=errors,
        form_data=request.form,
        form_type="card_only"  # ←ここも忘れずに！
    )



    # ✅ ここからメール本文・送信までが関数の「内側」にいる！
    body = f"""
【基本情報】
■ お名前：{basic_info["user_name"]}
■ メールアドレス：{basic_info["user_email"]}
■ 会社名・屋号：{basic_info["company"]}
■ 住所：{basic_info["address"]}
■ 電話番号：{basic_info["phone"]}

【名刺ヒアリングシート】
■ 名刺の向き：{orientation}
■ 既存ロゴの有無：{logo_exist}
■ 表記名：{card_name}
■ フリガナ：{furigana}
■ ローマ字：{romaji}
■ 住所・メール・SNS等：{phone}
■ ご住所など：{address}
■ 名刺用会社名：{company}
■ デザインキーワード：{', '.join(keywords)}（補足：{keywords_note}）
■ イメージカラー：{', '.join(colors)}（補足：{colors_note}）
■ ご希望フォント：{font}
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
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body,
            attachments=attachments
        )
        return render_template("thank_you.html")
    except Exception as e:
        return f"送信エラー: {e}"




def handle_logo_card_form():
    # 共通（基本）情報
    basic_info = get_basic_info()
    if basic_info["error"]:
        return render_template(
        "index.html",
        errors=basic_info["messages"],
        form_data=basic_info["form_data"],  # ★フォーム値も戻す
        form_type="logo_and_card"
    )
    # 必須項目
    target = safe_get_form("target_audience")
    age_group = safe_get_form("target_age_group")
    company_name = safe_get_form("logo_company")
    name_origin = safe_get_form("logo_meaning")
    logo_type = safe_get_form("logo_type")
    direction = safe_get_form("logo_direction")
    keywords = safe_get_form_list("keywords")
    colors = safe_get_form_list("logo_colors")
    usage = safe_get_form_list("usage")
    card_name = safe_get_form("card_name")
    font = safe_get_form("font")

    # バリデーション
    errors = []
    if not target:
        errors.append("主なターゲット層は必須です。")
    if not age_group:
        errors.append("ターゲットの年齢層は必須です。")
    if not company_name:
        errors.append("会社・商品名は必須です。")
    if not name_origin:
        errors.append("名前の由来は必須です。")
    if not logo_type:
        errors.append("ロゴイメージは必須です。")
    if not direction:
        errors.append("ロゴの方向性は必須です。")
    if not keywords:
        errors.append("デザインキーワードは1つ以上選択してください。")
    if not colors:
        errors.append("イメージカラーは1つ以上選択してください。")
    if not usage:
        errors.append("使用用途は1つ以上選択してください。")
    if not card_name:
        errors.append("表記名（名刺）は必須です。")
    if not logo_type:
        errors.append("ロゴイメージは必須です。")
    if not font:
        errors.append("ご希望のフォントは必須です。")

    # 🔽 ここがフォーム専用のバリデーションエラー処理！！
    if errors:
        return render_template(
        "index.html",
        errors=errors,
        form_data=request.form,
        form_type="logo_and_card"  # ←ここも忘れずに！
    )


    # 任意・補足項目
    motif = safe_get_form("logo_motif")
    text = safe_get_form("logo_text")
    usage_other = safe_get_form("usage_other_text")
    priority_color = safe_get_form("priority_color")
    reference_url = safe_get_form("reference_url")
    other = safe_get_form("other_requests")
    furigana = safe_get_form("card_furigana")
    romaji = safe_get_form("card_romaji")
    phone = safe_get_form("card_contact")
    address = safe_get_form("address")
    card_back = safe_get_form("card_back")
    qr_url = safe_get_form("qr_url")
    font_notes = safe_get_form("font_notes")

    # メール本文
    body = f"""
【基本情報】
■ お名前：{basic_info["user_name"]}
■ メールアドレス：{basic_info["user_email"]}
■ 会社名・屋号：{basic_info["company"]}
■ 住所：{basic_info["address"]}
■ 電話番号：{basic_info["phone"]}


【ロゴ＋名刺ヒアリングシート】
=== ロゴデザイン ===
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

=== 名刺デザイン ===
■ 表記名：{card_name}
■ フリガナ：{furigana}
■ ローマ字表記：{romaji}
■ 住所・メール・SNS情報等：{phone}
■ 住所：{address}
■ 裏面に入れる内容：{card_back}
■ QRコードURL：{qr_url}
■ ご希望フォント：{font}
■ フォントに関するご希望：{font_notes}
"""

    try:
        send_mail(
            subject="【ロゴ＋名刺ヒアリング】新しい回答が届きました",
            sender_email="azumaprint@p-pigeon.com",
            app_password="zhzt njjz lmby hunm",
            recipient_email="az_bridal@p-pigeon.com",
            body=body
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
    msg['Subject'] = str(Header(subject, 'utf-8'))  # ← ここ！！
    user_name = request.form.get("user_name", "お客様")
    msg['From'] = formataddr((str(Header(user_name, "utf-8")), sender_email))
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