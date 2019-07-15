import nltk
import os
import sys
import glob
from os import getenv
import pyodbc
import pandas as pd


#connect to DB
data = pyodbc.connect('driver={SQL Server};'
                      'server=JAMESHAMIL;'
                      'database=training;'
                      'trusted_connection=yes')

# query DB and write to files
df = pd.read_sql_query('select * from negativesentiment', data)

cur = data.cursor()
cur.execute("select * from negativesentiment")
with open("negat.txt","w",encoding="utf8", newline='') as f:
    for row in cur:
        print(row[0], file=f)

cur.execute("select * from positivesentiment")
with open("posr.txt","w",encoding="utf8", newline='') as f:
    for row in cur:
        print(row[0], file=f)










#Sample posts


post1link= "https://social.msdn.microsoft.com/Forums/en-US/5ba99b16-3a95-4dd9-8e3b-6b295bede1a1/database-still-not-updating?forum=winformsdatacontrols"

post2link =  "https://social.msdn.microsoft.com/Forums/en-US/eff6241d-877f-4b8c-b56a-e6cb7219962e/angry-about-reporting-services?forum=sqlreportingservices"


#Thread 1: negative to positive sentiment
Post1 = "Hi everyone,I created a very simple app that reads data from an Access database, created a save button to update the chages done to the fields but it does not update it.Now, before you say this, yes, i have tryed the Copy if newer and the Never Copy options in the solutions explorer of the db, but it still doesnt update it.The code for the save button (just in case) is: Private Sub SaveButton_Click(ByVal sender As System.Object, ByVal e As System.EventArgs) Handles SaveButton.ClickMe.Validate()Me.ProyectosBindingSource.EndEdit()Me.TableAdapterManager.UpdateAll(Me.EcoIndicesDataSet)End Sub"
Post2 = "Thank you for your response Andreas,but unfortunately the problem is still there. I had checked the copy if newer option, but it still doesnt work.I have the same issue with the app you created, it works fine but it doesnt update the db, even if the copy to newer is selected.Any other ideas? Thanks in advance!"
Post3 ="Ok I tryed the app from the debug folder and it did the same thing.I recoded the whole thing and now it works. Thank you!!!!!"

#Thread 2: negative to negative sentiment
Post4 = "I have seen the odd thread on here that just mentions in passing that data-driven subscriptions are only available on the SQL 2005 Enterprise edition. Does no-one else but me think that this is absolutely disgraceful? We bought SQL Server Standard for our 2 processor server and it cost just under £8,000. The only reason we would have to buy Enterprise is for the data-driven subscriptions in RS and that would cost us £33,000. When the beta of RS came out, it had data-driven subscriptions at all levels. When RS 2000 came out, we could easily get a legitimate copy of RS 2000 Enterprise from Microsoft and have the same functionality. Now we have to pay £25,000 for the privilege or hand-code the whole thing. I repeat; this is an absolutely disgraceful piece of profiteering from Microsoft. Do they really think that data-driven subscriptions are only of value to people using the Enterprise edition?"
Post5 = "I think it's disgraceful that a product which was in all versions of the beta and freely available in SQL 2000, now costs me £25,000 in SQL 2005. Don't you? As I believe this forum is read by Microsoft developers, maybe I thought they could give me a rational response. If you know of a place where I can get a better response, or where I ought to post this, please let me know. It is not my intention to upset anyone on the forum, just to let Microsoft know how I feel about their product."

















#reading text files for training

accuracy = 0
with open ("negat.txt","r",encoding="utf8") as f:
    negative = f.readlines()

with open("posr.txt", "r",encoding="utf8") as f:
    positive = f.readlines()

#split into train and score data
SplitIndex = 75
testNeg = negative[SplitIndex+1:]
testPos = positive[SplitIndex+1:]
trainNeg = negative[:SplitIndex]
trainPos = positive[:SplitIndex]

#split data into sets of words, negative and positive
def getVocab():
    positives = [word for line in trainPos for word in line.split()]
    negatives = [word for line in trainNeg for word in line.split()]
    allWords = [item for sublist in [positives,negatives]for item in sublist]
    allWordsSet = list(set(allWords))
    vocabulary = allWordsSet
    return vocabulary

vocabulary = getVocab()

#splits vocab to train, list of words and sentiment label
def getTrainingData():
    negTagged = [{'review':oneReview.split(),'label':'negative'}for oneReview in trainNeg]
    posTagged = [{'review': oneReview.split(), 'label': 'positive'} for oneReview in trainPos]
    fullData = [item for sublist in [negTagged,posTagged] for item in sublist]
    trainingData = [(review['review'],review['label']) for review in fullData]
    return trainingData

trainingData = getTrainingData()

#assigns values to words (0,1) for words in input.
def extract_features(review): #rename, pull from "bag of words"

    review_words = set(review)
    features = {}
    for word in vocabulary:
            features[word]=(word in review_words)
    return features

#trains model
def getTrainedBayesClass(extract_features,trainingData):
    #print("training")
    trainingFeatures = nltk.classify.apply_features(extract_features,trainingData)
    trainedNBC = nltk.NaiveBayesClassifier.train(trainingFeatures)
    return trainedNBC

trainedNBC = getTrainedBayesClass(extract_features,trainingData)

#predict using model
def naiveBayesCalc(review):
    probInstance = review.split() # split input into array
    probFeatures = extract_features(probInstance)
    return trainedNBC.classify(probFeatures)

#test harness
def getReviewSentiments(naiveBayesCalc):
    testNegResults = [naiveBayesCalc(review) for review in testNeg]
    testPosResults = [naiveBayesCalc(review) for review in testPos]
    labelToNum = {'positive':1,'negative':-1}
    numericNeg = [labelToNum[x] for x in testNegResults]
    numericPos = [labelToNum[x] for x in testPosResults]
    return {'results-on-pos':numericPos,'results-on-neg':numericNeg}


list3 = []
def runDiagnostics(reviewResult):
    posResult = reviewResult['results-on-pos']
    negResult = reviewResult['results-on-neg']
    numTruePos = sum(x>0 for x in posResult)
    numTrueNeg = sum(x<0 for x in negResult)

    pctTruePos = float(numTruePos)/len(posResult)
    pctTrueNeg = float(numTrueNeg)/len(negResult)
    totalAccurate = numTruePos+numTrueNeg
    total = len(posResult)+len(negResult)
    print("accuracy on pos = " +"%.2f" %(pctTruePos*100)+"%" )
    print("accuracy on neg = " + "%.2f" % (pctTrueNeg * 100) + "%")
    print("overall accuracy = " + "%.2f"%(totalAccurate*100/total)+"%")
    list3.append(totalAccurate*100/total)
    list3.append(totalAccurate * 100 / total)


runDiagnostics(getReviewSentiments(naiveBayesCalc))

#print(naiveBayesCalc("I love AWS"))

cnxn2 = pyodbc.connect('driver={SQL Server};'
                      'server=JAMESHAMIL;'
                      'database=testwrite;'
                      'trusted_connection=yes')

#pd.write_sql_query(insert into test values (1,'aaa'), cnxn2)


cursor = cnxn2.cursor()







accuracy1 = list3[0]

post1sent = naiveBayesCalc(Post1)
post2sent = naiveBayesCalc(Post2)
post3sent = naiveBayesCalc(Post3)
post4sent = naiveBayesCalc(Post4)
post5sent = naiveBayesCalc(Post5)
print(post1sent)
print(post2sent)
print(post3sent)
print(post4sent)
print(post5sent)






cursor.execute(
    """
    INSERT INTO table2
    (Link, Sentiment, CS, Sentiment48, CS48,trend)
    VALUES (?, ?, ?,?,?,?)
    """,
    (post1link, post1sent, accuracy1,post3sent,accuracy1,"0"),

)

cursor.execute(
    """
    INSERT INTO table2
    (Link, Sentiment, CS, Sentiment48, CS48,trend)
    VALUES (?, ?, ?,?,?,?)
    """,
    (post2link, post4sent, accuracy1, post5sent, accuracy1, "1"),

)

cursor.execute(
    """
    INSERT INTO table2
    (Link, Sentiment, CS, Sentiment48, CS48,trend)
    VALUES (?, ?, ?,?,?,?)
    """,
    (post1link, post3sent, accuracy1, post5sent, accuracy1, "1"),

)




cnxn2.commit()