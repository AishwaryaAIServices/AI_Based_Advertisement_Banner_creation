import streamlit as st
import google.generativeai as genai
from PIL import Image
import io, os

from gradio_client import Client  # Import Gradio client

# 1) Configure Google Generative AI (Gemini 1.5 Flash)
genai.configure(api_key="AIzaSyCYp4KCJx_EyjbbYeatf5DqBfjO8IhPVOk")

st.title("Advertisement Banner Generator with Flux")

# -------------------------- SESSION STATE SETUP -------------------------- #
# We'll store some items in session_state so we can regenerate/download without losing data.
if "refined_prompt" not in st.session_state:
    st.session_state["refined_prompt"] = ""

if "last_image_bytes" not in st.session_state:
    st.session_state["last_image_bytes"] = None

if "model_prompt" not in st.session_state:
    st.session_state["model_prompt"] = None

# This function calls the FLUX-REALISM model
def generate_banner_flux(prompt, random_seed=True):
    """
    Generates an image using the FLUX-REALISM Gradio client.
    Returns (banner_image_bytes, error_message).
    """
    client = Client("prithivMLmods/FLUX-REALISM")

    try:
        result = client.predict(
            prompt=prompt,
            seed=0,
            width=1024,
            height=1024,
            guidance_scale=6,
            randomize_seed=random_seed,
            api_name="/run"
        )

        # result structure: ([{'image': '/tmp/...png', 'caption': None}], seed_int)
        images_data, random_seed_used = result

        if images_data and 'image' in images_data[0]:
            image_path = images_data[0]['image']  # e.g. /tmp/gradio/...
            banner_img = Image.open(image_path)
            # Convert to bytes for easy display & download
            img_buffer = io.BytesIO()
            banner_img.save(img_buffer, format="PNG")
            img_bytes = img_buffer.getvalue()
            return img_bytes, None
        else:
            return None, "No image returned from FLUX-REALISM model."
    except Exception as e:
        return None, f"Error while contacting FLUX-REALISM: {e}"

# -------------------------- UI: PROMPT REFINEMENT -------------------------- #
with st.form("ad_form"):
    st.header("Provide Advertisement Details")

    background_theme = st.text_input(
        "Background Theme", 
        placeholder="E.g., Minimalist, Luxury, Playful, Modern, Nature-inspired"
    )
    primary_colors = st.text_input(
        "Primary Colors", 
        placeholder="E.g., Blue, Red, Gold, Pastel shades, Gradient styles"
    )
    headline = st.text_input(
        "Main Headline", 
        placeholder="E.g., SALE NOW, Limited Time Offer"
    )
    subheading = st.text_input(
        "Subheading", 
        placeholder="E.g., Up to 70% OFF on all products"
    )
    cta = st.text_input(
        "Call to Action (CTA)", 
        placeholder="E.g., Shop Now, Sign Up Today"
    )
    product_type = st.text_input(
        "Brand or Product Type", 
        placeholder="E.g., Electronics, Fashion, Food & Beverages"
    )
    purpose = st.text_input(
        "Purpose of Advertisement", 
        placeholder="E.g., Promotion, Event Announcement, Product Launch"
    )
    target_audience = st.text_input(
        "Target Audience", 
        placeholder="E.g., Millennials, Families, Business Owners"
    )
    font_style = st.text_input(
        "Font Style Preference", 
        placeholder="E.g., Bold, Elegant, Playful, Minimal"
    )
    description = st.text_area(
        "Description of Advertisement", 
        placeholder="Provide a brief description of what you want to convey..."
    )

    submitted = st.form_submit_button("Generate and Refine Prompt")

if submitted:
    user_prompt = (
        f"Create an advertisement banner with a {background_theme} theme. "
        f"Use primary colors like {primary_colors}. "
        f"The banner should feature the headline: \"{headline}\", "
        f"with a subheading: \"{subheading}\", and a call-to-action: \"{cta}\". "
        f"Design it for a {product_type} product to {purpose}. "
        f"Keep the design appealing for {target_audience} using a {font_style} font style. "
        f"Description: {description}. "
        f"Ensure the design elements, text, and imagery convey the message clearly."
    )

    refinement_instructions = (
        "Generate a professional, detailed advertisement banner prompt based on the following user inputs. "
        "Ensure the description is concise, in single paragraph,limited to 6 lines, and includes: "
        "1. Purpose of the banner (e.g., promotion, event). "
        "2. Key text elements (headline, subheading, call to action). "
        "3. Visual design details (background, colors, font style). "
        "4. Target audience and brand type relevance. "
        "5. Any specific imagery or layout preferences mentioned by the user. "
        "Refine the text to make it polished, cohesive, and impactful."
    )

    # Call Gemini to refine the prompt
    model = genai.GenerativeModel("gemini-1.5-flash")
    with st.spinner("Refining your prompt with Gemini..."):
        response = model.generate_content(
            [f"{refinement_instructions}\n\nUser Input: {user_prompt}"]
        )

    refined_prompt = response.text.strip()
    st.session_state["refined_prompt"] = refined_prompt  # store for next step
    st.session_state["model_prompt"] = refined_prompt    # model uses refined prompt by default

# If we have a refined prompt, display it for editing
if st.session_state["refined_prompt"]:
    st.subheader("Refined Advertisement Prompt:")
    edited_prompt = st.text_area(
        "Edit the Prompt:", 
        value=st.session_state["refined_prompt"], 
        height=200
    )

    # Update our session state whenever the user edits
    st.session_state["model_prompt"] = edited_prompt

    # Button to generate the banner
    if st.button("Finalize Prompt and Generate Images"):
        st.info("Generating advertisement banner with Flux Realism. Please wait...")
        with st.spinner("Contacting FLUX-REALISM model..."):
            img_bytes, error_msg = generate_banner_flux(st.session_state["model_prompt"], random_seed=True)

        if error_msg:
            st.error(error_msg)
        else:
            # Store image bytes in session state
            st.session_state["last_image_bytes"] = img_bytes

            # Display it
            st.image(img_bytes, caption="Generated Advertisement Banner", use_column_width=True)
            st.success("Banner generation complete!")

# -------------------------- UI: REGENERATE / DOWNLOAD SECTION -------------------------- #
if st.session_state["last_image_bytes"]:
    st.write("---")
    st.write("### What would you like to do next?")
    col1, col2 = st.columns(2)

    with col1:
        # Regenerate button (calls the model again with a new random seed)
        if st.button("Regenerate New Banner"):
            st.info("Regenerating a new banner with a different seed...")
            with st.spinner("Generating..."):
                img_bytes, error_msg = generate_banner_flux(st.session_state["model_prompt"], random_seed=True)
            if error_msg:
                st.error(error_msg)
            else:
                st.session_state["last_image_bytes"] = img_bytes
                st.image(img_bytes, caption="Newly Generated Banner", use_column_width=True)
                st.success("Regeneration complete!")

    with col2:
        # Download button
        if st.session_state["last_image_bytes"] is not None:
            st.download_button(
                label="Download Banner",
                data=st.session_state["last_image_bytes"],
                file_name="advertisement_banner.png",
                mime="image/png"
            )
