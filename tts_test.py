import pyttsx3

engine = pyttsx3.init()

engine.say("Hello Priya. This is a text to speech test.")

engine.runAndWait()

print("Done")