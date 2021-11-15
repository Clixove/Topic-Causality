# Causality of Public Opinions

Granger causality test for the posts in social networks 

![](https://img.shields.io/badge/language-zh--CN-orange)
![](https://img.shields.io/badge/dependencies-Python%203.9-blue)
![](https://img.shields.io/badge/dependencies-Django%203.2-green)
![](https://img.shields.io/badge/dependencies-TensorFlow%202.6-orange)

## Acknowledge

BERT-3 Preprocessing (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_preprocess/3

BERT-3 Model (Chinese Language): 
https://tfhub.dev/tensorflow/bert_zh_L-12_H-768_A-12/3

Data collection tool: https://github.com/dataabc/weibo-search

## Introduction

A discussion will be raised when an enterprise, organization of famous
individual announces an activity. However, their competitors (especially
bad ones) will hire a lot of robots and zombie accounts to publish
negative opinions in social networks. This phenomenon will drive normal
individuals away from the truth.

This software can:
1. Find obvious events against the noisy and unordered opinions.
2. Test the causality between highly active accounts, to figure out how one
is affected by other's opinions or affects others.

The software use BERT-3 model to extract features from text, and use DBSCAN
algorithm to cluster posts into several events. Finally, it uses Granger
causality test to figure out the causality between different accounts.

As a conclusion, this technology is designed to help distinguish real public 
opinion from intended intensive promotion.

## Installation

1. Create `token` folder at project root. There are two files in token:
`token/django_secret_key` and `token/smtp.json`. 
In `django_secret_key`, there should be a string about 52 characters, being 
a secret key for communication between client and web server. And in 
`smtp.json`, there should be the config of web maintainer's email sender.
The format is:
```json
{
  "host": "example.com",
  "port": 465,
  "username": "registration@example.com",
  "password": "anypassword"
}
```
If you don't use a registration confirming service by email, you can modify
the source code. It is mainly defined at `add_register` and `add_user` functions
at `my_login/views.py`.

2. Create the python environment. I recommend using a virtual 
environment. After implementing that, please enter the environment and run:
```bash
pip install -r requirements
```
It is a maximum required packages. With the environment, all functions can be
used, but not all functions are necessary.

3. Download BERT-3 models, and place model folders like 
`bert_zh_preprocessing_3/` inside this project's `bert_models` folder.

4. Navigate to the project folder, and create the database and super-user:
```bash
python manage.py migrate
python manage.py createsuperuser
```
This user has the root permission. To implement that, please follow the 
director in command line.

5. Run the server.
```bash
python manage.py 0.0.0.0:[port]
```
The IP address can only be 127.0.0.1 (for local use only) or 0.0.0.0 (for 
web server), and the port can be customized.
