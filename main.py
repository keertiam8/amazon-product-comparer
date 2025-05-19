
import streamlit as st
import time
from langchain.chat_models import ChatOpenAI
from bs4 import BeautifulSoup
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options  
import time
from bs4 import BeautifulSoup
import re

from dotenv import load_dotenv
load_dotenv() 

st.title("Amazon Product Comparer")
st.sidebar.title("Amazon Products URL")

if "product_data" not in st.session_state:
    st.session_state.product_data = []

chrome_options = Options()
chrome_options.add_argument("--headless") 
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox") 

driver = webdriver.Chrome(options=chrome_options)

urls = []
for i in range(3):
    url = st.sidebar.text_input(f"URL {i+1}")
    urls.append(url)

product_data = []
process_url_clicked = st.sidebar.button("Process URLs")

if process_url_clicked:
    st.session_state.product_data = [] 
    st.sidebar.write("Processing URLs...")


    for i, url in enumerate(urls, start=1):
        try:
            driver.get(url)
            time.sleep(2)

            center_col = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "centerCol"))
            )
            right_col = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "rightCol"))
            )

            center_col_html = center_col.get_attribute('outerHTML')
            right_col_html = right_col.get_attribute('outerHTML')

            combined_html = center_col_html + right_col_html
            soup = BeautifulSoup(combined_html, "html.parser")

          
            title_tag = soup.find(id='productTitle')
            title = title_tag.get_text(strip=True) if title_tag else "No title found"

            price_tag = soup.find('span', class_='a-price-whole')
            price = price_tag.get_text(strip=True) if price_tag else "Price not found"

            rating_tag = soup.find('span', class_='a-icon-alt')
            rating = rating_tag.get_text(strip=True) if rating_tag else "No rating found"

            reviews_tag = soup.find('span', id='acrCustomerReviewText')
            reviews = reviews_tag.get_text(strip=True) if reviews_tag else "No reviews found"

            amazons_choice = "No"
            for tag in soup.find_all(['div', 'span']):
                tag_text = tag.get_text(separator=' ', strip=True)
                if "Amazon's Choice" in tag_text:
                    amazons_choice = "Yes"
                    break

            text = soup.get_text(separator=' ', strip=True)

            offers_match = re.search(r'(\d+)\s*percent savings.*?-?\s*(₹[\d,]+)', text, re.IGNORECASE)
            if offers_match:
                offers = f"{offers_match.group(1)}% savings ({offers_match.group(2)})"
            else:
                offers = "No offers found"

            delivery_match = re.search(r'(FREE delivery|Get it by)[^\n,]+(?: to [^\n]+)?', text)
            delivery_info = delivery_match.group() if delivery_match else "No delivery info found"

            bought_match = re.search(r'([\d,]+[\+]?)[ ]*bought in past month', text, re.IGNORECASE)
            bought = bought_match.group(0) if bought_match else "No purchase data found"

            product_details = {
                'Title': title,
                'Price': price,
                'Rating': rating,
                'Reviews': reviews,
                'Offers': offers,
                'Delivery Info': delivery_info,
                'Amazon\'s Choice': amazons_choice,
                'Bought': bought,
                'URL': url
            }

            st.session_state.product_data.append(product_details)


        except Exception as e:
            print(f"Error processing URL {url}: {e}")
            continue
        st.sidebar.write(f"Processed URL {i}/{len(urls)}")
    st.sidebar.write("All URLs processed.")

driver.quit()


main_placeholder = st.empty()
query = main_placeholder.text_input("Question: ")

if query and st.session_state.product_data:
    product_gpt_format = "\n".join([
        f"--- Product {i} ---\n" + "\n".join([f"{key}: {value}" for key, value in product.items()])
        for i, product in enumerate(st.session_state.product_data, start=1)
    ])

    products_text = product_gpt_format

    prompt = f"""You are an assistant with access to the following Amazon products data:

{products_text}

Answer the following question based ONLY on the above data.

When choosing the best product, consider but do not limit yourself to the following factors:
- Price
- Rating and reviews
- Offers and savings
- Delivery information (faster delivery)
- Popularity (how many people bought it)

In your answer, also specify the URL of the product you think is the best fit for the question.

Question: {query}
"""
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o-mini"
    )

    answer = llm.predict(prompt)
    st.header("Answer")
    st.write(answer)