import streamlit as st
from googleapiclient.discovery import build
from textblob import TextBlob
import pandas as pd
import matplotlib.pyplot as plt
import re
import random
import html
from io import BytesIO
from xquik_export import load_xquik_rows

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

# ---------------- UI ----------------
st.set_page_config(page_title="Sentiment Analyzer", layout="wide")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#0f172a,#1e293b);
    color: white;
}
h1,h2,h3,label,p {
    color: #e2e8f0 !important;
}
.stButton>button {
    background-color:#6366f1;
    color:white;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- SESSION ----------------
if "df" not in st.session_state:
    st.session_state.df = None

# ---------------- SENTIMENT ----------------
def get_sentiment(text):
    p = TextBlob(str(text)).sentiment.polarity
    if p > 0.1:
        return "Positive"
    elif p < -0.1:
        return "Negative"
    else:
        return "Neutral"

# ---------------- SAFE TEXT ----------------
def safe_text(text):
    text = re.sub(r'<.*?>', '', str(text))
    text = html.escape(text)
    return text[:200]

# ---------------- PDF ----------------
def create_pdf(df, title):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    elements.append(Spacer(1,10))

    total = len(df)
    pos = len(df[df["Sentiment"]=="Positive"])
    neg = len(df[df["Sentiment"]=="Negative"])
    neu = len(df[df["Sentiment"]=="Neutral"])

    elements.append(Paragraph(f"Total: {total}", styles["Normal"]))
    elements.append(Paragraph(f"Positive: {pos}", styles["Normal"]))
    elements.append(Paragraph(f"Negative: {neg}", styles["Normal"]))
    elements.append(Paragraph(f"Neutral: {neu}", styles["Normal"]))
    elements.append(Spacer(1,10))

    # Graph (small)
    counts = df["Sentiment"].value_counts()
    img_buffer = BytesIO()
    fig, ax = plt.subplots(figsize=(2,1.2))
    ax.bar(counts.index, counts.values, color=["green","red","orange"])
    plt.tight_layout()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)

    elements.append(Image(img_buffer, width=150, height=90))
    elements.append(Spacer(1,10))

    # All comments
    for i, c in enumerate(df["Comment"]):
        elements.append(Paragraph(f"{i+1}. {safe_text(c)}", styles["Normal"]))
        elements.append(Spacer(1,4))

        if (i+1) % 30 == 0:
            elements.append(PageBreak())

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ---------------- SIDEBAR ----------------
platform = st.sidebar.selectbox("📂 Platform", ["🎬 YouTube", "🐦 X", "ℹ️ About"])

# ================= YOUTUBE =================
if platform == "🎬 YouTube":

    menu = st.sidebar.selectbox("📌 Menu", ["🏠 Home", "📊 Graph", "📈 Trend", "📄 Report"])

    if menu == "🏠 Home":
        st.title("🎬 YouTube Sentiment Analyzer")

        url = st.text_input("Enter YouTube URL")

        if st.button("Analyze"):

            video_id = None
            patterns = [r"v=([a-zA-Z0-9_-]{11})", r"youtu\.be/([a-zA-Z0-9_-]{11})"]

            for p in patterns:
                m = re.search(p, url)
                if m:
                    video_id = m.group(1)

            youtube = build('youtube', 'v3', developerKey="Replace with your key")

            comments, dates = [], []

            request = youtube.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=100
            )

            while request:
                response = request.execute()
                for item in response["items"]:
                    snippet = item["snippet"]["topLevelComment"]["snippet"]
                    comments.append(snippet["textDisplay"])
                    dates.append(snippet["publishedAt"])
                request = youtube.commentThreads().list_next(request, response)

            sentiments = [get_sentiment(c) for c in comments]

            df = pd.DataFrame({
                "Comment": comments,
                "Sentiment": sentiments,
                "Date": pd.to_datetime(dates)
            })

            st.session_state.df = df

            st.subheader("😊 Positive")
            st.dataframe(df[df["Sentiment"]=="Positive"])

            st.subheader("😡 Negative")
            st.dataframe(df[df["Sentiment"]=="Negative"])

            st.subheader("😐 Neutral")
            st.dataframe(df[df["Sentiment"]=="Neutral"])

    elif menu == "📊 Graph":
        df = st.session_state.df
        if df is not None:
            counts = df["Sentiment"].value_counts()

            fig, ax = plt.subplots(figsize=(2.2,1.3))
            ax.bar(counts.index, counts.values, color=["green","red","orange"])
            ax.tick_params(labelsize=6)

            st.pyplot(fig, use_container_width=False)

    elif menu == "📈 Trend":
        df = st.session_state.df
        if df is not None:
            df["Day"] = df["Date"].dt.date
            trend = df.groupby("Day").size()

            fig, ax = plt.subplots(figsize=(4.5,2.5))  # balanced width
            ax.plot(trend.index, trend.values, marker='o')

            ax.set_title("Comment Trend", fontsize=10)

            # 🔥 FIX overlap
            plt.xticks(rotation=45, fontsize=7)
            ax.tick_params(axis='y', labelsize=7)

            plt.tight_layout()

            st.pyplot(fig, use_container_width=False)

    elif menu == "📄 Report":
        df = st.session_state.df
        if df is not None:

            st.write("Total:", len(df))
            st.write("Positive:", len(df[df["Sentiment"]=="Positive"]))
            st.write("Negative:", len(df[df["Sentiment"]=="Negative"]))
            st.write("Neutral:", len(df[df["Sentiment"]=="Neutral"]))

            st.subheader("All Comments")
            st.dataframe(df)

            st.download_button(
                "Download PDF",
                create_pdf(df, "YouTube Report"),
                "youtube_report.pdf"
            )

# ================= X =================
elif platform == "🐦 X":

    menu = st.sidebar.selectbox("📌 Menu", ["🏠 Home", "📊 Graph", "📄 Report"])

    def fake_tweets(keyword):
        samples = [
            f"{keyword} is amazing",
            f"{keyword} is bad",
            f"{keyword} is okay",
            f"{keyword} is average",
            f"I love {keyword}",
            f"I hate {keyword}"
        ]
        return [random.choice(samples) for _ in range(50)]

    if menu == "🏠 Home":
        keyword = st.text_input("Enter Keyword")
        uploaded = st.file_uploader("Upload a CSV, JSON, or JSONL Xquik export", type=["csv", "json", "jsonl"])

        if st.button("Analyze"):
            if uploaded:
                rows = load_xquik_rows(uploaded.getvalue())
                tweets = [row["tweet"] for row in rows]
            else:
                tweets = fake_tweets(keyword)

            sentiments = [get_sentiment(tweet) for tweet in tweets]
            df = pd.DataFrame({"Comment": tweets, "Sentiment": sentiments})
            st.session_state.df = df

            st.subheader("😊 Positive")
            st.dataframe(df[df["Sentiment"]=="Positive"])

            st.subheader("😡 Negative")
            st.dataframe(df[df["Sentiment"]=="Negative"])

            st.subheader("😐 Neutral")
            st.dataframe(df[df["Sentiment"]=="Neutral"])

    elif menu == "📊 Graph":
        df = st.session_state.df
        if df is not None:
            counts = df["Sentiment"].value_counts()

            fig, ax = plt.subplots(figsize=(2.2,1.3))
            ax.bar(counts.index, counts.values)
            ax.tick_params(labelsize=6)

            st.pyplot(fig, use_container_width=False)

    elif menu == "📄 Report":
        df = st.session_state.df
        if df is not None:
            st.dataframe(df)

            st.download_button(
                "Download PDF",
                create_pdf(df, "X Report"),
                "x_report.pdf"
            )

# ================= ABOUT =================
else:
    st.title("ℹ️ About Project")

    st.write("""
    📌 Social Media Sentiment Analyzer  

    👩‍💻 Developed By:
    - Kaklotar Mansi  
    - Kaklotar Hemanshi  
    - Patel Palak  

    🔹 YouTube + X sentiment analysis  
    🔹 Graph & trend visualization  
    🔹 PDF report with full comments  
    """)
