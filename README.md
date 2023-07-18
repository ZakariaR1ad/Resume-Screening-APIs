# Resume-Screening-APIs
This is the open-source version of the resume screening APIs

## Installation
To install the project, you will need to have Python installed on your machine. Once you have Python installed, you can install the project dependencies by running the following command:

```pip install -r requirements.txt```


## Running the Project
To run the project, you can run the following command:\
```uvicorn main:app --reload```\
This will start the project on port 8000. You can then access the API documentation at http://localhost:8000/docs.

## Using docker
First, you'll need to build the image :\
```docker build -t screening-apis .```\
After that, you can run it using :\
```docker run -d -p 8000:8000 screening-apis```
