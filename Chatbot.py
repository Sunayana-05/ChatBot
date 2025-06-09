import google.generativeai as genai  # pip install google-generativeai
import pyttsx3  # pip install pyttsx3
import tkinter as tk
from tkinter import ttk
import threading
from apikey import api_data  # Your apikey.py file should have: api_data = "your-api-key"

# Configure Gemini API
GENAI_API_KEY = api_data
genai.configure(api_key=GENAI_API_KEY)

# Initialize TTS engine
engine = pyttsx3.init('sapi5')
engine.setProperty('voice', engine.getProperty('voices')[0].id)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def generate_response(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=500,
                temperature=0.2,
            )
        )
        return response.text
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"

class ChatApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Chatbot")
        self.geometry("1000x600")
        self.minsize(600, 400)
        self.configure(bg="#F0F8FF")

        self.conversation_history = []

        # Main frame
        main_frame = tk.Frame(self, bg="#F0F8FF")
        main_frame.pack(fill="both", expand=True)

        # Canvas for scrolling chat
        self.canvas = tk.Canvas(main_frame, bg="#F0F8FF", highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#F0F8FF")

        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Input frame at bottom
        input_frame = tk.Frame(self, bg="#F0F8FF")
        input_frame.pack(fill="x", padx=10, pady=10, side="bottom")

        self.user_input = tk.Text(input_frame, font=("Arial", 12), height=2, wrap="word")
        self.user_input.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.user_input.focus()
        self.user_input.bind("<Return>", self.on_enter_pressed)

        send_btn = tk.Button(input_frame, text="Send", font=("Arial", 12), command=self.send_message)
        send_btn.pack(side="left", padx=(0, 5))

        end_btn = tk.Button(input_frame, text="End Chat", font=("Arial", 12), command=self.end_chat)
        end_btn.pack(side="left")

        self.msg_row = 0

        # Welcome message
        welcome_text = "Hi, I am Sam. How can I help you?"
        self.add_message(f"Sam: {welcome_text}", is_user=False)
        self.conversation_history.append(("bot", welcome_text))
        threading.Thread(target=speak, args=(welcome_text,), daemon=True).start()

    def on_enter_pressed(self, event):
        if event.state & 0x0001:  # Shift held
            return  # allow newline
        else:
            self.send_message()
            return "break"  # prevent newline

    def add_message(self, text, is_user=True):
        self.update_idletasks()
        max_width = int(self.winfo_width() * 0.8)
        padding_x = 10
        padding_y = 5
        radius = 45

        wrapper_frame = tk.Frame(self.scrollable_frame, bg="#F0F8FF")
        wrapper_frame.grid(row=self.msg_row, column=0, sticky="ew", pady=5, padx=10)
        wrapper_frame.grid_columnconfigure(0, weight=1)
        wrapper_frame.grid_columnconfigure(1, weight=1)
        self.msg_row += 1

        bubble_frame = tk.Frame(wrapper_frame, bg="#F0F8FF")
        column = 1 if is_user else 0
        bubble_frame.grid(row=0, column=column, sticky="e" if is_user else "w")

        # Dummy label to measure size
        label = tk.Label(bubble_frame, text=text, font=("Arial", 12), wraplength=max_width, justify="left")
        label.pack()
        self.update_idletasks()

        w = label.winfo_width() + padding_x * 2
        h = label.winfo_height() + padding_y * 2
        label.destroy()

        bubble = tk.Canvas(bubble_frame, width=w, height=h, bg="#F0F8FF", highlightthickness=0)
        bubble.pack()

        bg_color = "#000101" if is_user else "#E6E6E6"
        fg_color = "#00FFFF" if is_user else "#333333"

        self.round_rectangle(bubble, 0, 0, w, h, radius, fill=bg_color, outline=bg_color)
        bubble.create_text(w // 2, h // 2, text=text, fill=fg_color, font=("Arial", 12), width=max_width)

        self.canvas.yview_moveto(1)

    def round_rectangle(self, canvas, x1, y1, x2, y2, r=30, **kwargs):
        points = [
            x1+r, y1,
            x2-r, y1,
            x2, y1,
            x2, y1+r,
            x2, y2-r,
            x2, y2,
            x2-r, y2,
            x1+r, y2,
            x1, y2,
            x1, y2-r,
            x1, y1+r,
            x1, y1,
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    def send_message(self):
        query = self.user_input.get("1.0", tk.END).strip()
        if not query:
            return
        self.user_input.delete("1.0", tk.END)
        self.add_message(f"You: {query}", is_user=True)
        self.conversation_history.append(("user", query))

        def respond():
            prompt = ""
            for speaker, text in self.conversation_history:
                if speaker == "user":
                    prompt += f"User: {text}\n"
                else:
                    prompt += f"Sam: {text}\n"
            prompt += "Sam:"

            response = generate_response(prompt)
            self.add_message(f"Sam: {response}", is_user=False)
            self.conversation_history.append(("bot", response))
            speak(response)

        threading.Thread(target=respond, daemon=True).start()

    def end_chat(self):
        goodbye = "Conversation ended.Goodbye!"
        self.add_message(f"Sam: {goodbye}", is_user=False)
        threading.Thread(target=speak, args=(goodbye,), daemon=True).start()
        self.after(2000, self.destroy)

if __name__ == "__main__":
    app = ChatApp()
    app.mainloop()
