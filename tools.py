# Function to extract Product Title
def get_title(soup):

    try:
        # Outer Tag Object
        title = soup.find("span", attrs={"id":'productTitle'})
        
        # Inner NavigatableString Object
        title_value = title.text

        # Title as a string value
        title_string = title_value.strip()

    except AttributeError:
        title_string = ""

    return title_string

# Function to extract Product Price
def get_price(soup):

    try:
        price = soup.find("span", attrs={"class":'a-price-whole'})
        price_value = price.text
        price_string = '₹' + price_value.strip()
        
    except AttributeError:
            price_string = ""

    return price_string

# Function to extract Product Rating
def get_rating(soup):

    try:
        rating = soup.find("i", attrs={'class':'a-icon a-icon-star a-star-4-5'}).string.strip()
    
    except AttributeError:
        try:
            rating = soup.find("span", attrs={'class':'a-icon-alt'}).string.strip()
        except:
            rating = ""	

    return rating

# Function to extract Number of User Reviews
def get_review_count(soup):
    try:
        review_count = soup.find("span", attrs={'id':'acrCustomerReviewText'}).string.strip()

    except AttributeError:
        review_count = ""	

    return review_count

# Function to extract Availability Status
def get_availability(soup):
    try:
        available = soup.find("div", attrs={'id':'availability'})
        available = available.find("span").string.strip()

    except AttributeError:
        available = "Not Available"	

    return available

def get_delivery_time(soup):
    try:
        delivery_time = soup.find("div", attrs={"class":'a-section a-spacing-none a-padding-none'}).find("div", attrs={"id": "deliveryBlockMessage"}).find("div", attrs={"class": "a-spacing-base"}).find('span', class_='a-text-bold').text.strip()
    except AttributeError:
        delivery_time = ""
    
    return delivery_time

def get_size(soup):

    dropdown = soup.find("select", {"id": "native_dropdown_selected_size_name"})

    if dropdown:
        # Extract only available sizes (exclude unavailable ones)
        sizes = [
            option.text.strip()
            for option in dropdown.find_all("option")
            if "dropdownUnavailable" not in option.get("class", []) and option.get("value") != "-1"
        ]
        
    else:
        sizes = ""
        
    return sizes

def get_return_policy(soup):
    return_policy_title = soup.find("h2", class_="a-size-medium return-policy-title").get_text(strip=True)

    # Extract the return policy table
    table = soup.find("table", class_="a-keyvalue")
    rows = table.find_all("tr")[1:]  # Skipping the header row

    return_policies = []
    for row in rows:
        cols = [col.get_text(strip=True) for col in row.find_all("td")]
        return_policies.append(cols)

    # Extract return instructions
    return_instructions = soup.find("div", class_="a-column a-span8 a-text-left").get_text(strip=True)
    
    return {"Return Policy Title": return_policy_title, "Return Instruction": return_instructions}
