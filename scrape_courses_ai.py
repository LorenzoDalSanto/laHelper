import requests
from bs4 import BeautifulSoup
from groq import Groq
from key import GROQ_API_KEY
import csv
import re


# Initialize the Groq client for LLM API calls
client = Groq(api_key=GROQ_API_KEY)

def extract_text_from_url(url):
    """
    Downloads the HTML content from a URL, cleans it of scripts and styles,
    and returns the plain text.

    Args:
        url (str): The URL of the web page to extract text from.

    Returns:
        str: The extracted text from the page.
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 404, 500)
    soup = BeautifulSoup(response.text, "html.parser")

    # Remove <script> and <style> tags, which do not contain useful information
    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    return text

def ask_ai_to_extract_courses(text):
    """
    Sends the extracted text to a language model (via Groq) to extract
    course information in CSV format.

    Args:
        text (str): The web page text to be analyzed.

    Returns:
        list: A list of strings, where each string is a CSV row of a course.
    """
    prompt = f"""
    Analyze the following webpage text and extract every university course mentioned.

    For each course, extract the following information **in this exact order**:
    1. Course name  
    2. Duration in hours  
    3. Credits (ECTS or CFU)  
    4. Faculty or Department  
    5. Language of instruction  
    6. Level (e.g., Bachelor, Master, PhD)

    Return the result as a CSV-style table where each field is separated by a semicolon `;` and each course is on a new line.

    The output **must follow this structure exactly**:

    Course Name;Duration (hours);Credits;Faculty;Language;Level

    If some information is not available, leave the field empty but keep the semicolon separators.
    Do not include any explanations, comments, or extra text before or after the table.
    Include header.

    Text to analyze:
    {text[:50000]}
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    content = response.choices[0].message.content.strip()

    # Clean the output to ensure we only have valid CSV lines
    lines = content.splitlines()
    clean_lines = [l for l in lines if ";" in l]
    return clean_lines

def save_courses_to_csv(courses_lines, filename="corsi_completi.csv"):
    """
    Saves the extracted course lines to a CSV file.

    Args:
        courses_lines (list): List of CSV strings, including the header.
        filename (str, optional): The name of the output file.
                                  Defaults to "corsi_completi.csv".
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter=";")

        if courses_lines:
            header = courses_lines[0].split(";")
            writer.writerow([h.strip() for h in header])
            for line in courses_lines[1:]:
                writer.writerow([c.strip() for c in line.split(";")])

def main():
    """
    Main function that orchestrates the scraping and AI analysis process.
    """
    # Example URL for course extraction (Vilnius University)
    url = "https://is.vu.lt/pls/pub/vustud.public_ni$wwwtprs.dalsar_show?p_lpd_srautas_id=43&p_pad_id=11&p_search_str=Bachelor&p_search_cols=1&p_search_cols=2&p_search_cols=3&p_search_cols=0&p_search_cols=5&p_search_cols=6&p_search_cols=0&p_search_cols=8&p_search_cols=9&p_search_cols=10&p_search_cols=11"  # you can change this to the page you want to test
    print("🔍 Extracting text from the page...")
    text = extract_text_from_url(url)

    print("🧠 Extracting courses and information via AI...")
    courses_lines = ask_ai_to_extract_courses(text)

    if courses_lines:
        print(f"💾 Saving {len(courses_lines) - 1} courses to 'corsi_completi.csv'...")
        save_courses_to_csv(courses_lines)
        print("✅ Done! Check the corsi_completi.csv file.")
    else:
        print("⚠️ No courses found or AI error.")

# Execute the main function only if the script is run directly
if __name__ == "__main__":
    main()
