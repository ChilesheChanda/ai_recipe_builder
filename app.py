import streamlit as st
from openai import OpenAI
import urllib.parse
from fpdf import FPDF

# --- Load OpenAI API key ---
api_key = st.secrets["OPENAI_API_KEY"]
openai_client = OpenAI(api_key=api_key)
MODEL = "gpt-4o-mini"

# --- Recipe Generator Function ---
def get_recipe_suggestion(craving, dietary_filters, prep_time, cook_time, language):
    system_prompt = f"""
    You are a helpful and multilingual recipe assistant.
    Based on user input, generate a delicious recipe in {language}.
    Consider any dietary restrictions and stay within the time constraints.
    Include:
    - Title
    - Ingredients
    - Step-by-step Instructions
    - Suggested side dishes (2-3)
    """

    filters = ", ".join(dietary_filters) if dietary_filters else "no restrictions"
    user_prompt = f"""
    I feel like eating {craving}.
    Please make it {filters}.
    Maximum prep time: {prep_time} minutes.
    Maximum cook time: {cook_time} minutes.
    Respond in {language}.
    """

    response = openai_client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    return response.choices[0].message.content.strip()

# --- PDF Export Class ---
class PDFRecipe(FPDF):
    def __init__(self):
        super().__init__()
        self.add_font("NotoSans", "", "NotoSans-Regular.ttf", uni=True)
        self.add_font("NotoSans", "B", "NotoSans-Bold.ttf", uni=True)
        self.set_margins(10, 10, 10)
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        self.set_font("NotoSans", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "🍽️ AI Recipe", ln=True, align="C")
        self.ln(5)

    def chapter_title(self, title):
        self.set_font("NotoSans", "B", 14)
        self.set_text_color(0, 102, 204)
        self.cell(0, 10, title, ln=True)
        self.ln(2)

    def chapter_body(self, body):
        self.set_font("NotoSans", "", 12)
        self.set_text_color(50, 50, 50)

        for line in body.split("\n"):
            if line.strip():
                try:
                    self.multi_cell(0, 8, line.strip(), max_line_height=self.font_size)
                except RuntimeError:
                    self.multi_cell(0, 8, line.strip(), split_only=True)
            else:
                self.ln(2)
        self.ln()

# --- Save as PDF ---
def save_recipe_as_pdf(recipe_text):
    pdf = PDFRecipe()
    pdf.add_page()

    sections = {"Title": "", "Ingredients": "", "Instructions": "", "Side Dishes": ""}
    current_section = "Title"

    for line in recipe_text.split("\n"):
        line = line.strip()
        if line.lower().startswith("ingredients"):
            current_section = "Ingredients"
        elif line.lower().startswith("instructions") or line.lower().startswith("directions"):
            current_section = "Instructions"
        elif "side dish" in line.lower():
            current_section = "Side Dishes"
        else:
            if sections[current_section]:
                sections[current_section] += "\n" + line
            else:
                sections[current_section] = line

    if sections["Title"]:
        pdf.chapter_title(sections["Title"])
    if sections["Ingredients"]:
        pdf.chapter_title("🧂 Ingredients")
        pdf.chapter_body(sections["Ingredients"])
    if sections["Instructions"]:
        pdf.chapter_title("👩‍🍳 Instructions")
        pdf.chapter_body(sections["Instructions"])
    if sections["Side Dishes"]:
        pdf.chapter_title("🍽️ Suggested Side Dishes")
        pdf.chapter_body(sections["Side Dishes"])

    pdf_file = "recipe.pdf"
    pdf.output(pdf_file)
    return pdf_file

# --- Streamlit App UI ---
def main():
    st.title("🍽️ AI Recipe Builder")
    st.markdown("Tell me what you're craving, and I'll suggest a recipe + sides!")

    craving = st.text_input("What do you feel like eating?", placeholder="e.g., fried chicken")

    dietary_filters = st.multiselect(
        "Select dietary preferences (optional):",
        ["Vegan", "Vegetarian", "Gluten-Free", "Keto", "Low-Carb"]
    )

    prep_time = st.slider("Maximum prep time (minutes):", 5, 120, 30)
    cook_time = st.slider("Maximum cook time (minutes):", 5, 180, 45)

    language = st.selectbox("Language for recipe output:", ["English", "Spanish", "French", "German", "Italian"])

    if st.button("Get Recipe"):
        if craving:
            with st.spinner("Cooking up something special..."):
                try:
                    recipe = get_recipe_suggestion(craving, dietary_filters, prep_time, cook_time, language)
                    st.markdown("## 🍳 Your Recipe")
                    st.markdown(recipe)

                    # PDF Export
                    pdf_file = save_recipe_as_pdf(recipe)
                    with open(pdf_file, "rb") as file:
                        st.download_button("📄 Download Recipe as PDF", file, file_name="recipe.pdf")

                    # Share Options
                    encoded_text = urllib.parse.quote(recipe)
                    st.markdown("### 📤 Share Your Recipe")
                    st.markdown(f"[📧 Send via Gmail](mailto:?subject=AI Recipe&body={encoded_text})")
                    st.markdown(f"[💬 Share on WhatsApp](https://wa.me/?text={encoded_text})")
                    st.markdown(f"[🐦 Post on Twitter/X](https://twitter.com/intent/tweet?text={encoded_text})")

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please type something you're craving.")

if __name__ == "__main__":
    main()
