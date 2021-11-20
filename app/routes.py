from flask import render_template
from app import app
from app.forms import *
import json, datetime, requests

#for comment scrapping
api_key = "AIzaSyAh56rvV3so6f8JtELq3tgjDuTJOwMIoZQ" # Replace this dummy api key with your own.

from googleapiclient.discovery import build
youtube = build('youtube', 'v3', developerKey=api_key)
import pandas as pd
box = [['Name', 'Comment', 'Time', 'Likes', 'Reply Count']]
dat=[]

from urllib.parse import urlparse, parse_qs



from modzy import ApiClient
client = ApiClient(base_url=app.config['API_URL'], api_key=app.config['API_KEY'])

@app.route('/', methods=['GET', 'POST'])
@app.route('/sentiment', methods=['GET', 'POST'])
def sentiment():
	form = SentimentAnalysisForm()

	if form.validate_on_submit():
		if form.input_text.data == 'asdf':
			data = {'input-text':form.input_text.data,"classPredictions":[{"class":"neutral","score":0.831},{"class":"negative","score":0.137},{"class":"positive","score":0.032}]} #this example output is used for debugging.
		else:
                    url = form.input_text.data
                    parsed_url = urlparse(url)
                    ID=parsed_url.query[2:]
                    df=scrape_comments_with_replies(ID)
                    dataframe=df[1:].copy()
                    list_classes=[]
                    list_score =list_classes.copy()
                    for text in dataframe["Comment"]:
                        job = client.jobs.submit_text('ed542963de', '1.0.1', {'input.txt': text})
                        result = client.results.block_until_complete(job, timeout=None)
                        print(text)
                        print(result['results']['job']['results.json']['data']['result'])
                        print("__+++++__")
                        print(result['results']['job']['results.json']['data']['result']['classPredictions'][0])
                        list_classes.append(result['results']['job']['results.json']['data']['result']['classPredictions'][0]['class'])
                        list_score.append(result['results']['job']['results.json']['data']['result']['classPredictions'][0]['score'])
                    #print(list_classes)
                    dataframe["classPredictions"]=list_classes
                    dataframe["score"]=list_score
                    print(dataframe)
                    data=dataframe["classPredictions"].value_counts().rename_axis('class').reset_index(name='counts')
                    print(data)
                    dat=data.to_dict('records')
                    print(dat)
		return render_template('/sentiment.html', form=form, data=dat)
	return render_template('/sentiment.html', title='Sentiment Analysis', form=form, data=None)

@app.route('/next')
def index():
	return render_template('index.html')

def scrape_comments_with_replies(ID):
    data = youtube.commentThreads().list(part='snippet', videoId=ID, maxResults='100', textFormat="plainText").execute()

    for i in data["items"]:

        name = i["snippet"]['topLevelComment']["snippet"]["authorDisplayName"]
        comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"]
        published_at = i["snippet"]['topLevelComment']["snippet"]['publishedAt']
        likes = i["snippet"]['topLevelComment']["snippet"]['likeCount']
        replies = i["snippet"]['totalReplyCount']

        box.append([name, comment, published_at, likes, replies])

        totalReplyCount = i["snippet"]['totalReplyCount']

        if totalReplyCount > 0:

            parent = i["snippet"]['topLevelComment']["id"]

            data2 = youtube.comments().list(part='snippet', maxResults='100', parentId=parent,
                                            textFormat="plainText").execute()

            for i in data2["items"]:
                name = i["snippet"]["authorDisplayName"]
                comment = i["snippet"]["textDisplay"]
                published_at = i["snippet"]['publishedAt']
                likes = i["snippet"]['likeCount']
                replies = ""

                box.append([name, comment, published_at, likes, replies])

    while ("nextPageToken" in data):

        data = youtube.commentThreads().list(part='snippet', videoId=ID, pageToken=data["nextPageToken"],
                                             maxResults='100', textFormat="plainText").execute()

        for i in data["items"]:
            name = i["snippet"]['topLevelComment']["snippet"]["authorDisplayName"]
            comment = i["snippet"]['topLevelComment']["snippet"]["textDisplay"]
            published_at = i["snippet"]['topLevelComment']["snippet"]['publishedAt']
            likes = i["snippet"]['topLevelComment']["snippet"]['likeCount']
            replies = i["snippet"]['totalReplyCount']

            box.append([name, comment, published_at, likes, replies])

            totalReplyCount = i["snippet"]['totalReplyCount']

            if totalReplyCount > 0:

                parent = i["snippet"]['topLevelComment']["id"]

                data2 = youtube.comments().list(part='snippet', maxResults='100', parentId=parent,
                                                textFormat="plainText").execute()

                for i in data2["items"]:
                    name = i["snippet"]["authorDisplayName"]
                    comment = i["snippet"]["textDisplay"]
                    published_at = i["snippet"]['publishedAt']
                    likes = i["snippet"]['likeCount']
                    replies = ''

                    box.append([name, comment, published_at, likes, replies])

    df = pd.DataFrame({'Name': [i[0] for i in box], 'Comment': [i[1] for i in box], 'Time': [i[2] for i in box],
                       'Likes': [i[3] for i in box], 'Reply Count': [i[4] for i in box]})

    df.to_csv('youtube-comments.csv', index=False, header=False)

    return df