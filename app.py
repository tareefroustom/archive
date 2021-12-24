#Import libraries
import streamlit as st
import requests
import benepar
import random
import spacy
import json
import nltk

from tqdm import tqdm
from bs4  import BeautifulSoup

#Load benpar
if "Benpar" not in st.session_state:
    benepar.download('benepar_en3')
    st.session_state["Benpar"] = 1

#Configure the app web page
st.set_page_config(
    #This is the title of the page
    page_title="Medview",
    #This is the string representation of the app icon
    page_icon="chart_with_upwards_trend",
)

#Initiate and load the Google Font we are using
st.markdown("""<head><link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Titillium Web"><style> body { font-family: "Titillium Web", sans-serif;} </style></head>""",unsafe_allow_html=True)


#The app Title, Description, and Instructions
#Title
st.title("Medview: Patient reported insights")

Describe, Purpose = st.columns(2)
#Instructions
with Purpose:
    st.markdown("""<div style="font-size: 16px; font-family:Titillium Web">Medview lets you know how your products and those of your competitors are perceived by patients.</div>""", unsafe_allow_html=True)

#Description
with Describe:
    st.markdown("""<div style="font-size: 16px; font-family:Titillium Web">Collect reviews from Drugs.com, analyze, and visualize them using Medview. Enter a product's name in the search bar belwo to start.</div>""", unsafe_allow_html=True)

#First Seperator
st.markdown("""---""")

#Load Healthsea
Appover, Searchbar = st.columns([2,2])

if "model" not in st.session_state:
    nlp = spacy.load("en_healthsea")
    st.session_state["model"] = nlp
else:
    nlp = st.session_state["model"]



with Appover:
    #An over view of the application's flow
    st.markdown("""<div style="font-size: 14px; font-family:Titillium Web">it takes on average 6 seconds per result so we've limited the number of retrieved results to 50, if you want to try it on more, please get in touch at <a href="https://www.linkedin.com/in/tareef-roustom-4952191b9/">Tareef</a>.</div>""", unsafe_allow_html=True)

#The user entered search term
Searchterm = Searchbar.text_input(label="Enter a product's name", value="Remicade")


st.text("")
st.text("")
st.text("")
st.text("")
st.text("")



#This functions gets the comments' main text out of the HTML code
def Commentdata(Comment):
    try:
        Commentmetadata = {"text": " ".join(Comment.split(":")[1:]),
                           "condition": (Comment.split(":")[0]).split("for")[1]}
    except:
        Commentmetadata = {"text": " ".join(Comment.split(":")[1:]),
                           "condition": (Comment.split(":")[0]).split("For")[1]}

    return Commentmetadata

def Processdoc(Text):
    doc = nlp(Text)
    effects = []
    for effect in doc._.health_effects:
        effects.append(f"{doc._.health_effects[effect]['effect']} {effect}".lower())
    return effects

#This function scrapes Drugs.com
def GetComments(Searchterm, Page):

    Loadpage = True
    Comments = []

    for Pagenumber in tqdm(range(0, Page)):

        if Loadpage:

            Search_URL = "https://www.drugs.com/search.php?searchterm=" + Searchterm

            # The search's homepage
            page = requests.get(Search_URL)
            soup = BeautifulSoup(page.content, "html.parser")
            results = soup.find(class_="ddc-media-list")

            # medicine's homepage url
            try:
                medpage = results.find_all("a")[0]["href"]
            except:
                st.warning("It seems you've entered a mis-spelled product name, unfortuantely at the moment Medview doesn't support spell checking, autocorrection or autocomplete, these feature will be coming soon, but till then please check the spelling. 🎋")
                break
            # The medicine's homepage
            page = requests.get(medpage)
            soup = BeautifulSoup(page.content, "html.parser")
            results = soup.find(class_="ddc-rating-summary")

            # The comments' page url
            reviews = "https://www.drugs.com" + results.find_all("a")[0]["href"] + "/?page="+ str(Pagenumber)

            # The comments' homepage
            page = requests.get(reviews)
            soup = BeautifulSoup(page.content, "html.parser")
            nextpage = soup.find_all(class_="ddc-paging-item-next")
            results = soup.find_all(class_="ddc-comment ddc-box ddc-mgb-2")

            if not nextpage:
                Loadpage = False


            for result in results:
                reviewtext = result.find_all("p")[0].text.replace("\t", "").replace("“", "").replace("”", "")
                reviewmetadata = Commentdata(reviewtext)

                spantext = ""

                for span in result.find_all("span"):
                    spantext += span.text + "$"

                reviewduration = "N/A"
                reviewscore = "N/A"
                reviewdate = "N/A"

                for Chunk in spantext.split("$"):
                    if "Taken" in Chunk:
                        reviewduration = Chunk

                    if "/" in Chunk:
                        reviewscore = Chunk

                    if "," in Chunk:
                        reviewdate = Chunk

                Comments.append({"text": reviewmetadata["text"], "date": reviewdate, "score": reviewscore,
                                "condition": reviewmetadata["condition"], "review duration": reviewduration, "effects": Processdoc(reviewmetadata["text"])})

    #with open('Medview.json', 'w') as outfile:
    #    json.dump(Comments, outfile)

    return (Comments, results)



def Visualize(Comments, Search_Term):
    # Chunck to count the conditions and retrieve the "value"
    all_effect_get_value = []
    for first_layer_comment in Comments[0]:
        if first_layer_comment["text"] != "N/A":
            all_effect_get_value.extend(first_layer_comment["effects"])  #

    first_layer = []

    first_layer_children = []
    #my_bar = st.progress(0)
    for first_layer_comment in tqdm(Comments[0]):
        #my_bar.progress(index + (index/100))
        if first_layer_comment["condition"] != "N/A":

            second_layer_children = []

            for second_layer_comment in Comments[0]:
                if first_layer_comment["condition"] == second_layer_comment["condition"]:

                    for effect in second_layer_comment["effects"]:

                        appendefect = True
                        for x in second_layer_children:
                            if effect == x["name"]:
                                appendefect = False

                        if appendefect and Search_Term.lower() not in effect.lower():

                            if "negative" in effect.lower():
                                LayerColor = "#C84B31"
                            if "neutral" in effect.lower():
                                LayerColor = "#ECDBBA"
                            if "positive" in effect.lower():
                                LayerColor = "#2D4263"

                            second_layer_children.append({"name": effect, "itemStyle": {'color': LayerColor},
                                                          "value": all_effect_get_value.count(effect)})

            append = True
            for x in first_layer_children:
                if first_layer_comment["condition"] == x["name"]:
                    append = False

            if append:
                first_layer_children.append({"name": first_layer_comment["condition"], "itemStyle": {'color': "#676FA3"},
                                             "children": second_layer_children})

    first_layer.append({"name": Search_Term, "itemStyle": {'color': "#CDDEFF"}, "children": first_layer_children})

    #with open('Medview.json', 'w') as outfile:
    #    json.dump(first_layer, outfile)

    return first_layer

if Searchterm:
    Comments = GetComments(Searchterm, 2)

    data = Visualize(Comments, Searchterm)

    from streamlit_echarts import st_echarts

    option = {
        "title": {
            "text": "",
            "subtext": f"Nothing",
            "textStyle": {"fontSize": 90, "align": "center"},
            "subtextStyle": {"align": "center"},
            "sublink": "https://worldcoffeeresearch.org/work/sensory-lexicon/",
        },
        "series": {
            "type": "sunburst",
            "data": data,
            "radius": [0, "90%"],
            "sort": None,
            "emphasis": {"focus": "ancestor"},
            "levels": [
                {},
                {
                    "r0": "20%",
                    "r": "35%",
                    "itemStyle": {"borderWidth": 5},
                    "label": {"rotate": "tangential", "fontFamily" : 'Helvetica', "color": "#000B49"},
                },
                {"r0": "35%", "r": "45%", "label": {"align": "right", "fontFamily" : 'Helvetica', "color": "#000B49"}, "itemStyle": {"borderWidth": 5}},
                {
                    "r0": "45%",
                    "r": "55%",
                    "label": {"position": "outside", "padding": 3, "silent": False, "fontFamily" : 'Helvetica', "backgroundColor":"#F5F5F5", "borderRadius":5},
                    "itemStyle": {"borderWidth": 5},
                },
            ],
        },
    }
    st_echarts(option, height="700px")


    with st.expander("Reviews"):

        for index, Comment in enumerate(Comments[0]):
            #Meta Data
            text = Comment["text"].replace("\n","")

            st.markdown(f"""<div style=" color: #161853; font-size: 12px; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{text}</div>""", unsafe_allow_html=True)

            st.markdown(f"""<span style=" color: #161853; font-size: 20px; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{Comment["score"]}</span><span style=" color: #161853; font-size: 12px; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{Comment["review duration"]}</span>""", unsafe_allow_html=True)

            effects = ""
            for effect in Comment["effects"]:
                if "negative" in effect.lower():
                    LayerColor = "#C84B31"
                    effects += f"""<span style=" color: #ffffff; font-size: 12px; border-radius: 10px; margin: 0.15em; line-height: 3.5; background: {LayerColor}; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{effect}</span>"""

                if "neutral" in effect.lower():
                    LayerColor = "#ECDBBA"
                    effects += f"""<span style=" color: #ffffff; font-size: 12px; border-radius: 10px; margin: 0.15em; line-height: 3.5; background: {LayerColor}; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{effect}</span>"""

                if "positive" in effect.lower():
                    LayerColor = "#2D4263"
                    effects += f"""<span style=" color: #ffffff; font-size: 12px; border-radius: 10px; margin: 0.15em; line-height: 3.5; background: {LayerColor}; font-family:Titillium Web; height: auto; padding:10px; transition: 0.5s;">{effect}</span>"""

            st.markdown(effects, unsafe_allow_html=True)
            st.markdown("""-----""")

