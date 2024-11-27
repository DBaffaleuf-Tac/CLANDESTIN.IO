class AIPrompts():

    findGDPRData = "I would like you to identify for me which " \
	"column in this dataset can be considered as personal data as per GDPR " \
	"and return me ONLY " \
    "a concisive one row comma-separated list with just the name " \
	"of each column concerned, NOTHING ELSE. it is very important " \
    "that you don't add any comment or explanation. " \
    "If you do not find any column with personal data, just respond \'None\' :" 

    # replaceGDPRData = "I would like you to substitue each value in this dataset  " \
    # "with new fictionnal data  " \
    # "with respects to the country of origin of the data.  " \
    # "It is important to create new values at every row." \
    # "\n " \

    replaceGDPRData = "You are an expert at data pseudonimization."\
    " I would like you to substitue each value in this dataset  with new fictionnal data." \
    "I want you to keep the document type of the data, for example if the data is in HTML or JSON format, substitute with the same format data." \
    "I want also you to identify the localization of the data, for example if it is a turkish name, substitute ith a turkish name." \
    "If you substitute firstnames and lastnames and there is also an email to substitue, combine the corresponding firstname and lastname to create a substitute email" \
    "It is important to create new values at every row." \
    "\n " \
        
    def __init__(self):
        return
    
    def __del__(self):
        return
    