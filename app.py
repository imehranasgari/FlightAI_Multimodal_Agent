import gradio as gr
from database import init_db
from agent import run_agent_chat

def user_submit(user_message, history):
    if not user_message.strip():
        return "", history
    history = history or []
    history.append({"role": "user", "content": user_message})
    return "", history

def agent_respond(history, model_choice):
    # پاس دادن مدل انتخابی به هسته agent
    return run_agent_chat(history, model_choice)

def create_ui():
    init_db()
    
    with gr.Blocks(title="FlightAI - Multimodal Airline Agent") as demo:
        gr.Markdown("# ✈️ FlightAI Multimodal Agent")
        
        # نوار بالایی برای تنظیمات و انتخاب مدل
        with gr.Row():
            model_selector = gr.Dropdown(
                choices=["Gemini (Cloud)", "Ollama (Llama 3.2 Local)"],
                value="Gemini (Cloud)",
                label="Select AI Engine",
                interactive=True,
                scale=1
            )
            gr.Markdown("Ask about flight ticket prices (e.g., *'How much is a ticket to Tokyo?'*).")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Conversation", type="messages", height=450)
                with gr.Row():
                    user_input = gr.Textbox(
                        placeholder="Ask about flights, ticket prices, destinations...",
                        label="Your Query",
                        scale=8
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
                audio_output = gr.Audio(label="Voice Response (TTS)", autoplay=True)
            with gr.Column(scale=1):
                image_output = gr.Image(label="Destination Poster (Pop-Art)", interactive=False, height=520)

        gr.Examples(
            examples=[
                "How much is a ticket to London?",
                "What is the flight price to Tokyo?",
                "I want to travel to Paris, can you check the fare?"
            ],
            inputs=user_input
        )

        # ارسال پیام با اینتر (Enter)
        user_input.submit(
            user_submit,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        ).then(
            agent_respond,
            inputs=[chatbot, model_selector],  # افزودن model_selector به ورودی
            outputs=[chatbot, audio_output, image_output]
        )

        # ارسال پیام با کلیک روی دکمه Send
        send_btn.click(
            user_submit,
            inputs=[user_input, chatbot],
            outputs=[user_input, chatbot]
        ).then(
            agent_respond,
            inputs=[chatbot, model_selector],  # افزودن model_selector به ورودی
            outputs=[chatbot, audio_output, image_output]
        )

    return demo

if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="127.0.0.1", server_port=7860)