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

# --- PDF Export ---
def save_recipe_as_pdf(recipe_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in recipe_text.split("\n"):
        pdf.multi_cell(0, 10, line)

    pdf_file = "recipe.pdf"
    pdf.output(pdf_file)
    return pdf_file

# --- Streamlit UI ---
def main():
    st.title("🍽️ AI Recipe Builder")

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
                    st.markdown(recipe)

                    # PDF export
                    pdf_file = save_recipe_as_pdf(recipe)
                    with open(pdf_file, "rb") as file:
                        st.download_button("📄 Download as PDF", file, file_name="recipe.pdf")

                    # Email/social share
                    encoded_text = urllib.parse.quote(recipe)
                    st.markdown("### 📤 Share Your Recipe")
                    st.markdown(f"[Send via Gmail](mailto:?subject=Recipe&body={encoded_text})")
                    st.markdown(f"[Share on WhatsApp](https://wa.me/?text={encoded_text})")
                    st.markdown(f"[Post on Twitter/X](https://twitter.com/intent/tweet?text={encoded_text})")

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please type something you're craving.")

if __name__ == "__main__":
    main()