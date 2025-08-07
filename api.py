#api.py
from flask import Flask, jsonify, render_template, request
import cv2
import random
from fer import FER

app = Flask(__name__)

# Multilingual Emotion → Story mapping
story_map = {
    "happy": {
        "en": "Your smile lit up the day like a morning sun 🌞",
        "ta": "உங்கள் புன்னகை காலை சூரியனைப் போல பிரகாசித்தது 🌞",
        "hi": "आपकी मुस्कान ने दिन को सुबह के सूरज की तरह रोशन कर दिया 🌞",
        "te": "మీ చిరునవ్వు ఉదయపు సూర్యుడిలా రోజును వెలుగులోకి తెచ్చింది 🌞",
        "ml": "നിന്റെ പുഞ്ചിരി രാവിലെ സൂര്യനെപ്പോലെ പ്രകാശിച്ചു 🌞",
        "de": "Dein Lächeln hat den Tag wie die Morgensonne erhellt 🌞",
        "fr": "Ton sourire a illuminé la journée comme un soleil du matin 🌞",
        "ja": "あなたの笑顔は朝の太陽のように一日を明るくしました 🌞",
        "zh": "你的微笑如清晨的太阳照亮了整天 🌞",
        "es": "Tu sonrisa iluminó el día como el sol de la mañana 🌞"
    },
    "sad": {
        "en": "Even the rain understands how you feel today 🌧️",
        "ta": "இன்று உங்கள் உணர்வுகளை மழையும் புரிகிறது 🌧️",
        "hi": "आज आपकी भावनाओं को बारिश भी समझती है 🌧️",
        "te": "ఈ రోజు మీరు ఎలా భావిస్తున్నారో వర్షం కూడా అర్థం చేసుకుంటుంది 🌧️",
        "ml": "ഇന്ന് നിന്റെ മനസ്സറിയാൻ മഴക്കുമാകും 🌧️",
        "de": "Sogar der Regen versteht heute, wie du dich fühlst 🌧️",
        "fr": "Même la pluie comprend ce que tu ressens aujourd’hui 🌧️",
        "ja": "今日のあなたの気持ちを雨もわかってくれる 🌧️",
        "zh": "连雨也懂你今天的感受 🌧️",
        "es": "Incluso la lluvia entiende cómo te sientes hoy 🌧️"
    },
    "angry": {
        "en": "Take a breath... the storm inside you will pass 🌩️",
        "ta": "ஒரு மூச்சை இழுக்கவும்... உங்களுள் உள்ள புயல் கடந்து போகும் 🌩️",
        "hi": "एक गहरी सांस लें... आपके भीतर का तूफान गुजर जाएगा 🌩️",
        "te": "ఒక గట్టిగా శ్వాస తీసుకోండి... మీలో ఉన్న పిడుగు క్రమంగా తగ్గుతుంది 🌩️",
        "ml": "ഒരു ശ്വാസം എടുക്കൂ... നിങ്ങളുടെ ഉള്ളിലെ കാറ്റ് കടക്കും 🌩️",
        "de": "Atme tief durch... der Sturm in dir wird vorübergehen 🌩️",
        "fr": "Respire... la tempête en toi finira par passer 🌩️",
        "ja": "深呼吸して… あなたの中の嵐はやがて過ぎ去ります 🌩️",
        "zh": "深呼吸……你内心的风暴终将过去 🌩️",
        "es": "Respira... la tormenta dentro de ti pasará 🌩️"
    },
    "neutral": {
        "en": "Peaceful as a silent library 📘",
        "ta": "அமைதியான நூலகம் போல அமைதி 📘",
        "hi": "एक शांत पुस्तकालय की तरह शांत 📘",
        "te": "నిశ్శబ్ద గ్రంథాలయం వలె శాంతంగా 📘",
        "ml": "നിശ്ബ്ദമായ ലൈബ്രറിയെപ്പോലെ സമാധാനം 📘",
        "de": "Friedlich wie eine stille Bibliothek 📘",
        "fr": "Paisible comme une bibliothèque silencieuse 📘",
        "ja": "静かな図書館のように平和 📘",
        "zh": "像寂静的图书馆一样平静 📘",
        "es": "Pacífico como una biblioteca silenciosa 📘"
    },
    "fear": {
        "en": "Courage doesn’t mean no fear, it means moving forward anyway 🦁",
        "ta": "தைரியம் என்பது பயமில்லை என்பதல்ல, பயத்தை எதிர்கொள்வதே 🦁",
        "hi": "साहस का मतलब डर नहीं होना नहीं, बल्कि डर के बावजूद आगे बढ़ना है 🦁",
        "te": "ధైర్యం అంటే భయం లేకపోవడం కాదు, అయినా ముందుకు సాగడమే 🦁",
        "ml": "ധൈര്യം ഭയം ഇല്ലായ്മയല്ല, ഭയത്തെയും നേരിട്ട് മുന്നോട്ട് പോകലാണ് 🦁",
        "de": "Mut bedeutet nicht keine Angst zu haben, sondern trotzdem weiterzumachen 🦁",
        "fr": "Le courage, ce n’est pas l’absence de peur, mais avancer malgré elle 🦁",
        "ja": "勇気とは恐れがないことではなく、それでも前進することです 🦁",
        "zh": "勇气不是没有恐惧，而是仍然向前 🦁",
        "es": "El coraje no es no tener miedo, sino avanzar a pesar de él 🦁"
    },
    "surprise": {
        "en": "Something unexpected is brewing in your stars ✨",
        "ta": "உங்கள் நட்சத்திரங்களில் எதிர்பாராத ஒன்று உருவாகுகிறது ✨",
        "hi": "आपके सितारों में कुछ अप्रत्याशित घट रहा है ✨",
        "te": "మీ నక్షత్రాల్లో ఏదో అప్రతീക്ഷితంగా జరగబోతుంది ✨",
        "ml": "നിന്റെ നക്ഷത്രങ്ങളിൽ പ്രതീക്ഷിക്കാത്തതു വീഴുന്നു ✨",
        "de": "Etwas Unerwartetes braut sich in deinen Sternen zusammen ✨",
        "fr": "Quelque chose d’inattendu se prépare dans tes étoiles ✨",
        "ja": "あなたの星に何か予想外のことが起きています ✨",
        "zh": "你的星象中正在酝酿一些意想不到的事 ✨",
        "es": "Algo inesperado se está gestando en tus estrellas ✨"
    },
    "disgust": {
        "en": "That didn’t sit right, did it? Let's shake it off 🧼",
        "ta": "அது சும்மா இல்லை அல்லவா? அதை கழுவிவிடலாம் 🧼",
        "hi": "वो ठीक नहीं लगा ना? चलो उसे निकाल फेंकते हैं 🧼",
        "te": "అది సరైనట్లు అనిపించలేదా? విడిచి వేయండి 🧼",
        "ml": "അത് ശരിയില്ലെന്നു തോന്നിയോ? അതിനെ നീക്കാം 🧼",
        "de": "Das fühlte sich nicht richtig an, oder? Lass es uns abschütteln 🧼",
        "fr": "Ça ne semblait pas correct, hein ? Secouons ça 🧼",
        "ja": "それ、ちょっと変だったよね？振り払おう 🧼",
        "zh": "感觉怪怪的对吧？甩掉它吧 🧼",
        "es": "Eso no estuvo bien, ¿verdad? Sacúdelo 🧼"
    }
}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/moodify', methods=['GET'])
def moodify():
    try:
        print("🎥 Starting enhanced FER emotion detection...")

        detector = FER(mtcnn=False)
        cap = cv2.VideoCapture(0)

        emotion_totals = {emo: 0 for emo in story_map}
        emotion_counts = {emo: 0 for emo in story_map}
        frames_to_capture = 15
        valid_frames = 0

        for i in range(frames_to_capture):
            ret, frame = cap.read()
            if not ret:
                continue

            results = detector.detect_emotions(frame)
            if results:
                top_result = results[0]['emotions']
                top_emotion = max(top_result, key=top_result.get)
                top_score = top_result[top_emotion]

                if top_score > 0.2:
                    emotion_totals[top_emotion] += top_score
                    emotion_counts[top_emotion] += 1
                    valid_frames += 1

                print(f"🧠 Frame {i+1}: {top_result} → Top: {top_emotion} ({top_score:.2f})")
            else:
                print(f"⚠️ Frame {i+1} - No face detected")

        cap.release()

        if valid_frames == 0:
            return jsonify({"emotion": "unknown", "story": "No face detected. Please try again!"}), 500

        weighted_scores = {
            emo: emotion_totals[emo] * emotion_counts[emo]
            for emo in emotion_totals if emotion_counts[emo] > 0
        }

        print("📊 Weighted Emotion Scores:")
        for emo, score in weighted_scores.items():
            print(f"{emo.upper():<10}: {score:.2f}")

        final_emotion = max(weighted_scores, key=weighted_scores.get) if weighted_scores else "neutral"

        lang_code = request.args.get("lang", "en")[:2]
        story = story_map.get(final_emotion, {}).get(lang_code, story_map[final_emotion]["en"])

        print(f"✅ Final Detected Emotion: {final_emotion}")
        return jsonify({"emotion": final_emotion, "story": story})

    except Exception as e:
        print("❌ EXCEPTION:", e)
        return jsonify({"emotion": "error", "story": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
