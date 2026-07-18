import pyttsx3
import speech_recognition as sr

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("🎤 Speak something...")
    recognizer.adjust_for_ambient_noise(source)

    audio = recognizer.listen(source)

try:
    text = recognizer.recognize_google(audio, language="en-IN")
    print("You said:", text)
    engine = pyttsx3.init()
engine.say("Hello Priya, your microphone is working perfectly.")
engine.runAndWait()

except Exception as e:
    print("Error Type:", type(e).__name__)
    print("Error Message:", repr(e))